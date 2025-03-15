import openai
import ollama
from ollama import generate,GenerateResponse


import google.generativeai as genai 


from surrealdb_rag.constants import DatabaseParams, ModelParams, ArgsLoader
from surrealdb import AsyncSurreal
import re


"""
Handles the retrieval of available LLM models and corpus tables.
"""
class ModelListHandler():
    
    """
        Initializes the ModelListHandler.

        Args:
            model_params (ModelParams): Model parameters.
            connection (AsyncSurreal): Asynchronous SurrealDB connection.
        """
    def __init__(self, model_params, connection):
        self.LLM_MODELS = {}
        self.CORPUS_TABLES = {}
        self.model_params = model_params
        self.connection = connection
    
    """
        Retrieves a dictionary of available LLM models.

        Returns:
            dict: Dictionary of available LLM models.
        """
    async def available_llm_models(self):
        if self.LLM_MODELS != {}:
            return self.LLM_MODELS 
        else:
            self.LLM_MODELS = {}
            

            # Configure Gemini API if API key is available
            if self.model_params.gemini_token:
                genai.configure(api_key=self.model_params.gemini_token)

                for model in genai.list_models():
                    #print(model)
                    if (    model.supported_generation_methods in
                            [ 
                                ['generateContent', 'countTokens'] , 
                                ['generateContent', 'countTokens', 'createCachedContent']
                            ]
                            and "gemini" in model.name 
                            and (model.display_name == model.description
                                or "stable" in model.description.lower()) ):
                        self.LLM_MODELS["GOOGLE - " + model.display_name] = {"model_version":model.name,"host":"API","platform":"GOOGLE","temperature":0}
                        self.LLM_MODELS["GOOGLE - " + model.display_name + " (surreal)"] = {"model_version":model.name, "host":"SQL","platform":"GOOGLE","temperature":0}
                    
            # Configure OpenAI API if API key is available
            if self.model_params.openai_token:
                openai.api_key = self.model_params.openai_token
                models = openai.models.list()
                for model in models.data:
                    if(model.owned_by == "openai" and "gpt" in model.id):
                        #print(model)
                        self.LLM_MODELS["OPENAI - " + model.id] = {"model_version":model.id,"host":"API","platform":"OPENAI","temperature":0.5}
                        self.LLM_MODELS["OPENAI - " + model.id + " (surreal)"] = {"model_version":model.id,"host":"SQL","platform":"OPENAI","temperature":0.5}
                    

            # Retrieve models from Ollama
            response: ollama.ListResponse = ollama.list()

            for model in response.models:
                self.LLM_MODELS["OLLAMA " + model.model] = {"model_version":model.model,"host":"OLLAMA","platform":"OLLAMA","temperature":0}

        

            return self.LLM_MODELS 
    """
    Retrieves a dictionary of available corpus tables.

    Returns:
        dict: Dictionary of available corpus tables.
    """
    async def available_corpus_tables(self):
        if self.CORPUS_TABLES != {}:
            return self.CORPUS_TABLES 
        else:
            self.CORPUS_TABLES = {}
            corpus_tables = await self.connection.query("""
                SELECT display_name,table_name,embed_models,fn::additional_data_keys(table_name) as addional_data_keys FROM corpus_table FETCH embed_models,embed_models.model;
            """)
           
            # Filter out OpenAI models if API key is absent
            for corpus_table in corpus_tables:
               
                # create an dict item for table_name
                table_name = corpus_table["table_name"]
                self.CORPUS_TABLES[table_name] = {}
                self.CORPUS_TABLES[table_name]["display_name"] = corpus_table["display_name"]
                self.CORPUS_TABLES[table_name]["table_name"] = corpus_table["table_name"]
                self.CORPUS_TABLES[table_name]["addional_data_keys"] = corpus_table["addional_data_keys"]
                self.CORPUS_TABLES[table_name]["embed_models"] = []
                for model in corpus_table["embed_models"]:
                    model_def =  model["model"]
                    model_def_id = model_def["id"].id
                    if model_def_id[0] != "OPENAI" or (
                        model_def_id[0] == "OPENAI" and self.model_params.openai_token):

                        self.CORPUS_TABLES[table_name]["embed_models"].append(
                                {"model":model_def_id,
                                 "field_name":model["field_name"],
                                 "corpus":model_def["corpus"],
                                 "description":model_def["description"],
                                 "host":model_def["host"],
                                 "model_trainer":model_def["model_trainer"],
                                 "version":model_def["version"],
                                 "dimensions":model_def["dimensions"],
                                 }
                            )
            return self.CORPUS_TABLES 


        


        
"""
Handles interactions with different LLM models.
"""
class LLMModelHander():



    PROMPT_TEXT_TEMPLATES =  {

        "Generic_Exclusive":{"name":"Generic Exclusive", "text":"""              
    You are an AI assistant answering questions about anything from the corpus of knowledge provided in the <context></context> tags.
    
    You may also refer to the text in the <chat_history></chat_history> tags but only for refining your understanding of what is being asked of you. Do not rely on the chat_history for answering the question!
    
    Please provide your response in HTML format. Include appropriate headings and lists where relevant.

    At the end of the response, add any links as a HTML link and replace the title and url with the associated title and url of the more relevant page from the context.

    Only reply with the context provided. If the context is an empty string, reply with 'I am sorry, I do not know the answer.'.

    Do not use any prior knowledge that you have been trained on.

    <context>
        $context
    </context>
    <chat_history>
        $chat_history
    </chat_history>         
    """},
    "Generic_Inclusive":{"name":"Generic Inclusive","text":"""              
    You are an AI assistant answering questions about anything from the corpus of knowledge provided in the <context></context> tags.
    
    You may also refer to the text in the <chat_history></chat_history> tags but only for refining your understanding of what is being asked of you. Do not rely on the chat_history for answering the question!
    
    Please provide your response in HTML format. Include appropriate headings and lists where relevant.

    At the end of the response, add any links as a HTML link and replace the title and url with the associated title and url of the more relevant page from the context.

    Use the context as a guide but feel free to use any prior knowledge that you have been trained on.

    <context>
        $context
    </context>
    <chat_history>
        $chat_history
    </chat_history>         
    """}
    ,
    "Finance_Exclusive":{"name":"Finance Exclusive","text":"""              
    You are an a financial analyist helping me with my finance questions.
     
    I have given you some details from my database to consider as a focused corpus of knowledge provided in the <context></context> tags.
    
    You may also refer to the text in the <chat_history></chat_history> tags but only for refining your understanding of what is being asked of you. Do not rely on the chat_history for answering the question!
    
    Please provide your response in HTML format. Include appropriate headings and lists where relevant.

    At the end of the response, add any links as a HTML link and replace the title and url with the associated title and url of the more relevant page from the context.

    Only reply with the context provided. If the context is an empty string, reply with 'I am sorry, I do not know the answer.'.

    Do not use any prior knowledge that you have been trained on.

    <context>
        $context
    </context>
    <chat_history>
        $chat_history
    </chat_history>         
    """}
    ,
    "Finance_Inclusive":{"name":"Finance Inclusive","text":"""              
    You are an a financial analyist helping me with my finance questions.
     
    I have given you some details from my database to consider as a focused corpus of knowledge provided in the <context></context> tags.
    
    You may also refer to the text in the <chat_history></chat_history> tags but only for refining your understanding of what is being asked of you. Do not rely on the chat_history for answering the question!
    
    Please provide your response in HTML format. Include appropriate headings and lists where relevant.

    At the end of the response, add any links as a HTML link and replace the title and url with the associated title and url of the more relevant page from the context.

    Use the context as a guide but feel free to use any prior knowledge that you have been trained on.

    <context>
        $context
    </context>
    <chat_history>
        $chat_history
    </chat_history>         
    """},
    "No_Context":{"name":"No Context","text":"""
    """}
    }

    GEMINI_CHAT_COMPLETE = """RETURN fn::gemini_chat_complete($llm,$prompt_with_context,$input,$google_token);"""

    OPENAI_CHAT_COMPLETE = """RETURN fn::openai_chat_complete($llm,$prompt_with_context, $input, $temperature, $openai_token);"""


    """
    Initializes the LLMModelHander.

    Args:
        model_data (str): Model data.
        model_params (ModelParams): Model parameters.
        connection (AsyncSurreal): Asynchronous SurrealDB connection.
    """
    def __init__(self,model_data:str,model_params:ModelParams,connection:AsyncSurreal):
        
        self.model_data = model_data
        self.model_params = model_params
        self.connection = connection


    """
    Parses a string containing <think> tags and extracts the content.

    Args:
        input_string: The string to parse.

    Returns:
        A dictionary with two keys:
        - "think": The content between the <think> tags.
        - "content": The rest of the string.
    """
    def parse_deepseek_response(input_string):
        """
        Parses a string containing <think> tags and extracts the content.

        Args:
            input_string: The string to parse.

        Returns:
            A dictionary with two keys:
            - "think": The content between the <think> tags.
            - "content": The rest of the string.
        """

        # Use regular expression to find the content within the <think> tags
        think_match = re.search(r"<think>(.*?)</think>", input_string, re.DOTALL)
        think_content = think_match.group(1).strip() if think_match else ""

        # Remove the <think> section from the original string
        content = re.sub(r"<think>.*?</think>\s*", "", input_string, flags=re.DOTALL).strip()

        return {"think": think_content, "content": content}
    
    """
        Extracts plain text from a string by removing content within tags.

        Args:
            text (str): The input string containing tags.

        Returns:
            str: The plain text with tags and their contents removed.
        """
    def extract_plain_text(text):

        # Use a regular expression to find and remove content within tags
        clean_text = LLMModelHander.remove_think_tags(text)
        clean_text = re.sub(r'<[^>]*>', '', clean_text)
        return clean_text
    
    """
        Removes <think> tags and their content from the given text, leaving only the text after the closing tag.

        Args:
            text (str): The input string.

        Returns:
            str: The string with <think> tags and their content removed.
        """
    def remove_think_tags(text):
        # Uses a regular expression to find and remove <think> tags and their content.
        
        return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()
    

    """
    Parses a string for <think> tags and returns a dictionary with 'think' and 'content' fields.

    Args:
        text (str): The input string containing or not containing <think> tags.

    Returns:
        dict: A dictionary with 'think' (content within <think> tags) and 
            'content' (content outside <think> tags) fields.
    """
    def parse_llm_response_content(text):
        
        text = text.replace("```html","").replace("```","")
        think_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
        if think_match:
            think_content = think_match.group(1).strip()
            content = re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()
            return {"think": think_content, "content": content}
        else:
            return {"think": None, "content": text.strip()}
    
    
    """
        Gets a short plain text response from the chat model.

        Args:
            prompt_with_context (str): The prompt with context.
            input (str): The user input.

        Returns:
            str: A short plain text response.
        """
    async def get_short_plain_text_response(self,prompt_with_context:str,input:str):
        # Limits the response to 255 characters.
        n = 255
        # Extracts plain text from the chat response.
        text = LLMModelHander.extract_plain_text(await self.get_chat_response(prompt_with_context,input))
        if len(text) > n:
            # Returns the first 255 characters if the response is longer.
            return text[:n]
        else:
            # Returns the full response if it's shorter than 255 characters.
            return text 
    
    """
        Gets a chat response based on the model's host.

        Args:
            prompt_with_context (str): The prompt with context.
            input (str): The user input.

        Returns:
            str: The chat response.
        """
    async def get_chat_response(self,prompt_with_context:str,input:str):

        # Matches the model's host and calls the appropriate method.
        match self.model_data["host"]:
            case "SQL":
                # Gets response from SurrealDB.
                return await self.get_chat_response_from_surreal(prompt_with_context,input)
            case "API":
                # Gets response from API.
                return self.get_chat_response_from_api(prompt_with_context,input)
            case "OLLAMA":
                # Gets response from Ollama.
                return self.get_chat_response_from_ollama(prompt_with_context,input)
            case _:
                raise SystemError(f"Invalid host method {self.model_data["host"]}") 

    """
        Gets a chat response from an API based on the model's platform.

        Args:
            prompt_with_context (str): The prompt with context.
            input (str): The user input.

        Returns:
            str: The chat response from the API.
        """
    def get_chat_response_from_api(self,prompt_with_context:str,input:str):
        # Matches the model's platform and calls the appropriate method.
        match self.model_data["platform"]:
            case "OPENAI":
                # Gets response from OpenAI API.
                return self.get_chat_openai_response_from_api(prompt_with_context,input)
            case "GOOGLE":
                # Gets response from Google Gemini API.
                return self.get_chat_gemini_response_from_api(prompt_with_context,input)
            case _:
                raise SystemError(f"Error in outcome: Invalid model for API execution {self.model_data["platform"]}") 
     
     
    """
        Gets a chat response from SurrealDB based on the model's platform.

        Args:
            prompt_with_context (str): The prompt with context.
            input (str): The user input.

        Returns:
            str: The chat response from SurrealDB.
        """
    async def get_chat_response_from_surreal(self,prompt_with_context:str,input:str):
        # Matches the model's platform and calls the appropriate method.
        match self.model_data["platform"]:
            case "OPENAI":
                # Gets response from OpenAI using SurrealDB.
                return await self.get_chat_openai_response_from_surreal(prompt_with_context,input)
            case "GOOGLE":
                # Gets response from Google Gemini using SurrealDB.
                return await self.get_chat_gemini_response_from_surreal(prompt_with_context,input)
            case _:
                raise SystemError(f"Error in outcome: Invalid model for SQL execution {self.model_data["platform"]}") 


    """
        Gets a chat response from OpenAI using SurrealDB.

        Args:
            prompt_with_context (str): The prompt with context.
            input (str): The user input.

        Returns:
            str: The OpenAI chat response.
        """
    async def get_chat_openai_response_from_surreal(self,prompt_with_context:str,input:str):
          
        # Executes the OpenAI chat completion query in SurrealDB.
        model_version = self.model_data["model_version"]
        openai_response = await self.connection.query(
            LLMModelHander.OPENAI_CHAT_COMPLETE, params={
                "llm":model_version,
                "prompt_with_context":prompt_with_context,
                "input":input,
                "temperature":self.model_data["temperature"],
                "openai_token":self.model_params.openai_token
            })
                       
        # Returns the content of the response.
        return openai_response["choices"][0]["message"]["content"]                    
                                
    
    """
        Gets a chat response from Google Gemini using SurrealDB.

        Args:
            prompt_with_context (str): The prompt with context.
            input (str): The user input.

        Returns:
            str: The Gemini chat response.
        """
    async def get_chat_gemini_response_from_surreal(self,prompt_with_context:str,input:str):
        
        # Executes the Gemini chat completion query in SurrealDB.
        model_version = self.model_data["model_version"].replace("models/","")
        gemini_response = await self.connection.query(
            LLMModelHander.GEMINI_CHAT_COMPLETE, params={
                "llm":model_version,
                "prompt_with_context":prompt_with_context,
                "input":input,
                "google_token":self.model_params.gemini_token
            } )
        # Returns the text content of the response.
        return gemini_response["candidates"][0]["content"]["parts"][0]["text"]

    """
        Gets a chat response from the OpenAI API.

        Args:
            prompt_with_context (str): The prompt with context.
            input (str): The user input.

        Returns:
            str: The OpenAI chat response.
        """
    def get_chat_openai_response_from_api(self,prompt_with_context:str,input:str):
        
        # Constructs the messages for the OpenAI API.
        messages = [
            {
                "role": "system",
                "content": prompt_with_context
            },
            {
                "role": "user",
                "content": input
            }
        ]
        # Sets the OpenAI API key.
        openai.api_key = self.model_params.openai_token
        if openai.api_key is None:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        try:
            # Calls the OpenAI chat completions API.
            response = openai.chat.completions.create(
                model=self.model_data["model_version"],
                messages=messages,
                temperature=self.model_data["temperature"]
            )
            # Returns the content of the response.
            return response.choices[0].message.content
        except openai.error.OpenAIError as e:
            print(f"An error occurred: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    """
        Gets a chat response from the Google Gemini API.

        Args:
            prompt_with_context (str): The prompt with context.
            input (str): The user input.

        Returns:
            str: The Gemini chat response.
        """
    def get_chat_gemini_response_from_api(self,prompt_with_context:str,input:str):
        
        # Constructs the messages for the Gemini API.
        messages = [
            {
                "text": prompt_with_context
            },
            {
                "text": input
            }
        ]
        genai.configure(api_key=self.model_params.gemini_token)
        # Initializes the GenerativeModel with the model version.
        model = genai.GenerativeModel(self.model_data["model_version"])
        # Generates the content from the model.
        response = model.generate_content(messages)
        # Returns the text content of the response.
        return response.text

    """
        Gets a chat response from Ollama.

        Args:
            prompt_with_context (str): The prompt with context.
            input (str): The user input.

        Returns:
            str: The Ollama chat response.
        """
    def get_chat_response_from_ollama(self,prompt_with_context:str,input:str):
        
        # Constructs the messages for Ollama.
        messages = [
            {
                "role": "system",
                "content": prompt_with_context
            },
            {
                "role": "user",
                "content": input
            }
        ]
        # Generates the response from Ollama.
        response: GenerateResponse = generate(model=self.model_data["model_version"], prompt=str(messages))
        # Optional: Parse DeepSeek response if needed.
        #parsed_response = parse_deepseek_response(response.response)
        #return {"response":response, "think": parsed_response["think"],"content":parsed_response["content"]}
        return response.response
    

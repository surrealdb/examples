import openai
import ollama
from ollama import generate,GenerateResponse


import google.generativeai as genai 


from surrealdb_rag.constants import DatabaseParams, ModelParams, ArgsLoader
from surrealdb import AsyncSurreal
import re

class ModelListHandler():

    def __init__(self, model_params, connection):
        self.LLM_MODELS = {}
        self.CORPUS_TABLES = {}
        self.model_params = model_params
        self.connection = connection

    async def available_llm_models(self):
        if self.LLM_MODELS != {}:
            return self.LLM_MODELS 
        else:
            self.LLM_MODELS = {}
            

            #you need an api key for gemini
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
                    
            #you need an api key for openai
            if self.model_params.openai_token:
                openai.api_key = self.model_params.openai_token
                models = openai.models.list()
                for model in models.data:
                    if(model.owned_by == "openai" and "gpt" in model.id):
                        #print(model)
                        self.LLM_MODELS["OPENAI - " + model.id] = {"model_version":model.id,"host":"API","platform":"OPENAI","temperature":0.5}
                        self.LLM_MODELS["OPENAI - " + model.id + " (surreal)"] = {"model_version":model.id,"host":"SQL","platform":"OPENAI","temperature":0.5}
                    

            response: ollama.ListResponse = ollama.list()

            for model in response.models:
                self.LLM_MODELS["OLLAMA " + model.model] = {"model_version":model.model,"host":"OLLAMA","platform":"OLLAMA","temperature":0}

        

            return self.LLM_MODELS 
    
    async def available_corpus_tables(self):
        if self.CORPUS_TABLES != {}:
            return self.CORPUS_TABLES 
        else:
            self.CORPUS_TABLES = {}
            corpus_tables = await self.connection.query("""
                SELECT display_name,table_name,embed_models FROM corpus_table FETCH embed_models,embed_models.model;
            """)

            #you need an api key for openai so remove openai from list if api is absent

            for corpus_table in corpus_tables:
                # example record 
                # {
                #     display_name: 'Wikipedia',
                #     embed_models: [
                #         {
                #             corpus_table: corpus_table:embedded_wiki,
                #             field_name: 'content_fasttext_vector',
                #             id: corpus_table_model:[
                #                 corpus_table:embedded_wiki,
                #                 embedding_model_definition:[
                #                     'FASTTEXT',
                #                     'wiki'
                #                 ]
                #             ],
                #             model: {
                #                 corpus: 'https://cdn.openai.com/API/examples/data/vector_database_wikipedia_articles_embedded.zip',
                #                 description: 'Custom trained model using fasttext based on OPENAI wiki example download',
                #                 dimensions: 100,
                #                 host: 'SQL',
                #                 id: embedding_model_definition:[
                #                     'FASTTEXT',
                #                     'wiki'
                #                 ],
                #                 model_trainer: 'FASTTEXT',
                #                 version: 'wiki'
                #             }
                #         },
                #         {
                #             corpus_table: corpus_table:embedded_wiki,
                #             field_name: 'content_glove_vector',
                #             id: corpus_table_model:[
                #                 corpus_table:embedded_wiki,
                #                 embedding_model_definition:[
                #                     'GLOVE',
                #                     '6b 300d'
                #                 ]
                #             ],
                #             model: {
                #                 corpus: 'Wikipedia 2014 + Gigaword 5',
                #                 description: 'Standard pretrained GLoVE model from https://nlp.stanford.edu/projects/glove/ 300 dimensions version',
                #                 dimensions: 300,
                #                 host: 'SQL',
                #                 id: embedding_model_definition:[
                #                     'GLOVE',
                #                     '6b 300d'
                #                 ],
                #                 model_trainer: 'GLOVE',
                #                 version: '6b 300d'
                #             }
                #         },
                #         {
                #             corpus_table: corpus_table:embedded_wiki,
                #             field_name: 'content_openai_vector',
                #             id: corpus_table_model:[
                #                 corpus_table:embedded_wiki,
                #                 embedding_model_definition:[
                #                     'OPENAI',
                #                     'text-embedding-ada-002'
                #                 ]
                #             ],
                #             model: {
                #                 corpus: 'generic pretrained',
                #                 description: 'The standard OPENAI embedding model',
                #                 dimensions: 1536,
                #                 host: 'API',
                #                 id: embedding_model_definition:[
                #                     'OPENAI',
                #                     'text-embedding-ada-002'
                #                 ],
                #                 model_trainer: 'OPENAI',
                #                 version: 'text-embedding-ada-002'
                #             }
                #         }
                #     ],
                #     table_name: 'embedded_wiki'
                # }
                # create an dict item for table_name
                table_name = corpus_table["table_name"]
                self.CORPUS_TABLES[table_name] = {}
                self.CORPUS_TABLES[table_name]["display_name"] = corpus_table["display_name"]
                self.CORPUS_TABLES[table_name]["table_name"] = corpus_table["table_name"]
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


        


        

class LLMModelHander():



    def __init__(self,model_data:str,model_params:ModelParams,connection:AsyncSurreal):
        
        self.model_data = model_data
        self.model_params = model_params
        self.connection = connection


    def extract_plain_text(text):
        """
        Extracts plain text from a string by removing content within tags.

        Args:
            text (str): The input string containing tags.

        Returns:
            str: The plain text with tags and their contents removed.
        """
        # Use a regular expression to find and remove content within tags
        clean_text = remove_think_tags(clean_text)
        clean_text = re.sub(r'<[^>]*>', '', clean_text)
        return clean_text
    def remove_think_tags(text):
        """
        Removes <think> tags and their content from the given text, leaving only the text after the closing tag.

        Args:
            text (str): The input string.

        Returns:
            str: The string with <think> tags and their content removed.
        """
        return re.sub(r'<think>.*?</think>\n*', '', text, flags=re.DOTALL | re.IGNORECASE).strip()

    def get_short_plain_text_response(self,prompt_with_context:str,input:str):
        return LLMModelHander.extract_plain_text(self.get_chat_response(prompt_with_context,input))

    def get_chat_response(self,prompt_with_context:str,input:str):

        match self.model_data["host"]:
            case "SQL":
                return self.get_chat_response_from_surreal(prompt_with_context,input)
            case "API":
                return self.get_chat_response_from_api(prompt_with_context,input)
            case "OLLAMA":
                return self.get_chat_response_from_ollama(prompt_with_context,input)
            case _:
                raise SystemError(f"Invalid host method {self.model_data["host"]}") 


    
    def get_chat_response_from_api(self,prompt_with_context:str,input:str):
        match self.model_data["platform"]:
            case "OPENAI":
                return self.get_chat_openai_response_from_api(prompt_with_context,input)
            case "GOOGLE":
                return self.get_chat_gemini_response_from_api(prompt_with_context,input)
            case _:
                raise SystemError(f"Error in outcome: Invalid model for API execution {self.model_data["platform"]}") 

    def get_chat_response_from_surreal(self,prompt_with_context:str,input:str):
        match self.model_data["platform"]:
            case "OPENAI":
                return self.get_chat_openai_response_from_surreal(prompt_with_context,input)
            case "GOOGLE":
                return self.get_chat_gemini_response_from_surreal(prompt_with_context,input)
            case _:
                raise SystemError(f"Error in outcome: Invalid model for SQL execution {self.model_data["platform"]}") 

    def get_chat_openai_response_from_surreal(self,prompt_with_context:str,input:str):
        return "get_chat_openai_response_from_surreal"
    
    def get_chat_gemini_response_from_surreal(self,prompt_with_context:str,input:str):
        return "get_chat_gemini_response_from_surreal"


    def get_chat_openai_response_from_api(self,prompt_with_context:str,input:str):
        
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
        openai.api_key = self.model_params.openai_token
        if openai.api_key is None:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        try:
            response = openai.chat.completions.create(
                model=self.model_data["model_version"],
                messages=messages,
                temperature=self.model_data["temperature"]
            )
            return response.choices[0].message.content
        except openai.error.OpenAIError as e:
            print(f"An error occurred: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None


    def get_chat_gemini_response_from_api(self,prompt_with_context:str,input:str):
        
        messages = [
            {
                "text": prompt_with_context
            },
            {
                "text": input
            }
        ]
        genai.configure(api_key=self.model_params.gemini_token)
        model = genai.GenerativeModel(self.model_data["model_version"])
        response = model.generate_content(messages)
        return response.text


    def get_chat_response_from_ollama(self,prompt_with_context:str,input:str):
        
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
        response: GenerateResponse = generate(model=self.model_data["model_version"], prompt=str(messages))
        #parsed_response = parse_deepseek_response(response.response)
        #return {"response":response, "think": parsed_response["think"],"content":parsed_response["content"]}
        return response.response
    

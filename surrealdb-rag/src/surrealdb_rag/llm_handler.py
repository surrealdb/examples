import openai
import ollama
from ollama import generate,GenerateResponse


import google.generativeai as genai 


from surrealdb_rag.constants import DatabaseParams, ModelParams, ArgsLoader
from surrealdb import AsyncSurreal


    # LLM_MODELS = {
    #     "GEMINI-SURREAL": {"model_version":"gemini-2.0-flash","host":"SQL","platform":"GOOGLE","temperature":None},
    #     "GEMINI": {"model_version":"gemini-2.0-flash","host":"API","platform":"GOOGLE","temperature":None},
    #     "DEEPSEEK": {"model_version":"deepseek-r1:1.5b","host":"OLLAMA","platform":"local","temperature":None},
    #     "OPENAI-SURREAL": {"model_version":"gpt-3.5-turbo","host":"API","platform":"OPENAI","temperature":0.5},
    #     "OPENAI": {"model_version":"gpt-3.5-turbo","host":"API","platform":"OPENAI","temperature":0.5}
    # # }

    # EMBED_MODELS = {
    #     "CUST_FASTTEXT": {"dimensions":100,"host":"SQL"},
    #     "GLOVE": {"dimensions":300,"host":"SQL"},
    #     "OPENAI": {"dimensions":1536,"host":"API"}
    # }

class ModelListHandler():

    def __init__(self, model_params, connection):
        self.LLM_MODELS = {}
        self.EMBED_MODELS = {}
        self.model_params = model_params
        self.connection = connection

    async def populate_models(self):
        self.LLM_MODELS = {}
        self.EMBED_MODELS = {}

        check_for_vectors = await self.connection.query(
            """SELECT 
                content_openai_vector!=None AS has_openai_vectors, 
                content_glove_vector!=None AS has_glove_vectors, 
                content_fasttext_vector!=None AS has_fasttext_vectors
                FROM embedded_wiki LIMIT 1;""")
        check_for_vectors = check_for_vectors[0]
        #you need the vector field populated for fasttext
        if check_for_vectors["has_fasttext_vectors"] == True: 
                self.EMBED_MODELS["CUST_FASTTEXT"] = ModelParams.EMBED_MODELS["CUST_FASTTEXT"] 

        #you need the vector field populated for glove
        if check_for_vectors["has_glove_vectors"] == True: 
                self.EMBED_MODELS["GLOVE"] = ModelParams.EMBED_MODELS["GLOVE"] 

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
                    self.LLM_MODELS["GOOGLE - " + model.display_name] = {"model_version":model.name,"host":"API","platform":"GOOGLE","temperature":None}
                    self.LLM_MODELS["GOOGLE - " + model.display_name + " (surreal)"] = {"model_version":model.name, "host":"SQL","platform":"GOOGLE","temperature":None}
                
        #you need an api key for openai
        if self.model_params.openai_token:
            openai.api_key = self.model_params.openai_token
            models = openai.models.list()
            for model in models.data:
                if(model.owned_by == "openai" and "gpt" in model.id):
                    #print(model)
                    self.LLM_MODELS["OPENAI - " + model.id] = {"model_version":model.id,"host":"API","platform":"OPENAI","temperature":0.5}
                    self.LLM_MODELS["OPENAI - " + model.id + " (surreal)"] = {"model_version":model.id,"host":"SQL","platform":"OPENAI","temperature":0.5}
                

            # self.LLM_MODELS["OPENAI"] = ModelParams.LLM_MODELS["OPENAI"]
            # self.LLM_MODELS["OPENAI-SURREAL"] = ModelParams.LLM_MODELS["OPENAI-SURREAL"]
            #you need the vector field populated for openai
            if check_for_vectors["has_openai_vectors"] == True:
                self.EMBED_MODELS["OPENAI"] = ModelParams.EMBED_MODELS["OPENAI"] 

        response: ollama.ListResponse = ollama.list()

        for model in response.models:
            self.LLM_MODELS["OLLAMA " + model.model] = {"model_version":model.model,"host":"OLLAMA","platform":"local","temperature":None}

            # print('Name:', model.model)
            # print('  Size (MB):', f'{(model.size.real / 1024 / 1024):.2f}')
            # if model.details:
            #     print('  Format:', model.details.format)
            #     print('  Family:', model.details.family)
            #     print('  Parameter Size:', model.details.parameter_size)
            #     print('  Quantization Level:', model.details.quantization_level)
            # print('\n')


    async def available_llm_models(self):
        if self.LLM_MODELS != {}:
            return self.LLM_MODELS 
        else:
            await self.populate_models()
            return self.LLM_MODELS 
    
    async def available_embed_models(self):
        if self.EMBED_MODELS != {}:
            return self.EMBED_MODELS 
        else:
            await self.populate_models()
            return self.EMBED_MODELS 
            
        

        

class LLMModelHander():



    def __init__(self,model_data:str,model_params:ModelParams,connection:AsyncSurreal):
        
        self.model_data = model_data
        self.model_params = model_params
        self.connection = connection




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
    

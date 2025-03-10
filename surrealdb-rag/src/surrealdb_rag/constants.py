import argparse
import os


WIKI_URL = "https://cdn.openai.com/API/examples/data/vector_database_wikipedia_articles_embedded.zip"
WIKI_ZIP_PATH = "data/vector_database_wikipedia_articles_embedded.zip"
WIKI_PATH = "data/vector_database_wikipedia_articles_embedded.csv"

GLOVE_URL = "https://nlp.stanford.edu/data/glove.6B.zip"
GLOVE_ZIP_PATH = "data/glove.6B.zip"
GLOVE_PATH = "data/glove.6B.300d.txt"

FS_WIKI_PATH = "data/custom_fast_wiki_text.txt"


class SurrealParams():
    def __init__(self = None, url = None,username = None, password = None, namespace = None, database = None):
        self.username = username
        self.password = password
        self.namespace = namespace
        self.database = database
        self.url = url

    @staticmethod
    def ParseResponseForErrors(outcome):
      
      if outcome:
        if "result" in outcome:
            for item in outcome["result"]:
                if item["status"]=="ERR":
                    raise SystemError("Error in results: {0}".format(item["result"])) 
        
        if "error" in outcome:
            raise SystemError("Error in outcome: {0}".format(outcome["error"])) 

        return outcome
      else:
        return None
    

class ModelParams():

    # GEMINI_MODELS = ["gemini-2.0-flash-lite","gemini-2.0-flash","gemini-1.5-flash","gemini-1.5-flash-8b","gemini-1.5-pro"]
    # # OPENAI_MODELS = ["gemini-2.0-flash-lite","gemini-2.0-flash","gemini-1.5-flash","gemini-1.5-flash-8b","gemini-1.5-pro"]
    # # LLM_MODELS = {
    # #     "GEMINI-SURREAL": {"model_version":"gemini-2.0-flash","host":"SQL","platform":"GOOGLE","temperature":None},
    # #     "GEMINI": {"model_version":"gemini-2.0-flash","host":"API","platform":"GOOGLE","temperature":None},
    # #     "DEEPSEEK": {"model_version":"deepseek-r1:1.5b","host":"OLLAMA","platform":"local","temperature":None},
    # #     "OPENAI-SURREAL": {"model_version":"gpt-3.5-turbo","host":"API","platform":"OPENAI","temperature":0.5},
    # #     "OPENAI": {"model_version":"gpt-3.5-turbo","host":"API","platform":"OPENAI","temperature":0.5}
    # # }

    # EMBED_MODELS = {
    #     "FASTTEXT": {"dimensions":100,"host":"SQL"},
    #     "GLOVE": {"dimensions":300,"host":"SQL"},
    #     "OPENAI": {"dimensions":1536,"host":"API"}
    # }
    def __init__(self):
        self.openai_token_env_var = "OPENAI_API_KEY"
        self.openai_token = None
        self.gemini_token_env_var = "GOOGLE_GENAI_API_KEY"
        self.gemini_token = None
        # self.embedding_model_env_var = "SURREAL_RAG_EMBEDDING_MODEL"
        # self.embedding_model = None
        # self.llm_model_env_var = "SURREAL_RAG_LLM_MODEL"
        # self.llm_model = None
        # self.version = None
        # self.host = None
        # self.temperature = 0.5

    def AddArgs(self, parser:argparse.ArgumentParser):
        parser.add_argument("-oenv","--openai_token_env", help="Your env variable for LLM openai_token (Default: {0} for ollama hosted ignore)".format(self.openai_token_env_var))
        parser.add_argument("-genv","--gemini_token_env", help="Your env variable for LLM gemini_token (Default: {0} for ollama hosted ignore)".format(self.gemini_token_env_var))
        
        #parser.add_argument("-emenv","--embedding_model_env_var", help="Your env variable for embedding model value can be 'OPENAI' or 'GLOVE' (Default: {0})".format(self.embedding_model_env_var))
        #parser.add_argument("-em","--embedding_model", help="Embedding model value can be 'OPENAI' or 'GLOVE', if none it will use env var (Default: {0})".format("<from env variable>"))
        # parser.add_argument("-llmenv","--llm_model_env_var", help="Your env variable for LLM model value can be 'OPENAI','DEEPSEEK' or 'GEMINI' (Default: {0})".format(self.llm_model_env_var))
        # parser.add_argument("-llm","--llm_model", help="LLM model value can be 'OPENAI'.'DEEPSEEK' or 'GEMINI', if none it will use env var (Default: {0})".format("<from env variable>"))
        
    def SetArgs(self,args:argparse.Namespace):
        if args.openai_token_env:
            self.openai_token_env_var = args.openai_token_env
        
        self.openai_token = os.getenv(self.openai_token_env_var)

        if args.gemini_token_env:
            self.gemini_token_env_var = args.gemini_token_env
        self.gemini_token = os.getenv(self.gemini_token_env_var)


        # if args.embedding_model_env_var:
        #     self.embedding_model_env_var = args.embedding_model_env_var
        # if args.llm_model_env_var:
        #     self.llm_model_env_var = args.llm_model_env_var


        # if args.embedding_model:
        #     self.embedding_model = args.embedding_model
        # else:
        #     self.embedding_model = os.getenv(self.embedding_model_env_var)
            
        # if self.embedding_model not in ["OPENAI","GLOVE"]:
        #     raise ValueError("Embedding model must be 'OPENAI' or 'GLOVE'")

        # if args.llm_model:
        #     self.llm_model = args.llm_model
        # else:
        #     self.llm_model = os.getenv(self.llm_model_env_var)

        # self.version = self.LLM_MODELS[self.llm_model]["model_version"]
        # self.host = self.LLM_MODELS[self.llm_model]["host"]
            

    
    
class DatabaseParams():
    def __init__(self):
        #export SURREAL_CLOUD_TEST_USER=xxx
        #export SURREAL_CLOUD_TEST_PASS=xxx
        self.DB_USER_ENV_VAR = "SURREAL_RAG_USER"
        self.DB_PASS_ENV_VAR = "SURREAL_RAG_PASS"
        self.DB_URL_ENV_VAR = "SURREAL_RAG_DB_URL"
        self.DB_NS_ENV_VAR = "SURREAL_RAG_DB_NS"
        self.DB_DB_ENV_VAR = "SURREAL_RAG_DB_DB"
    
        
        #The path to your SurrealDB instance
        #The the SurrealDB namespace and database to upload the model to
        self.DB_PARAMS = SurrealParams()
                    
        #For use in authenticating your database in database.py
        #These are just the pointers to the env variables
        #Don't put the actual passwords here
    def AddArgs(self, parser:argparse.ArgumentParser):
        
        parser.add_argument("-urlenv","--url_env", help="Your env variable for Path to your SurrealDB instance (Default: {0})".format(self.DB_URL_ENV_VAR))
        parser.add_argument("-nsenv","--namespace_env", help="Your env variable for SurrealDB namespace to create and install the data (Default: {0})".format(self.DB_NS_ENV_VAR))
        parser.add_argument("-dbenv","--database_env", help="Your env variable for SurrealDB database to create and install the data (Default: {0})".format(self.DB_DB_ENV_VAR))
        parser.add_argument("-uenv","--user_env", help="Your env variable for db username (Default: {0})".format(self.DB_USER_ENV_VAR))
        parser.add_argument("-penv","--pass_env", help="Your env variable for db password (Default: {0})".format(self.DB_PASS_ENV_VAR))


        parser.add_argument("-url","--url", help="Your Path to your SurrealDB instance (Default: {0})".format("<from env variable>"))
        parser.add_argument("-ns","--namespace", help="Your SurrealDB namespace to create and install the data (Default: {0})".format("<from env variable>"))
        parser.add_argument("-db","--database", help="Your SurrealDB database to create and install the data (Default: {0})".format("<from env variable>"))
        parser.add_argument("-u","--username", help="Your db username (Default: {0})".format("<from env variable>"))
        parser.add_argument("-p","--password", help="Your db password (Default: {0})".format("<from env variable>"))
        
    def SetArgs(self,args:argparse.Namespace):
        if args.url_env:
            self.DB_URL_ENV_VAR = args.url_env
        if args.namespace_env:
            self.DB_NS_ENV_VAR = args.namespace_env
        if args.database_env:
            self.DB_DB_ENV_VAR = args.database_env
        if args.user_env:
            self.DB_USER_ENV_VAR = args.user_env
        if args.pass_env:
            self.DB_PASS_ENV_VAR = args.pass_env

        if args.url:
            self.DB_PARAMS.url = args.url
        else:
            self.DB_PARAMS.url = os.getenv(self.DB_URL_ENV_VAR)

        if args.namespace:
            self.DB_PARAMS.namespace = args.namespace
        else:
            self.DB_PARAMS.namespace = os.getenv(self.DB_NS_ENV_VAR)

        if args.database:
            self.DB_PARAMS.database = args.database
        else:
            self.DB_PARAMS.database = os.getenv(self.DB_DB_ENV_VAR)

        if args.username:
            self.DB_PARAMS.username = args.username
        else:
            self.DB_PARAMS.username = os.getenv(self.DB_USER_ENV_VAR)

        if args.password:
            self.DB_PARAMS.password = args.password
        else:
            self.DB_PARAMS.password = os.getenv(self.DB_PASS_ENV_VAR)

        
    

    

class ArgsLoader():

    def __init__(self,description,
            db_params: DatabaseParams,model_params: ModelParams):
        self.parser = argparse.ArgumentParser(description=description)
        self.db_params = db_params
        self.model_params = model_params
        self.model_params.AddArgs(self.parser)
        self.db_params.AddArgs(self.parser)
        self.AdditionalArgs = {}

    def AddArg(self,name:str,flag:str,action:str,help:str,default:str):
        self.parser.add_argument(f"-{flag}",f"--{action}", help=help.format(default))
        self.AdditionalArgs[name] = {"flag":flag,"action":action,"value":default}
        

    

    def LoadArgs(self):
        self.args = self.parser.parse_args()
        self.db_params.SetArgs(self.args)
        self.model_params.SetArgs(self.args)
        for key in self.AdditionalArgs.keys():
            if getattr(self.args, self.AdditionalArgs[key]["action"]):
                self.AdditionalArgs[key]["value"] = getattr(self.args, self.AdditionalArgs[key]["action"])

    def string_to_print(self):
        ret_val = self.parser.description


        ret_val += "\n\nDB Params:"
        ret_val += ArgsLoader.dict_to_str(self.db_params.DB_PARAMS.__dict__)
        ret_val += "\n\nModel Params:"
        ret_val += ArgsLoader.dict_to_str(self.model_params.__dict__)
        ret_val += "\n\nAdditional Params:"
        ret_val += ArgsLoader.additional_args_dict_to_str(self.AdditionalArgs)
        return ret_val

        ret_val += f"\n{self.db_params.DB_PARAMS.__dict__}"
        ret_val += f"\n{self.model_params.__dict__}"
        for key in self.AdditionalArgs.keys():
            ret_val += f"\n{key} : {self.AdditionalArgs[key]["value"]}"
        return ret_val
    
    def additional_args_dict_to_str(the_dict:dict):
        ret_val = ""
        for key in the_dict.keys():
            ret_val += f"\n{key} : {the_dict[key]["value"]}"
        return ret_val


    def dict_to_str(the_dict:dict):
        ret_val = ""
        for key in the_dict.keys():
            ret_val += f"\n{key} : {the_dict[key]}"
        return ret_val


    
    def print(self):
        print(self.string_to_print())





        



       
        
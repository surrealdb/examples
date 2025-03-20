import argparse
import os


DEFAULT_WIKI_URL = "https://cdn.openai.com/API/examples/data/vector_database_wikipedia_articles_embedded.zip"
DEFAULT_WIKI_ZIP_PATH = "data/vector_database_wikipedia_articles_embedded.zip"
DEFAULT_WIKI_PATH = "data/vector_database_wikipedia_articles_embedded.csv"

DEFAULT_GLOVE_URL = "https://nlp.stanford.edu/data/glove.6B.zip"
DEFAULT_GLOVE_ZIP_PATH = "data/glove.6B.zip"
DEFAULT_GLOVE_PATH = "data/glove.6B.300d.txt"

DEFAULT_FS_WIKI_PATH = "data/custom_fast_wiki_text.txt"

EDGAR_FOLDER = "data/edgar/"
DEFAULT_EDGAR_FOLDER_FILE_INDEX = "data/edgar/index.csv"
DEFAULT_EDGAR_PATH = "data/vector_database_edgar_data_embedded.csv"
DEFAULT_EDGAR_GRAPH_PATH = "data/graph_database_edgar_data.csv"
FS_EDGAR_PATH = "data/custom_fast_edgar_text.txt"
DEFAULT_CHUNK_SIZE = 500
EDGAR_PUBLIC_COMPANIES_LIST = "data/public_companies.csv"

COMMON_FUNCTIONS_DDL = "./schema/common_function_ddl.surql"
COMMON_TABLES_DDL = "./schema/common_tables_ddl.surql"
CORPUS_TABLE_DDL = "./schema/corpus_table_ddl.surql"
CORPUS_GRAPH_TABLE_DDL = "./schema/corpus_graph_tables_ddl.surql"



class SurrealDML():
    
    # SurrealQL query to get embedding model definitions
    GET_EMBED_MODEL_DESCRIPTIONS = """
        SELECT * FROM embedding_model_definition;
    """

    # Mapping of embedding models to their field names and definitions
    EMBED_MODEL_DEFINITIONS = {
        "GLOVE":{"field_name":"content_glove_vector","model_definition":[
            'GLOVE',
            '6b 300d'
            ]},
        "OPENAI":{"field_name":"content_openai_vector","model_definition":[
            'OPENAI',
            'text-embedding-ada-002'
            ]},
        "FASTTEXT":{"field_name":"content_fasttext_vector","model_definition":[
            'FASTTEXT',
            'wiki'
            ]},
    }


    # SurrealQL query to update corpus table information    
    def DELETE_CORPUS_TABLE_INFO(TABLE_NAME:str):
        return f"""
                DELETE FROM corpus_table_model WHERE corpus_table = corpus_table:{TABLE_NAME};
                DELETE corpus_table:{TABLE_NAME};  
            """
    

    # SurrealQL query to update corpus graph table information    
    def DELETE_CORPUS_GRAPH_TABLE_INFO(TABLE_NAME:str):
        return f"""
                DELETE corpus_graph_tables:{TABLE_NAME};  
            """
    

    # SurrealQL query to update corpus table information    
    def UPDATE_CORPUS_TABLE_INFO(TABLE_NAME:str,DISPLAY_NAME:str):
        
       
          
        return f"""

                LET $chunk_size =  IF $chunk_size = None THEN 
                    math::ceil(math::mean( SELECT VALUE text.split(' ').len() FROM embedded_wiki))
                ELSE 
                    $chunk_size
                END; 
                DELETE FROM corpus_table_model WHERE corpus_table = corpus_table:{TABLE_NAME};
                FOR $model IN $embed_models {{
                    LET $model_definition = type::thing("embedding_model_definition",$model.model_id);
                    UPSERT corpus_table_model:[corpus_table:{TABLE_NAME},$model_definition] SET model = $model_definition,field_name = $model.field_name, corpus_table=corpus_table:{TABLE_NAME};
                }};
                UPSERT corpus_table:{TABLE_NAME} SET table_name = '{TABLE_NAME}', display_name = '{DISPLAY_NAME}', chunk_size = $chunk_size,
                    embed_models = (SELECT value id FROM corpus_table_model WHERE corpus_table = corpus_table:{TABLE_NAME}) RETURN NONE;
                    
            """
    

    # SurrealQL query to update corpus table information    
    def UPDATE_CORPUS_GRAPH_TABLE_INFO(TABLE_NAME:str):
      
        return f"""
                UPSERT corpus_graph_tables:{TABLE_NAME} SET corpus_table = corpus_table:{TABLE_NAME}, 
                entity_display_name = $entity_display_name,
                entity_table_name = $entity_table_name,
                relation_display_name = $relation_display_name, 
                relation_table_name = $relation_table_name
                  RETURN NONE;
            """

    # SurrealQL query to insert corpus table records
    def INSERT_RECORDS(TABLE_NAME:str):
        return f"""
        FOR $row IN $records {{
            CREATE type::thing("{TABLE_NAME}",$row.url)  CONTENT {{
                url : $row.url,
                title: $row.title,
                text: $row.text,
                content_glove_vector: IF $row.content_glove_vector= NULL THEN None ELSE $row.content_glove_vector END,
                content_openai_vector: IF $row.content_openai_vector= NULL THEN None ELSE $row.content_openai_vector END,
                content_fasttext_vector: IF $row.content_fasttext_vector= NULL THEN None ELSE $row.content_fasttext_vector END,
                additional_data: IF $row.additional_data= NULL THEN None ELSE $row.additional_data END
            }} RETURN NONE;
        }};
    """


    # SurrealQL query to insert corpus graph entity table records
    def INSERT_GRAPH_ENTITY_RECORDS(TABLE_NAME:str):
        return f"""
        FOR $row IN $records {{
            CREATE type::thing("{TABLE_NAME}",$row.full_id)  CONTENT {{
                source_document : $row.source_document,
                entity_type: $row.entity_type,
                identifier: $row.identifier,
                name: $row.name,
                contexts: $row.contexts,
                context_glove_vector: IF $row.content_glove_vector= NULL THEN None ELSE $row.content_glove_vector END,
                context_openai_vector: IF $row.content_openai_vector= NULL THEN None ELSE $row.content_openai_vector END,
                context_fasttext_vector: IF $row.content_fasttext_vector= NULL THEN None ELSE $row.content_fasttext_vector END,
                additional_data: IF $row.additional_data = NULL THEN None ELSE $row.additional_data END
            }} RETURN NONE;
        }};
    """


    # SurrealQL query to insert corpus graph entity table records
    def INSERT_GRAPH_RELATION_RECORDS(ENTITY_TABLE_NAME:str,RELATE_TABLE_NAME:str,):
        return f"""
        # entity1 and entity2 are arrays in format [source_document,entity_type,identifier] that are the ids
        FOR $row IN $records {{
            LET $ent1 = type::thing("{ENTITY_TABLE_NAME}",$row.entity1);
            LET $ent2 = type::thing("{ENTITY_TABLE_NAME}",$row.entity2);
            RELATE 
            $ent1
                -> {RELATE_TABLE_NAME} -> 
            $ent2
                  CONTENT {{
                source_document : $row.source_document,
                confidence: $row.confidence,
                relationship: $row.relationship,
                contexts: $row.contexts,
                context_glove_vector: IF $row.content_glove_vector= NULL THEN None ELSE $row.content_glove_vector END,
                context_openai_vector: IF $row.content_openai_vector= NULL THEN None ELSE $row.content_openai_vector END,
                context_fasttext_vector: IF $row.content_fasttext_vector= NULL THEN None ELSE $row.content_fasttext_vector END
            }} RETURN NONE;
        }};
    """



class SurrealParams():
    """
    Class to hold SurrealDB connection parameters.
    """
    def __init__(self = None, url = None,username = None, password = None, namespace = None, database = None):
        
        self.username = username
        self.password = password
        self.namespace = namespace
        self.database = database
        self.url = url

    """
      Parses the SurrealDB response for errors.

      Args:
          outcome (dict): The SurrealDB response.

      Returns:
          dict: The parsed response, or None if the outcome is None.

      Raises:
          SystemError: If an error is found in the response.
      """
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

    def __init__(self):

        #These are just the pointers to the env variables
        #Don't put the actual tokens here

        self.openai_token_env_var = "OPENAI_API_KEY"
        self.openai_token = None
        self.gemini_token_env_var = "GOOGLE_GENAI_API_KEY"
        self.gemini_token = None
       
    """
    Adds command-line arguments for model parameters.

    Args:
        parser (argparse.ArgumentParser): The argument parser.
    """
    def AddArgs(self, parser:argparse.ArgumentParser):
        parser.add_argument("-oenv","--openai_token_env", help="Your env variable for LLM openai_token (Default: {0} for ollama hosted ignore)".format(self.openai_token_env_var))
        parser.add_argument("-genv","--gemini_token_env", help="Your env variable for LLM gemini_token (Default: {0} for ollama hosted ignore)".format(self.gemini_token_env_var))
        
    """
    Sets model parameters from command-line arguments and environment variables.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.
    """    
    def SetArgs(self,args:argparse.Namespace):
        if args.openai_token_env:
            self.openai_token_env_var = args.openai_token_env
        
        self.openai_token = os.getenv(self.openai_token_env_var)

        if args.gemini_token_env:
            self.gemini_token_env_var = args.gemini_token_env
        self.gemini_token = os.getenv(self.gemini_token_env_var)




    
    
class DatabaseParams():
    def __init__(self):

        #The path to your SurrealDB instance
        #The the SurrealDB namespace and database 
        #For use in authenticating your database
        #These are just the pointers to the env variables
        #Don't put the actual passwords here

        self.DB_USER_ENV_VAR = "SURREAL_RAG_USER"
        self.DB_PASS_ENV_VAR = "SURREAL_RAG_PASS"
        self.DB_URL_ENV_VAR = "SURREAL_RAG_DB_URL"
        self.DB_NS_ENV_VAR = "SURREAL_RAG_DB_NS"
        self.DB_DB_ENV_VAR = "SURREAL_RAG_DB_DB"
    
        
        self.DB_PARAMS = SurrealParams()
                    

     
    """
    Sets model parameters from command-line arguments and environment variables.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.
    """   
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

        
    

    
"""
Class to load and manage command-line arguments using argparse.
"""
class ArgsLoader():
    """
        Initializes the ArgsLoader with a description and parameter objects.

    Args:
        description (str): Description of the program for the help message.
        db_params (DatabaseParams): Instance of DatabaseParams to manage database arguments.
        model_params (ModelParams): Instance of ModelParams to manage model arguments.
    """
    def __init__(self,description,
            db_params: DatabaseParams,model_params: ModelParams):
        self.parser = argparse.ArgumentParser(description=description)
        self.db_params = db_params
        self.model_params = model_params
        self.model_params.AddArgs(self.parser)
        self.db_params.AddArgs(self.parser)
        self.AdditionalArgs = {}
    
    """
    Adds a custom argument to the parser.

    Args:
        name (str): Name of the argument.
        flag (str): Short flag for the argument (e.g., 'f').
        action (str): Long flag for the argument (e.g., 'file').
        help (str): Help message for the argument.
        default (str): Default value for the argument.
    """
    def AddArg(self,name:str,flag:str,action:str,help:str,default:str):
        self.parser.add_argument(f"-{flag}",f"--{action}", help=help.format(default))
        self.AdditionalArgs[name] = {"flag":flag,"action":action,"value":default}
        

    """
        Parses the command-line arguments and sets the parameter objects.
    """
    def LoadArgs(self):
        self.args = self.parser.parse_args()
        self.db_params.SetArgs(self.args)
        self.model_params.SetArgs(self.args)
        for key in self.AdditionalArgs.keys():
            if getattr(self.args, self.AdditionalArgs[key]["action"]):
                self.AdditionalArgs[key]["value"] = getattr(self.args, self.AdditionalArgs[key]["action"])
    """
    Generates a formatted string containing all parsed arguments.

    Returns:
        str: Formatted string of arguments.
    """
    def string_to_print(self):
        ret_val = self.parser.description


        ret_val += "\n\nDB Params:"
        ret_val += ArgsLoader.dict_to_str(self.db_params.DB_PARAMS.__dict__)
        ret_val += "\n\nModel Params:"
        ret_val += ArgsLoader.dict_to_str(self.model_params.__dict__)
        ret_val += "\n\nAdditional Params:"
        ret_val += ArgsLoader.additional_args_dict_to_str(self.AdditionalArgs)
        return ret_val

    """
    Converts a dictionary of additional arguments to a formatted string.

    Args:
        the_dict (dict): Dictionary of additional arguments.

    Returns:
        str: Formatted string.
    """
    def additional_args_dict_to_str(the_dict:dict):
        ret_val = ""
        for key in the_dict.keys():
            ret_val += f"\n{key} : {the_dict[key]["value"]}"
        return ret_val

    """
    Converts a dictionary to a formatted string.

    Args:
        the_dict (dict): Dictionary to convert.

    Returns:
        str: Formatted string.
    """
    def dict_to_str(the_dict:dict):
        ret_val = ""
        for key in the_dict.keys():
            ret_val += f"\n{key} : {the_dict[key]}"
        return ret_val


    """
    Prints the formatted string of arguments.
    """
    def print(self):
        print(self.string_to_print())





        



       
        
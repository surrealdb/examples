import argparse
from surrealdb_rag.helpers.params import DatabaseParams, ModelParams

"""
This file defines global constants, file paths, used throughout the application.
It also includes classes for managing and command-line arguments.
"""

# --- File and URL Constants ---

DEFAULT_WIKI_URL = "https://cdn.openai.com/API/examples/data/vector_database_wikipedia_articles_embedded.zip"
"""
The default URL for downloading the Wikipedia articles dataset.
"""
DEFAULT_WIKI_ZIP_PATH = "data/vector_database_wikipedia_articles_embedded.zip"
"""
The default path where the downloaded Wikipedia articles dataset zip file is saved.
"""
DEFAULT_WIKI_PATH = "data/vector_database_wikipedia_articles_embedded.csv"
"""
The default path to the extracted CSV file containing the Wikipedia articles.
"""

DEFAULT_GLOVE_URL = "https://nlp.stanford.edu/data/glove.6B.zip"
"""
The default URL for downloading the GloVe word embedding model.
"""
DEFAULT_GLOVE_ZIP_PATH = "data/glove.6B.zip"
"""
The default path where the downloaded GloVe word embedding model zip file is saved.
"""
DEFAULT_GLOVE_PATH = "data/glove.6B.300d.txt"
"""
The default path to the extracted GloVe word embedding model text file.
"""

DEFAULT_FS_WIKI_PATH = "data/custom_fast_wiki_text.txt"
"""
The default path to the custom FastText model trained on Wikipedia data.
"""

EDGAR_FOLDER = "data/edgar/"
"""
The default folder where EDGAR filings are stored.
"""
DEFAULT_EDGAR_FOLDER_FILE_INDEX = "data/edgar/index.csv"
"""
The default path to the CSV file that indexes the downloaded EDGAR filings.
"""
DEFAULT_EDGAR_PATH = "data/vector_database_edgar_data_embedded.csv"
"""
The default path to the CSV file containing EDGAR data with embeddings.
"""
DEFAULT_EDGAR_GRAPH_PATH = "data/graph_database_edgar_data.csv"
"""
The default path to the CSV file containing EDGAR graph data (entities and relationships).
"""
FS_EDGAR_PATH = "data/custom_fast_edgar_text.txt"
"""
The default path to the custom FastText model trained on EDGAR data.
"""
DEFAULT_CHUNK_SIZE = 500
"""
The default chunk size used for processing large text files or data.
"""
EDGAR_PUBLIC_COMPANIES_LIST = "data/public_companies.csv"
"""
The default path to the CSV file containing metadata about public companies.
"""

# --- Schema Definition Files ---

COMMON_FUNCTIONS_DDL = "./schema/common_function_ddl.surql"
"""
The path to the SurrealQL file containing common function definitions.
"""
COMMON_TABLES_DDL = "./schema/common_tables_ddl.surql"
"""
The path to the SurrealQL file containing common table schema definitions.
"""
CORPUS_TABLE_DDL = "./schema/corpus_table_ddl.surql"
"""
The path to the SurrealQL file containing the schema definition for corpus tables.
"""
CORPUS_GRAPH_TABLE_DDL = "./schema/corpus_graph_tables_ddl.surql"
"""
The path to the SurrealQL file containing the schema definition for corpus graph tables.
"""


class ArgsLoader():
    """
    Class to load and manage command-line arguments using argparse.
    """

    def __init__(self, description,
                 db_params: DatabaseParams, model_params: ModelParams):
        """
        Initializes the ArgsLoader with a description and parameter objects.

        Args:
            description (str): Description of the program for the help message.
            db_params (DatabaseParams): Instance of DatabaseParams to manage database arguments.
            model_params (ModelParams): Instance of ModelParams to manage model arguments.
        """
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

    def AddArg(self, name: str, flag: str, action: str, help: str, default: str):
        """
        Adds a custom argument to the argument parser.

        Args:
            name (str): The name of the argument (used as a key in AdditionalArgs).
            flag (str): The short flag for the argument (e.g., '-f').
            action (str): The long flag for the argument (e.g., '--file').
            help (str): The help message to display for the argument.
            default (str): The default value for the argument.
        """
        self.parser.add_argument(f"-{flag}", f"--{action}", help=help.format(default))
        self.AdditionalArgs[name] = {"flag": flag, "action": action, "value": default}

    """
        Parses the command-line arguments and sets the parameter objects.
    """

    def LoadArgs(self):
        """
        Parses the command-line arguments and sets the database and model parameters.

        This method should be called after all arguments have been added using `AddArg`.
        """
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
        """
        Generates a formatted string containing all parsed arguments and their values.

        This is useful for logging or debugging purposes to see the configuration of the
        application based on the provided arguments.

        Returns:
            str: A formatted string representing all parsed arguments.
        """
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

    def additional_args_dict_to_str(the_dict: dict):
        """
        Converts a dictionary of additional arguments to a formatted string.

        This method is used to format the custom arguments added using `AddArg`.

        Args:
            the_dict (dict): The dictionary of additional arguments.

        Returns:
            str: A formatted string representing the additional arguments.
        """
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

    def dict_to_str(the_dict: dict):
        """
        Converts a dictionary to a formatted string.

        This method is used to format the database and model parameters.

        Args:
            the_dict (dict): The dictionary to convert.

        Returns:
            str: A formatted string representing the dictionary.
        """
        ret_val = ""
        for key in the_dict.keys():
            ret_val += f"\n{key} : {the_dict[key]}"
        return ret_val

    """
    Prints the formatted string of arguments.
    """

    def print(self):
        """
        Prints the formatted string of all arguments.

        This method is a convenience method to display the parsed arguments.
        """
        print(self.string_to_print())




        


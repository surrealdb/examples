import argparse
import os
import datetime 
import pandas as pd
from graph_examples.helpers.params import DatabaseParams
import subprocess
import re

import tqdm
import numpy as np
# --- Configuration (Assuming these constants are defined elsewhere) ---
# Make sure these paths are correctly defined in your constants file or here
# Example definitions if constants not available:
BASE_OUTPUT_DIR = './data/'
FAST_TEXT_DIR = os.path.join(BASE_OUTPUT_DIR, 'fast_text/')


PART1_DIR = os.path.join(BASE_OUTPUT_DIR, 'adv_data/part1/')
INVESTMENT_ADVISER_FIRMS_DIR = os.path.join(BASE_OUTPUT_DIR, 'adv_data/IA/')

FOIA_DATA_PAGE = "https://www.sec.gov/foia-services/frequently-requested-documents/form-adv-data"
ADVISER_DATA_PAGE = "https://www.sec.gov/data-research/sec-markets-data/information-about-registered-investment-advisers-exempt-reporting-advisers"
# --- End Configuration ---

ADV_TABLES_DDL= "./schema/ADV_tables_ddl.surql"
ADV_FUNCTIONS_DDL= "./schema/ADV_functions_ddl.surql"
ADV_PERSON_TABLES_INDEX_DDL= "./schema/ADV_person_tables_indexes_ddl.surql"
ADV_FIRM_TABLES_INDEX_DDL= "./schema/ADV_indexes_for_firm_matching_ddl.surql"
ADV_APP_SEARCH_INDEX_DDL= "./schema/ADV_search_indexes_ddl.surql"

GEO_WORDS = [
    "AMERICAN",
    "AMERICAS",
    "ASIA",
    "ASIAPACIFIC",
    "BOSTON",
    "EUROPE",
    "GLOBAL",
    "INTERNATIONAL",
    "IRELAND",
    "LONDON",
    "LUXEMBOURG",
    "PACIFIC",
    "UK",
    "US",
    "USA",
    "WORLD"
]

JARGON_WORDS = [
    "ADVISER",
    "ADVISERS",
    "ADVISOR",
    "ADVISORS",
    "ADVOCATE",
    "ADVOCATES",
    "ADVISORY",
    "ALTERNATIVE",
    "ASSET",
    "ASSETS",
    "ASSOCIATES",
    "CAPITAL",
    "CENTER",
    "CLIENT",
    "CO",
    "COMPANY",
    "CONSULTING",
    "CORNERSTONE",
    "CORPORATION",
    "COUNSEL",
    "CREDIT",
    "DIVERSIFIED",
    "EQUITIES",
    "EQUITY",
    "ESTATE",
    "ETF",
    "FAMILY",
    "FIDUCIARY",
    "FINANCIAL",
    "FOR",
    "FUND",
    "FUNDS",
    "GLOBAL",
    "GROWTH",
    "GROUP",
    "HARVEST",
    "HERITAGE",
    "IMPACT",
    "INC",
    "INCOME",
    "INCORPORATED",
    "INDEPENDENCE",
    "INDEPENDENT",
    "INFRASTRUCTURE",
    "INSURANCE",
    "INTEGRATED",
    "INTEGRITY",
    "INVESTMENT",
    "INVESTMENTS",
    "INVESTOR",
    "INVESTORS",
    "LEGACY",
    "LIMITED",
    "LLC",
    "LLP",
    "LP",
    "LTD",
    "MANAGEMENT",
    "MANAGER",
    "NETWORK",
    "PARTNERS",
    "PLANNING",
    "PORTFOLIO",
    "PRIVATE",
    "PROFESSIONAL",
    "PUBLIC",
    "QUANTITATIVE",
    "REAL",
    "RESOURCE",
    "RETIREMENT",
    "SAGE",
    "SARL",
    "SECURITIES",
    "SERVICES",
    "SOLUTIONS",
    "STRATEGIC",
    "STRATEGIES",
    "STRATEGY",
    "THE",
    "TRUST",
    "UNITED",
    "VALUE",
    "VENTURES",
    "WEALTH"
]

PUNCTUATION = [
    '.', ',', '&', '(', ')', '"', "'", "+", "!", '-', "{", "}", "[", "]", ":", ";", "<", ">", "`", "/", "\\", "—", "–"
]
    
    


def get_file_encoding(filepath):
    """
    Gets the encoding of a file using the 'file -I' command.

    Args:
        filepath: The path to the file.

    Returns:
        The encoding string (e.g., 'us-ascii', 'iso-8859-1'), or a fallback if an error occurs.
    """
    try:
        result = subprocess.run(['file', '-I', filepath], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        match = re.search(r'charset=([\w-]+)', output)
        if match:
            encoding = match.group(1).lower()
            return encoding
        else:
            print(f"Warning: Could not determine encoding for {filepath}. Trying 'iso-8859-1'.")
            return 'iso-8859-1'  # Try iso-8859-1 as a fallback
    except subprocess.CalledProcessError as e:
        print(f"Warning: Command 'file -I' failed: {e}. Trying 'iso-8859-1'.")
        return 'iso-8859-1'
    except FileNotFoundError:
        print(f"Warning: 'file' command not found. Trying 'iso-8859-1'.")
        return 'iso-8859-1'
    except Exception as e:
        print(f"Warning: An unexpected error occurred while getting encoding for {filepath}: {e}. Trying 'iso-8859-1'.")
        return 'iso-8859-1'
    



def extract_csv_data(logger,filenames:list[str],                    
                                      filter_func = None,
                                      sort_by=None,key=None,ascending=True):
    
    """
    Processes multiple CSV files, optionally filters and sorts the combined data,
    and then returns a combined DataFrame.

    Args:
        
        field_mapping: A list of dictionaries defining how DataFrame columns map to SurrealDB fields.
                        Each dictionary should have keys like 'dataframe_field_name' and 'surql_field_name'.
        logger: A logger object for logging information and errors.
        filenames: A list of CSV filenames to process.
        filter_func: An optional function to filter the combined DataFrame.
                        It should accept a pandas DataFrame and return a filtered DataFrame.
        sort_by:   An optional column name to sort the combined DataFrame by.
        key:       An optional function to use for sorting (e.g., to sort by string length).
        ascending: An optional boolean indicating whether to sort in ascending order (default is True).
    """

    dfs: list[pd.DataFrame] = []  # List to store individual dataframes


    pbar = tqdm.tqdm(filenames, desc="Processing files", unit="file")

    for filename in pbar:

        filepath = os.path.join(PART1_DIR, filename)
        pbar.set_postfix(file=filename)  # Update progress bar with current file name

        encoding_hint = get_file_encoding(filepath)  # Get the encoding hint
        # Prioritize latin1/ISO-8859-1
        encodings_to_try = ['iso-8859-1', encoding_hint]  # Try iso-8859-1 first

        df = None
        for enc in encodings_to_try:
            try:
                df = pd.read_csv(filepath, encoding=enc, encoding_errors='replace')  # Use errors='replace'
                #if enc != encoding_hint:
                #    logger.warning(f"Successfully read {filepath} using {enc} instead of {encoding_hint}.")
                break  # If successful, stop trying other encodings
            except UnicodeDecodeError:
                logger.warning(f"UnicodeDecodeError for {filepath} with {enc}.")
            except Exception as e:
                logger.error(f"An unexpected error occurred while processing {filepath}: {e}")
                break  # Stop trying if a different error occurs
            
        if df is not None:
            dfs.append(df)


    if dfs:
        concat_df = pd.concat(dfs, ignore_index=True)  # Concatenate all dataframes

        if concat_df is not None:
            if filter_func:
                concat_df = filter_func(concat_df)


            if sort_by:
                if key:
                    concat_df = concat_df.sort_values(by=sort_by, key=key, ascending=ascending)
                else:
                    concat_df = concat_df.sort_values(by=sort_by, ascending=ascending)

            concat_df = concat_df.replace([np.nan], [None])
            return concat_df
    else:
        logger.error("No valid dataframes to process. Skipping.")
        return  # Exit if no dataframes were loaded
    
def pre_process_firm_name_token_text(text:str) ->str:
        """
        Preprocesses text for storage in a text-based embedding file.

        This method converts text to lowercase, removes punctuation, normalizes whitespace,
        and escapes spaces with a special character (!).

        Args:
            text (str): The text to preprocess.

        Returns:
            str: The preprocessed text.
        """

        token = str(text).lower()
        token = token.strip()
        token = token.replace(" ","!") # escape character should be no punctuation
        return token

def clean_non_breaking_space(text: str) -> str:
    if text is None: return None
    else: 
        text = text.replace('\xa0', ' ')  # Replace non-breaking space with a regular space
        text = re.sub(r'\s+', ' ', text).strip() # Normalize whitespace
        return text
    
def clean_initials_and_punctuation_for_company_string(name: str) -> str:
    
    if name is None: return None
    name = str(name)
    name = name.upper()
    for term in PUNCTUATION:
        name = name.replace(term, '')
    name = clean_non_breaking_space(name)
    name_array = name.split(' ')
    clean_firm_string = ''
    for word in name_array:
        text = word
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation and symbols
        if len(text) > 1:
            clean_firm_string += word + ' '
        else:
            clean_firm_string += '_' + word + '_'
    clean_firm_string = clean_firm_string.replace("__", "").replace("_", " ").replace("  ", " ").strip()
    if clean_firm_string == '':
        return None 
    else:
        return clean_firm_string



def clean_company_string(name: str) -> str:
    """
    Cleans a company name string by removing jargon and geographical terms.

    This function takes a company name string, removes common jargon and geographical
    terms, and returns a cleaned version of the name.

    Args:
        name (str): The company name to clean.

    Returns:
        str: The cleaned company name.
    """
    
    if name is None: return None
    name = str(name)
    name = name.upper()
    for term in PUNCTUATION:
        name = name.replace(term, '')
    
    name = clean_non_breaking_space(name)

    name_array = name.split(' ')
    clean_firm_string = ''
    for word in name_array:
        if word not in GEO_WORDS and word not in JARGON_WORDS:
            text = word
            text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation and symbols
            
            if len(text) > 1:
                clean_firm_string += word + ' '
            else:
                #combine initials to make non-single letter words
                clean_firm_string += '_' + text + '_'
    clean_firm_string = clean_firm_string.replace("__", "").replace("_", " ").replace("  ", " ").strip()
    if clean_firm_string == '':
        return name 
    else:
        return clean_firm_string
    


def escape_token_text_for_txt_file(text:str) ->str:

    """
    Unescapes text read from a text-based embedding file.

    This method reverses the space escaping performed by `process_token_text_for_txt_file`.

    Args:
        text (str): The text to unescape.

    Returns:
        str: The unescaped text.
    """

    if text:
        return text.replace(" ","!") 
    else:
        return ""

def unescape_token_text_for_txt_file(text:str) ->str:

    """
    Unescapes text read from a text-based embedding file.

    This method reverses the space escaping performed by `process_token_text_for_txt_file`.

    Args:
        text (str): The text to unescape.

    Returns:
        str: The unescaped text.
    """

    if text:
        return text.replace("!"," ") # unescape to get back the space
    else:
        return ""

def get_parsed_data_from_field_mapping(row, field_mapping:dict):
    """
    Extracts and formats data from a DataFrame row based on a field mapping.

    This function iterates through a predefined field mapping to extract specific columns
    from a DataFrame row, casts their values to the specified Python types, and organizes
    the extracted data into a dictionary suitable for SurrealDB insertion.

    Args:
        row:           A pandas Series representing a single row from a DataFrame.
        field_mapping: A list of dictionaries. Each dictionary defines how to extract and
                       process a field. Expected keys:
                       - 'dataframe_field_name' (str): The name of the column in the DataFrame.
                       - 'surql_field_name'     (str): The name of the field in SurrealDB.
                       - 'python_type'          (type): The Python type to cast the DataFrame value to.

    Returns:
        A dictionary where keys are SurrealDB field names and values are the extracted and
        type-casted data. Nested dictionaries are created for SurrealDB fields with dot notation
        (e.g., 'section.field').
    """
    row_data = {}
    for field in field_mapping:
        if field["dataframe_field_name"] in row and row[field["dataframe_field_name"]] is not None:
            casted_value = cast_value(row[field["dataframe_field_name"]], field["python_type"])
            if casted_value is None:
                continue
            else:
                if "." in field["surql_field_name"]:
                    section, field_name = field["surql_field_name"].split(".")
                    if section not in row_data:
                        row_data[section] = {}
                    row_data[section][field_name] = casted_value
                else:
                    row_data[field["surql_field_name"]] = casted_value
    return row_data

# Helper function to create directories
def ensure_dir(directory):
    """Creates a directory if it doesn't exist."""
    os.makedirs(directory, exist_ok=True)

    

def cast_value(value, python_type):
    """
    Casts a value to a specified Python type.

    Args:
        value: The value to cast.
        python_type: The Python type to cast to (e.g., str, int, float, datetime).

    Returns:
        The cast value, or None if casting fails.
    """
    if value is None:
        return None

    try:
        if python_type == datetime:
            # Handle datetime conversion (assuming ISO format or similar)
            return pd.to_datetime(value).to_pydatetime()
        return python_type(value)
    except (ValueError, TypeError):
        print(f"Warning: Could not cast value '{value}' to type {python_type}. Returning None.")
        return None

class ArgsLoader():
    """
    Class to load and manage command-line arguments using argparse.
    """

    def __init__(self, description,
                 db_params: DatabaseParams):
        """
        Initializes the ArgsLoader with a description and parameter objects.

        Args:
            description (str): Description of the program for the help message.
            db_params (DatabaseParams): Instance of DatabaseParams to manage database arguments.
            model_params (ModelParams): Instance of ModelParams to manage model arguments.
        """
        self.parser = argparse.ArgumentParser(description=description)
        self.db_params = db_params
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




        


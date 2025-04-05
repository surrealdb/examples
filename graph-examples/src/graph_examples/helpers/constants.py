import argparse
import os
import datetime 
import pandas as pd
from graph_examples.helpers.params import DatabaseParams
import subprocess
import re
# --- Configuration (Assuming these constants are defined elsewhere) ---
# Make sure these paths are correctly defined in your constants file or here
# Example definitions if constants not available:
BASE_OUTPUT_DIR = './data/'


PART1_DIR = os.path.join(BASE_OUTPUT_DIR, 'adv_data/part1/')
INVESTMENT_ADVISER_FIRMS_DIR = os.path.join(BASE_OUTPUT_DIR, 'adv_data/IA/')

FOIA_DATA_PAGE = "https://www.sec.gov/foia-services/frequently-requested-documents/form-adv-data"
ADVISER_DATA_PAGE = "https://www.sec.gov/data-research/sec-markets-data/information-about-registered-investment-advisers-exempt-reporting-advisers"
# --- End Configuration ---

ADV_TABLES_DDL= "./schema/ADV_tables_ddl.surql"
ADV_FUNCTIONS_DDL= "./schema/ADV_functions_ddl.surql"


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

def get_parsed_data_from_field_mapping(row, field_mapping:dict):
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




        


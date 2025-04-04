import argparse
import os
from graph_examples.helpers.params import DatabaseParams

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



field_mapping = [
    {"field_display_name": "SEC Region", "dataframe_field_name": "SEC Region"},
    {"field_display_name": "Organization CRD#", "dataframe_field_name": "Organization CRD#"},
    {"field_display_name": "Firm Type", "dataframe_field_name": "Firm Type"},
    {"field_display_name": "CIK#", "dataframe_field_name": "CIK#"},
    {"field_display_name": "Primary Business Name", "dataframe_field_name": "Primary Business Name"},
    {"field_display_name": "Legal Name", "dataframe_field_name": "Legal Name"},
    {"field_display_name": "Main Office Street Address 1", "dataframe_field_name": "Main Office Street Address 1"},
    {"field_display_name": "Main Office Street Address 2", "dataframe_field_name": "Main Office Street Address 2"},
    {"field_display_name": "Main Office City", "dataframe_field_name": "Main Office City"},
    {"field_display_name": "Main Office State", "dataframe_field_name": "Main Office State"},
    {"field_display_name": "Main Office Country", "dataframe_field_name": "Main Office Country"},
    {"field_display_name": "Main Office Postal Code", "dataframe_field_name": "Main Office Postal Code"},
    {"field_display_name": "Chief Compliance Officer Name", "dataframe_field_name": "Chief Compliance Officer Name"},
    {"field_display_name": "Chief Compliance Officer Other Titles", "dataframe_field_name": "Chief Compliance Officer Other Titles"},
    {"field_display_name": "Latest ADV Filing Date", "dataframe_field_name": "Latest ADV Filing Date"},
    {"field_display_name": "Website Address", "dataframe_field_name": "Website Address"},
    {"field_display_name": "Approx. Amount of Assets", "dataframe_field_name": "1O - If yes, approx. amount of assets"},
    {"field_display_name": "Individuals (other than high net worth) - Number of Clients", "dataframe_field_name": "5D(a)(1)"},
    {"field_display_name": "Individuals (other than high net worth) - Regulatory Assets", "dataframe_field_name": "5D(a)(3)"},
    {"field_display_name": "High net worth individuals - Number of Clients", "dataframe_field_name": "5D(b)(1)"},
    {"field_display_name": "High net worth individuals - Regulatory Assets", "dataframe_field_name": "5D(b)(3)"},
    {"field_display_name": "Banking or thrift institutions - Number of Clients", "dataframe_field_name": "5D(c)(1)"},
    {"field_display_name": "Banking or thrift institutions - Regulatory Assets", "dataframe_field_name": "5D(c)(3)"},
    {"field_display_name": "Investment companies - Number of Clients", "dataframe_field_name": "5D(d)(1)"},
    {"field_display_name": "Investment companies - Regulatory Assets", "dataframe_field_name": "5D(d)(3)"},
    {"field_display_name": "Business development companies - Number of Clients", "dataframe_field_name": "5D(e)(1)"},
    {"field_display_name": "Business development companies - Regulatory Assets", "dataframe_field_name": "5D(e)(3)"},
    {"field_display_name": "Pooled investment vehicles - Number of Clients", "dataframe_field_name": "5D(f)(1)"},
    {"field_display_name": "Pooled investment vehicles - Regulatory Assets", "dataframe_field_name": "5D(f)(3)"},
    {"field_display_name": "Pension and profit sharing plans - Number of Clients", "dataframe_field_name": "5D(g)(1)"},
    {"field_display_name": "Pension and profit sharing plans - Regulatory Assets", "dataframe_field_name": "5D(g)(3)"},
    {"field_display_name": "Charitable organizations - Number of Clients", "dataframe_field_name": "5D(h)(1)"},
    {"field_display_name": "Charitable organizations - Regulatory Assets", "dataframe_field_name": "5D(h)(3)"},
    {"field_display_name": "State or municipal government entities - Number of Clients", "dataframe_field_name": "5D(i)(1)"},
    {"field_display_name": "State or municipal government entities - Regulatory Assets", "dataframe_field_name": "5D(i)(3)"},
    {"field_display_name": "Other investment advisers - Number of Clients", "dataframe_field_name": "5D(j)(1)"},
    {"field_display_name": "Other investment advisers - Regulatory Assets", "dataframe_field_name": "5D(j)(3)"},
    {"field_display_name": "Insurance companies - Number of Clients", "dataframe_field_name": "5D(k)(1)"},
    {"field_display_name": "Insurance companies - Regulatory Assets", "dataframe_field_name": "5D(k)(3)"},
    {"field_display_name": "Sovereign wealth funds - Number of Clients", "dataframe_field_name": "5D(l)(1)"},
    {"field_display_name": "Sovereign wealth funds - Regulatory Assets", "dataframe_field_name": "5D(l)(3)"},
    {"field_display_name": "Corporations or other businesses - Number of Clients", "dataframe_field_name": "5D(m)(1)"},
    {"field_display_name": "Corporations or other businesses - Regulatory Assets", "dataframe_field_name": "5D(m)(3)"},
    {"field_display_name": "Other - Number of Clients", "dataframe_field_name": "5D(n)(1)"},
    {"field_display_name": "Other - Regulatory Assets", "dataframe_field_name": "5D(n)(3)"},
    {"field_display_name": "Other - Details", "dataframe_field_name": "5D(n)(3) - Other"},
    {"field_display_name": "Discretionary Regulatory Assets", "dataframe_field_name": "5F(2)(a)"},
    {"field_display_name": "Non-Discretionary Regulatory Assets", "dataframe_field_name": "5F(2)(b)"},
    {"field_display_name": "Total Regulatory Assets", "dataframe_field_name": "5F(2)(c)"},
    {"field_display_name": "Discretionary Accounts", "dataframe_field_name": "5F(2)(d)"},
    {"field_display_name": "Non-Discretionary Accounts", "dataframe_field_name": "5F(2)(e)"},
    {"field_display_name": "Total Accounts", "dataframe_field_name": "5F(2)(f)"},
    {"field_display_name": "Non-US Regulatory Assets", "dataframe_field_name": "5F(3)"}
]

# Helper function to create directories
def ensure_dir(directory):
    """Creates a directory if it doesn't exist."""
    os.makedirs(directory, exist_ok=True)

    


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




        


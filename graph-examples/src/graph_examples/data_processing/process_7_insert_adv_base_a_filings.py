
from graph_examples.helpers.constants import * 
from graph_examples.helpers import loggers     
import tqdm
import numpy as np
import pandas as pd
import os
from surrealdb import Surreal
from graph_examples.helpers.params import DatabaseParams, SurrealParams
import datetime
import re
from graph_examples.helpers.surreal_dml import SurrealDML


db_params = DatabaseParams()
args_loader = ArgsLoader("Insert latest filings",db_params)


# Defines a mapping between DataFrame column names, user-friendly display names,
# SurrealQL field names, and their corresponding Python data types.
# This is crucial for data transformation and insertion into SurrealDB.
FIELD_MAPPING = [
{"dataframe_field_name": "FilingID", "field_display_name": "Filing ID", "surql_field_name": "filing_id", "python_type": int},
{"dataframe_field_name": "1D", "field_display_name": "SEC#", "surql_field_name": "sec_number", "python_type": str},
{"dataframe_field_name": "1E1", "field_display_name": "CRC number", "surql_field_name": "crc_number", "python_type": int},
{"dataframe_field_name": "Execution Type", "field_display_name": "Execution Type", "surql_field_name": "execution_type", "python_type": str},
{"dataframe_field_name": "Execution Date", "field_display_name": "Execution Date", "surql_field_name": "execution_date", "python_type": datetime},
{"dataframe_field_name": "Signatory", "field_display_name": "Signatory", "surql_field_name": "signatory_name", "python_type": str},
{"dataframe_field_name": "Title", "field_display_name": "Signatory Title", "surql_field_name": "signatory_title", "python_type": str},
]

# need to add 1E1 for CRC number for link to pdf


def insert_data_into_surrealdb(logger,connection:Surreal,data):
    """
    Inserts filing data into SurrealDB using the 'fn::filing_upsert' function.

    This function takes filing data (parsed from a row of a DataFrame) and constructs
    a SurrealQL query to insert or update a 'filing' record. It checks for the
    presence of required fields and logs any errors during the insertion process.

    Args:
        logger: A logger object for logging information and errors.
        connection: A SurrealDB connection object.
        data: A dictionary containing the filing data to be inserted/updated.
              This dictionary should align with the parameters of the 'fn::filing_upsert'
              SurrealQL function.
    """

    # --- SurrealQL Query ---

    # The SurrealQL query string that calls the 'fn::filing_upsert' function.
    # This function is assumed to exist in the SurrealDB database and handles
    # the upsert (update or insert) logic for 'filing' records.
    insert_surql = """ 
        fn::filing_upsert(
            $filing_id,
            $sec_number,
            $execution_type,
            $execution_date,
            $signatory_name,
            $signatory_title,
            $crc_number)
        """
    
    # --- Parameter Construction and Validation ---

    # Check if all the required data fields are present.
    # These fields are considered essential for inserting a filing record.
    if ("filing_id" in data 
        and "sec_number" in data
        and "execution_type" in data
        and "execution_date" in data
        and "signatory_name" in data
        and "signatory_title" in data):

        # Construct the 'params' dictionary, which will be passed as parameters
        # to the SurrealQL query.

        params = {
            "filing_id": data["filing_id"],
            "sec_number": data["sec_number"],
            "execution_type": data["execution_type"],
            "execution_date": data["execution_date"],
            "signatory_name": data["signatory_name"],
            "signatory_title": data["signatory_title"],
            "crc_number": str(data["crc_number"]),
            }
        # --- Execute the Query ---

        try:
            # Execute the SurrealQL query with the constructed parameters.
            # 'SurrealParams.ParseResponseForErrors' is assumed to be a helper function
            # to handle potential errors in the SurrealDB response.
            SurrealParams.ParseResponseForErrors(
                connection.query_raw(insert_surql, params=params)
            )
        except Exception as e:
            # Log and raise an exception if there's an error during insertion.
            logger.error(f"Error inserting data into SurrealDB: {data}")
            raise

def process_filings():
    """
    Main function to process filings data from CSV files and insert it into SurrealDB.

    This function sets up logging, connects to SurrealDB, identifies relevant CSV files,
    and calls the necessary functions to extract and insert the data. It also sorts the
    data before insertion to improve matching.
    """

    logger = loggers.setup_logger("SurrealProcessFilings")
    args_loader.LoadArgs() # Parse command-line arguments
    logger.info(args_loader.string_to_print())

    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info("Connected to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)

        logger.info(f"Processing part 1 adv base a firms data in directory {PART1_DIR}")

        # Define regular expression patterns to identify relevant CSV files.
        file_pattern1 = re.compile(r"^IA_ADV_Base_A_.*\.csv$")
        file_pattern2 = re.compile(r"^ERA_ADV_Base_.*\.csv$")

        # Find all files in the directory that match either pattern.
        matching_files = [
            filename
            for filename in os.listdir(PART1_DIR)
            if file_pattern1.match(filename) or file_pattern2.match(filename)
        ]

        # Process the CSV files and insert data into SurrealDB.
        # The data is sorted by the length of the 'Signatory' name to improve matching
        # of compliance officers already submitted to the database.
        SurrealDML.process_csv_files_and_extract(insert_data_into_surrealdb,FIELD_MAPPING,logger,connection,matching_files,sort_by="Signatory",key=lambda x: x.str.len())
        

# --- Main execution block ---
if __name__ == "__main__":
    process_filings()
# --- End main execution block ---
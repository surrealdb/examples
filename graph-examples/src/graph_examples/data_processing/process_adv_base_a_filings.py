
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
args_loader = ArgsLoader("Input Glove embeddings model",db_params)
FIELD_MAPPING = [
{"dataframe_field_name": "FilingID", "field_display_name": "Filing ID", "surql_field_name": "filing_id", "python_type": int},
{"dataframe_field_name": "1D", "field_display_name": "SEC#", "surql_field_name": "sec_number", "python_type": str},
{"dataframe_field_name": "Execution Type", "field_display_name": "Execution Type", "surql_field_name": "execution_type", "python_type": str},
{"dataframe_field_name": "Execution Date", "field_display_name": "Execution Date", "surql_field_name": "execution_date", "python_type": datetime},
{"dataframe_field_name": "Signatory", "field_display_name": "Signatory", "surql_field_name": "signatory_name", "python_type": str},
{"dataframe_field_name": "Title", "field_display_name": "Signatory Title", "surql_field_name": "signatory_title", "python_type": str},
]


def insert_data_into_surrealdb(logger,connection:Surreal,data):
    """
    Inserts data into SurrealDB.

    Args:
        data: The data to be inserted.
    """
    # only insert data for regiestered firms
    if ("filing_id" in data 
        and "sec_number" in data
        and "execution_type" in data
        and "execution_date" in data
        and "signatory_name" in data
        and "signatory_title" in data):

        insert_surql = """ 
        fn::filing_upsert(
            $filing_id,
            $sec_number,
            $execution_type,
            $execution_date,
            $signatory_name,
            $signatory_title)
        """


        params = {
            "filing_id": data["filing_id"],
            "sec_number": data["sec_number"],
            "execution_type": data["execution_type"],
            "execution_date": data["execution_date"],
            "signatory_name": data["signatory_name"],
            "signatory_title": data["signatory_title"],
            }
        try:
            SurrealParams.ParseResponseForErrors(connection.query_raw(
                insert_surql,params=params
            ))
        except Exception as e:
            logger.error(f"Error inserting data into SurrealDB: {data}")
            raise


def process_filings():

    logger = loggers.setup_logger("SurrealProcessFilings")
    args_loader.LoadArgs() # Parse command-line arguments
    logger.info(args_loader.string_to_print())

    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info("Connected to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)

        logger.info(f"Processing part 1 adv base a firms data in directory {PART1_DIR}")

        file_pattern1 = re.compile(r"^IA_ADV_Base_A_.*\.csv$")
        file_pattern2 = re.compile(r"^ERA_ADV_Base_.*\.csv$")

        matching_files = [
            filename
            for filename in os.listdir(PART1_DIR)
            if file_pattern1.match(filename) or file_pattern2.match(filename)
        ]

        # sort by shortest values of person's name to try to match on already submitted compliance officers
        SurrealDML.process_csv_files_and_extract(insert_data_into_surrealdb,FIELD_MAPPING,logger,connection,matching_files,sort_by="Signatory",key=lambda x: x.str.len())
        

# --- Main execution block ---
if __name__ == "__main__":
    process_filings()
# --- End main execution block ---
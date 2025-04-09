

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



# FilingID	
# Name	
# Street 1	
# Street 2	
# City	
# State	
# Country	
# Postal Code	
# Private Residence	
# Phone	
# Fax	
# Type	
# Description


db_params = DatabaseParams()
args_loader = ArgsLoader("Input Glove embeddings model",db_params)
FIELD_MAPPING = [
    {
        "dataframe_field_name": "FilingID",
        "field_display_name": "Filing ID",
        "surql_field_name": "filing_id",
        "python_type": int,  # Assuming Filing ID is an integer
        "description": "Unique identifier for the filing.",
    },
    {
        "dataframe_field_name": "Name",
        "field_display_name": "Name",
        "surql_field_name": "name",
        "python_type": str,
        "description": "Name of the custodian holding books or records.",
    },
    {
        "dataframe_field_name": "City",
        "field_display_name": "Custodian Office City",
        "surql_field_name": "city",
        "python_type": str,
        "description": "City of the custodian's office responsible for custody of the books or records.",
    },
    {
        "dataframe_field_name": "State",
        "field_display_name": "Custodian Office State",
        "surql_field_name": "state",
        "python_type": str,
        "description": "State of the custodian's office responsible for custody of the books or records.",
    },
    {
        "dataframe_field_name": "Postal Code",
        "field_display_name": "Custodian Office Postal Code",
        "surql_field_name": "postal_code",
        "python_type": str,
        "description": "Country of the custodian's office responsible for custody of the books or records.",
    },
    {
        "dataframe_field_name": "Country",
        "field_display_name": "Custodian Office Country",
        "surql_field_name": "country",
        "python_type": str,
        "description": "Country of the custodian's office responsible for custody of the books or records.",
    },
    {
        "dataframe_field_name": "Type",
        "field_display_name": "Type of Custodian",
        "surql_field_name": "type",
        "python_type": str,
        "description": "Nature of the custodian's relationship to the books or records.",
    },
    {
        "dataframe_field_name": "Description",
        "field_display_name": "Description",
        "surql_field_name": "description",
        "python_type": str,
        "description": "Description of the custodian's relationship to the books or records.",
    },
]


def insert_data_into_surrealdb(logger,connection:Surreal,data):
    """
    Inserts data into SurrealDB.

    Args:
        data: The data to be inserted.
    """

    insert_surql = """ 
    fn::b_and_r_upsert(
        $filing_id,
        $name,
        $type,
        $city,
        $state,
        $postal_code,
        $country,
        $description,
        )
    """


    if ("filing_id" in data 
        and "name" in data
        and "type" in data):
        params = {
            "filing_id": data["filing_id"],
            "name": data["name"],
            "type": data["type"],
        }


        if "city" in data:
            params["city"] = data["city"]
        if "state" in data:
            params["state"] = data["state"]
        if "country" in data:
            params["country"] = data["country"]
        if "postal_code" in data:
            params["postal_code"] = data["postal_code"]
        if "description" in data:
            params["description"] = data["description"]


        try:
            SurrealParams.ParseResponseForErrors(connection.query_raw(
                insert_surql,params=params
            ))
        except Exception as e:
            logger.error(f"Error inserting data into SurrealDB: {data}")
            


        

def process_filing_books_records_data_files():

    logger = loggers.setup_logger("SurrealProcessD-Books-Records")
    args_loader.LoadArgs() # Parse command-line arguments
    logger.info(args_loader.string_to_print())

    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info("Connected to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)

        logger.info(f"Processing part 1 adv base a firms data in directory {PART1_DIR}")

        file_pattern = re.compile(r".*_Schedule_D_Books_and_Records_.*\.csv$")

        matching_files = [
            filename
            for filename in os.listdir(PART1_DIR)
            if file_pattern.match(filename)
        ]

        file_tqdm = tqdm.tqdm(matching_files, desc="Processing Files", position=1)
        for filename in file_tqdm:
            file_tqdm.set_description(f"Processing {filename}")
            filepath = os.path.join(PART1_DIR, filename)
            SurrealDML.process_excel_file_and_extract(insert_data_into_surrealdb,FIELD_MAPPING,logger,connection,filepath,sort_by="Name",key=lambda x: x.str.len())
            
            

# --- Main execution block ---
if __name__ == "__main__":
    process_filing_books_records_data_files()
# --- End main execution block ---
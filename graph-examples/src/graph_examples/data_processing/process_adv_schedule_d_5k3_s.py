
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
    {
        "dataframe_field_name": "Filing ID",
        "field_display_name": "Filing ID",
        "surql_field_name": "filing_id",
        "python_type": int,  # Assuming Filing ID is an integer
        "description": "Unique identifier for the filing.",
    },
    {
        "dataframe_field_name": "5K(3)(a)",
        "field_display_name": "Legal name of custodian",
        "surql_field_name": "legal_name",
        "python_type": str,
        "description": "Legal name of the custodian holding separately managed account assets.",
    },
    {
        "dataframe_field_name": "5K(3)(b)",
        "field_display_name": "Primary business name of custodian",
        "surql_field_name": "primary_business_name",
        "python_type": str,
        "description": "Primary business name of the custodian holding separately managed account assets.",
    },
    {
        "dataframe_field_name": "5K(3)(c) City",
        "field_display_name": "Custodian Office City",
        "surql_field_name": "office_city",
        "python_type": str,
        "description": "City of the custodian's office responsible for custody of the assets.",
    },
    {
        "dataframe_field_name": "5K(3)(c) State",
        "field_display_name": "Custodian Office State",
        "surql_field_name": "office_state",
        "python_type": str,
        "description": "State of the custodian's office responsible for custody of the assets.",
    },
    {
        "dataframe_field_name": "5K(3)(c) Country",
        "field_display_name": "Custodian Office Country",
        "surql_field_name": "office_country",
        "python_type": str,
        "description": "Country of the custodian's office responsible for custody of the assets.",
    },
    {
        "dataframe_field_name": "5K(3)(d)",
        "field_display_name": "Is custodian a related person",
        "surql_field_name": "is_related_person",
        "python_type": str,
        "description": "Indicates whether the custodian is a related person of the firm (Yes/No or Y/N).",
    },
    {
        "dataframe_field_name": "5K(3)(e)",
        "field_display_name": "Custodian SEC registration number",
        "surql_field_name": "sec_number",
        "python_type": str,
        "description": "SEC registration number of the custodian (if it is a broker-dealer).",
    },
    {
        "dataframe_field_name": "5K(3)(f)",
        "field_display_name": "Custodian Legal Entity Identifier",
        "surql_field_name": "legal_entity_identifier",
        "python_type": str,
        "description": "Legal Entity Identifier (LEI) of the custodian (if not a broker-dealer or no SEC number).",
    },
    {
        "dataframe_field_name": "5K(3)(g)",
        "field_display_name": "Regulatory assets at custodian",
        "surql_field_name": "regulatory_assets",
        "python_type": float,
        "description": "Amount of regulatory assets under management attributable to separately managed accounts held at the ",
    },
]


def insert_data_into_surrealdb(logger,connection:Surreal,data):
    """
    Inserts data into SurrealDB.

    Args:
        data: The data to be inserted.
    """


    insert_surql = """ 
    fn::sma_upsert(
        $filing_id,
        $primary_business_name,
        $legal_name,
        $sec_number,
        $legal_entity_identifier,
        $office_city,
        $office_state,
        $office_country,
        $is_related_person,
        $regulatory_assets,
        )
    """


    if ("filing_id" in data 
        and "legal_name" in data
        and "primary_business_name" in data):
        params = {
            "filing_id": data["filing_id"],
            "legal_name": data["legal_name"],
            "primary_business_name": data["primary_business_name"],
        }


        if "office_city" in data:
            params["office_city"] = data["office_city"]
        if "office_state" in data:
            params["office_state"] = data["office_state"]
        if "office_country" in data:
            params["office_country"] = data["office_country"]
        if "is_related_person" in data:
            params["is_related_person"] = data["is_related_person"]
        if "legal_entity_identifier" in data:
            params["legal_entity_identifier"] = data["legal_entity_identifier"]
        if "regulatory_assets" in data:
            params["regulatory_assets"] = data["regulatory_assets"]
        if "sec_number" in data:
            params["sec_number"] = data["sec_number"]


        try:
            SurrealParams.ParseResponseForErrors(connection.query_raw(
                insert_surql,params=params
            ))
        except Exception as e:
            logger.error(f"Error inserting data into SurrealDB: {data}")
            raise


        

def process_filing_5k3_data_files():

    logger = loggers.setup_logger("SurrealProcessD-5Ks")
    args_loader.LoadArgs() # Parse command-line arguments
    logger.info(args_loader.string_to_print())

    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info("Connected to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)

        logger.info(f"Processing part 1 adv base a firms data in directory {PART1_DIR}")

        file_pattern = re.compile(r"^IA_Schedule_D_5K3_.*\.csv$")

        matching_files = [
            filename
            for filename in os.listdir(PART1_DIR)
            if file_pattern.match(filename)
        ]
        file_tqdm = tqdm.tqdm(matching_files, desc="Processing Files", position=1)
        for filename in file_tqdm:
            file_tqdm.set_description(f"Processing {filename}")
            filepath = os.path.join(PART1_DIR, filename)
            SurrealDML.process_excel_file_and_extract(insert_data_into_surrealdb,FIELD_MAPPING,logger,connection,filepath,sort_by=["5K(3)(e)","5K(3)(f)"],ascending=False) 

# --- Main execution block ---
if __name__ == "__main__":
    process_filing_5k3_data_files()
# --- End main execution block ---
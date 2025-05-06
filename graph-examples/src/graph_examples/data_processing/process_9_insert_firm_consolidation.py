
from graph_examples.helpers.constants import * 
from graph_examples.helpers import loggers     
import tqdm
import numpy as np
import pandas as pd
import os
from surrealdb import Surreal
from graph_examples.helpers.params import DatabaseParams, SurrealParams
import datetime


db_params = DatabaseParams()
args_loader = ArgsLoader("Conoslidate firms based on names,relationships and firm types",db_params)

"""
WIP
[
	{
		count: 5658,
		firm_type: firm_type:ERA
	},
	{
		count: 10418,
		firm_type: firm_type:⟨Hedge Fund⟩
	},
	{
		count: 874,
		firm_type: firm_type:⟨RAUM Custodian⟩
	},
	{
		count: 8112,
		firm_type: firm_type:⟨Records Custodian⟩
	},
	{
		count: 16000,
		firm_type: firm_type:Registered
	},
	{
		count: 25181,
		firm_type: firm_type:⟨Venture Capital Fund⟩
	}
]
"""

def process_hedges(connection:Surreal):

    top_hedge_surql = """
        
        LET $hedge_deals = SELECT in.name AS in, math::sum(assets_under_management) AS assets_under_management FROM custodian_for WHERE in.firm_type = firm_type:⟨Hedge Fund⟩ OR out.firm_type = firm_type:⟨Hedge Fund⟩
            GROUP BY in;
        LET $total_hedge_deals = $hedge_deals.len();
        RETURN $total_hedge_deals;

        SELECT * FROM $hedge_deals ORDER BY assets_under_management DESC LIMIT  <int>($total_hedge_deals/10);
    """
    return

def process_vcs(connection:Surreal):
    return

def process_books_records_holders(connection:Surreal):
    return

def dedupe_out_registered(connection:Surreal):
    return

def process_custodian_subisdiaries(connection:Surreal):
    return


def insert_data_into_surrealdb(logger,connection:Surreal,data):
    """
    Inserts data into SurrealDB using the 'fn::firm_upsert' function.

    This function takes data (presumably parsed from a row of a DataFrame)
    and constructs a SurrealQL query to insert or update a 'firm' record.
    It handles various optional fields and logs any errors during the insertion process.

    Args:
        logger: A logger object for logging information and errors.
        connection: A SurrealDB connection object.
        data: A dictionary containing the data to be inserted/updated.
              This dictionary should align with the parameters of the 'fn::firm_upsert'
              SurrealQL function.
    """

    # --- SurrealQL Query ---

    # The SurrealQL query string that calls the 'fn::firm_upsert' function.
    # This function is assumed to exist in the SurrealDB database and handles
    # the upsert (update or insert) logic for 'firm' records.

    insert_surql = """ 
    fn::firm_upsert(
        $name,
        $firm_type,
        $legal_name,
        $sec_number,
        NONE, #not private funds
        $legal_entity_identifier,
        $cik,
        $city,
        $state,
        $postal_code,
        $country,
        $section1,
        $section_5d,
        $section_5f,
        NONE #not processing filings yet
        ); 
    """



    # --- Parameter Construction ---

    # Check if the necessary 'section1' data is present.
    # The 'primary_business_name', 'sec_number', and 'firm_type' are considered
    # essential for inserting a firm.

    if ("section1" in data 
        and "primary_business_name" in data["section1"]
        and "sec_number" in data["section1"]
        and "firm_type" in data["section1"]):
        params = {
            "name": data["section1"]["primary_business_name"],
            "sec_number": data["section1"]["sec_number"],
            "firm_type": data["section1"]["firm_type"],        
            "section1": data["section1"]
            }
        

        if "cik" in data["section1"]:
            params["cik"] = data["section1"]["cik"]
        if "legal_entity_identifier" in data["section1"]:
            params["legal_entity_identifier"] = data["section1"]["legal_entity_identifier"]

        if "legal_name" in data["section1"]:
            params["legal_name"] = data["section1"]["legal_name"]
        if "main_office_city" in data["section1"]:
            params["city"] = data["section1"]["main_office_city"]
        if "main_office_state" in data["section1"]:
            params["state"] = data["section1"]["main_office_state"]
        if "main_office_postal_code" in data["section1"]:
            params["country"] = data["section1"]["main_office_postal_code"]
        if "main_office_country" in data["section1"]:
            params["country"] = data["section1"]["main_office_country"]

        if "section_5d" in data:
            params["section_5d"] = data["section_5d"]
        if "section_5f" in data:
            params["section_5f"] = data["section_5f"]

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
            logger.error(f"Error inserting data into SurrealDB: {data}: {e}")
            raise




def process_firm_consolidation():

    logger = loggers.setup_logger("SurrealProcessFirms")
    args_loader.LoadArgs() # Parse command-line arguments
    logger.info(args_loader.string_to_print())

    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info("Connected to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)

        process_hedges(connection)
        process_vcs(connection)
        process_books_records_holders(connection)
        dedupe_out_registered(connection)
        process_custodian_subisdiaries(connection)


            

# --- Main execution block ---
if __name__ == "__main__":
    process_firm_consolidation()
# --- End main execution block ---
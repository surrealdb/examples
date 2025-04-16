
from graph_examples.helpers.constants import * 
from graph_examples.helpers import loggers     
import os
from surrealdb import Surreal
from graph_examples.helpers.params import DatabaseParams, SurrealParams
import re
from graph_examples.helpers.surreal_dml import SurrealDML

db_params = DatabaseParams()
args_loader = ArgsLoader("Input registerd firms SMA filings",db_params)

# --- Field Mapping ---

# Defines a mapping between DataFrame column names, user-friendly display names,
# SurrealQL field names, Python data types, and field descriptions.
# This mapping is used for data transformation and insertion into SurrealDB.
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
    Inserts data about custodians of separately managed account assets into SurrealDB
    using the 'fn::raum_upsert' function.

    This function takes custodian data (parsed from a row of a DataFrame) and constructs
    a SurrealQL query to insert or update custodian information. It checks for the
    presence of required fields and logs any errors during the insertion process.

    Args:
        logger:     A logger object for logging information and errors.
        connection: A SurrealDB connection object.
        data:       A dictionary containing the custodian data to be inserted/updated.
                    This dictionary should align with the parameters of the 'fn::raum_upsert'
                    SurrealQL function.
    """

    # --- SurrealQL Query ---

    # The SurrealQL query string that calls the 'fn::raum_upsert' function.
    # This function is assumed to exist in the SurrealDB database and handles
    # the upsert (update or insert) logic for custodian records.

    insert_surql = """ 
    fn::raum_upsert(
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

    # --- Parameter Construction and Validation ---

    # Check if all the required data fields are present.
    # These fields are considered essential for inserting a custodian record.
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


        

def process_filing_5k3_data_files():
    """
    Main function to process data about custodians of separately managed account
    assets (Schedule D 5K3) from CSV files and insert it into SurrealDB.

    This function sets up logging, connects to SurrealDB, identifies relevant CSV files,
    and calls the necessary functions to extract and insert the data. It also sorts the
    data before insertion to improve matching.
    """
    logger = loggers.setup_logger("SurrealProcessD-5Ks")
    args_loader.LoadArgs() # Parse command-line arguments
    logger.info(args_loader.string_to_print())

    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info("Connected to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)

        logger.info(f"Processing part 1 adv base a firms data in directory {PART1_DIR}")

        # Define regular expression pattern to identify relevant CSV files.
        file_pattern = re.compile(r"^IA_Schedule_D_5K3_.*\.csv$")

        matching_files = [
            filename
            for filename in os.listdir(PART1_DIR)
            if file_pattern.match(filename)
        ]
        
        # Process the CSV files and insert data into SurrealDB.
        # The data is sorted by "5K(3)(e)" (SEC number), "5K(3)(f)" (LEI), and
        # "5K(3)(a)" (Legal name of custodian) to improve matching. Sorting is
        # done by the length of the string in descending order.
        SurrealDML.process_csv_files_and_extract(insert_data_into_surrealdb,FIELD_MAPPING,logger,connection,matching_files,sort_by=["5K(3)(e)","5K(3)(f)","5K(3)(a)"],key=lambda x: x.str.len(),ascending=False) 

# --- Main execution block ---
if __name__ == "__main__":
    process_filing_5k3_data_files()
# --- End main execution block ---
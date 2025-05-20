

from graph_examples.helpers.constants import * 
from graph_examples.helpers import loggers  
import os
from surrealdb import Surreal
from graph_examples.helpers.params import DatabaseParams, SurrealParams
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
args_loader = ArgsLoader("Input books and records filings from section d",db_params)

# Defines a mapping between DataFrame column names, user-friendly display names,
# SurrealQL field names, Python data types, and field descriptions.
# This mapping is used for data transformation and insertion into SurrealDB.
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
        "description": "Postal Code of the custodian's office responsible for custody of the books or records.",
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
    Inserts data about books and records custodians into SurrealDB
    using the 'fn::b_and_r_upsert' function.

    This function takes custodian data (parsed from a row of a DataFrame) and constructs
    a SurrealQL query to insert or update custodian information. It checks for the
    presence of required fields and logs any errors during the insertion process.

    Args:
        logger:     A logger object for logging information and errors.
        connection: A SurrealDB connection object.
        data:       A dictionary containing the custodian data to be inserted/updated.
                    This dictionary should align with the parameters of the 'fn::b_and_r_upsert'
                    SurrealQL function.
    """

    # --- SurrealQL Query ---

    # The SurrealQL query string that calls the 'fn::b_and_r_upsert' function.
    # This function is assumed to exist in the SurrealDB database and handles
    # the upsert (update or insert) logic for books and records custodian records.
    

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

    # --- Parameter Construction and Validation ---

    # Check if all the required data fields are present.
    # These fields are considered essential for inserting a custodian record.
    

    if ("filing_id" in data 
        and "name" in data
        and "type" in data):
        # Construct the 'params' dictionary, which will be passed as parameters
        # to the SurrealQL query.
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


         # --- Execute the Query ---

        try:
            # Execute the SurrealQL query with the constructed parameters.
            # 'SurrealParams.ParseResponseForErrors' is assumed to be a helper function
            # to handle potential errors in the SurrealDB response.
            SurrealParams.ParseResponseForErrors(
                connection.query_raw(insert_surql, params=params)
            )
        except Exception as e:
            # Log and raise an exception if there's an error during insertion. Don't raise the error as filings sometimes miss a firm
            logger.error(f"Error inserting data into SurrealDB: {data}")
            # raise


        

def process_filing_books_records_data_files():
    """
    Main function to process data about books and records custodians
    from CSV files and insert it into SurrealDB.

    This function sets up logging, connects to SurrealDB, identifies relevant CSV files,
    and calls the necessary functions to extract and insert the data. It also sorts the
    data before insertion to improve matching.
    """

    logger = loggers.setup_logger("SurrealProcessD-Books-Records")
    args_loader.LoadArgs() # Parse command-line arguments
    logger.info(args_loader.string_to_print())

    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info("Connected to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)

        logger.info(f"Adding indexes to firm tables if not extist") 
        with open(ADV_FIRM_TABLES_INDEX_DDL) as f: 
            surlql_to_execute = f.read()
            SurrealParams.ParseResponseForErrors( connection.query_raw(surlql_to_execute))

        logger.info(f"Processing part 1 adv base a firms data in directory {PART1_DIR}")

        # Define regular expression pattern to identify relevant CSV files.
        file_pattern = re.compile(r".*_Schedule_D_Books_and_Records_.*\.csv$")

        matching_files = [
            filename
            for filename in os.listdir(PART1_DIR)
            if file_pattern.match(filename)
        ]


        
        # Process the CSV files and insert data into SurrealDB.
        # The data is sorted by "Name" to improve matching. Sorting is done by
        # the length of the string in descending order.
        SurrealDML.process_csv_files_and_extract(insert_data_into_surrealdb,FIELD_MAPPING,logger,connection,matching_files,sort_by="Name",key=lambda x: x.str.len(),ascending=False)
        
            

# --- Main execution block ---
if __name__ == "__main__":
    process_filing_books_records_data_files()
# --- End main execution block ---
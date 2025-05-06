
from graph_examples.helpers.constants import * 
from graph_examples.helpers import loggers   
import pandas as pd
import os
from surrealdb import Surreal
from graph_examples.helpers.params import DatabaseParams, SurrealParams
import re
from graph_examples.helpers.surreal_dml import SurrealDML



# "FilingID","Fund Name","Fund ID","ReferenceID","State","Country","3(c)(1) Exclusion","3(c)(7) Exclusion","Master Fund","Feeder Fund","Master Fund Name","Master Fund ID","Fund of Funds","Fund Invested Self or Related","Fund Invested in Securities","Fund Type","Fund Type Other","Gross Asset Value","Minimum Investment","Owners","%Owned You or Related","%Owned Funds","Sales Limited","%Owned Non-US","Subadviser","Other IAs Advise","Clients Solicited","Percentage Invested","Exempt from Registration","Annual Audit","GAAP","FS Distributed","Unqualified Opinion","Prime Brokers","Custodians","Administrator","% Assets Valued","Marketing"
# need a 7b https://files.adviserinfo.sec.gov/IAPD/content/viewform/adv/Sections/iapd_AdvPrivateFundReportingSection.aspx?ORG_PK=130819&FLNG_PK=02A0D5BE000801E404F057E105A82089056C8CC0
# who manages money for boothbay

#find out why corbin is kicking butt
db_params = DatabaseParams()
args_loader = ArgsLoader("Insert private fund SMA listings from section D 7b1",db_params)

# Defines a mapping between DataFrame column names, user-friendly display names,
# SurrealQL field names, Python data types, and field descriptions.
# This mapping is used for data transformation and insertion into SurrealDB.

FIELD_MAPPING = [
    {
        "dataframe_field_name": "FilingID",
        "field_display_name": "Filing ID",
        "surql_field_name": "filing_id",
        "python_type": int,  # Assuming FilingID is an integer
        "description": "Unique identifier for the filing.",
    },
    {
        "dataframe_field_name": "Fund Name",
        "field_display_name": "Fund Name",
        "surql_field_name": "fund_name",
        "python_type": str,
        "description": "Name of the fund.",
    },
    {
        "dataframe_field_name": "Fund ID",
        "field_display_name": "Fund ID",
        "surql_field_name": "fund_id",
        "python_type": str,  # PFID 805-xxx
        "description": "Identifier of the fund.",
    },
    {
        "dataframe_field_name": "State",
        "field_display_name": "Fund State",
        "surql_field_name": "fund_state",
        "python_type": str,
        "description": "State where the fund is located/organized.",
    },
    {
        "dataframe_field_name": "Country",
        "field_display_name": "Fund Country",
        "surql_field_name": "fund_country",
        "python_type": str,
        "description": "Country where the fund is located/organized.",
    },
    {
        "dataframe_field_name": "Fund Type",
        "field_display_name": "Fund Type",
        "surql_field_name": "fund_type",
        "python_type": str,
        "description": "Type of the fund (e.g., Hedge Fund).",
    },
    {
        "dataframe_field_name": "Fund Type Other",
        "field_display_name": "Fund Type Other",
        "surql_field_name": "fund_type_other",
        "python_type": str,
        "description": "Additional information about the fund type, if applicable.",
    },
    {
        "dataframe_field_name": "Master Fund",
        "field_display_name": "Master Fund",
        "surql_field_name": "master_fund",
        "python_type": bool,
        "description": "Indicates if the fund is a master fund.",
    },
    {
        "dataframe_field_name": "Feeder Fund",
        "field_display_name": "Feeder Fund",
        "surql_field_name": "feeder_fund",
        "python_type": str,
        "description": "Indicates if the fund is a feeder fund.",
    },
    {
        "dataframe_field_name": "Master Fund Name",
        "field_display_name": "Master Fund Name",
        "surql_field_name": "master_fund_name",
        "python_type": str,
        "description": "Name of the master fund (if applicable).",
    },
    {
        "dataframe_field_name": "Master Fund ID",
        "field_display_name": "Master Fund ID",
        "surql_field_name": "master_fund_id",
        "python_type": str,  # PFID 805-xxx
        "description": "Identifier of the master fund (if applicable).",
    },
    {
        "dataframe_field_name": "Gross Asset Value",
        "field_display_name": "Gross Asset Value",
        "surql_field_name": "gross_asset_value",
        "python_type": float,
        "description": "Gross asset value of the fund.",
    },
    {
        "dataframe_field_name": "%Owned You or Related",
        "field_display_name": "Percentage Owned You or Related",
        "surql_field_name": "percentage_owned_you_or_related",
        "python_type": float,
        "description": "Percentage of the fund owned by you or related parties.",
    },
    {
        "dataframe_field_name": "%Owned Funds",
        "field_display_name": "Percentage Owned Funds",
        "surql_field_name": "percentage_owned_funds",
        "python_type": float,
        "description": "Percentage of the fund owned by other funds.",
    },
    {
        "dataframe_field_name": "Percentage Invested",
        "field_display_name": "Percentage Invested",
        "surql_field_name": "percentage_invested",
        "python_type": float,
        "description": "Percentage of assets invested by the fund.",
    },
    {
        "dataframe_field_name": "Unqualified Opinion",
        "field_display_name": "Unqualified Opinion",
        "surql_field_name": "unqualified_opinion",
        "python_type": str,  # Or bool if it's a flag (e.g., Y/N)
        "description": "Indicates whether the fund received an unqualified opinion.",
    },
]


def insert_data_into_surrealdb(logger,connection:Surreal,data):
    """
    Inserts private fund data into SurrealDB using the 'fn::pf_upsert' function.

    This function takes fund data (parsed from a row of a DataFrame) and constructs
    a SurrealQL query to insert or update a private fund record. It checks for the
    presence of required fields and logs any errors during the insertion process.

    Args:
        logger:     A logger object for logging information and errors.
        connection: A SurrealDB connection object.
        data:       A dictionary containing the private fund data to be inserted/updated.
                    This dictionary should align with the parameters of the 'fn::pf_upsert'
                    SurrealQL function.
    """

    # --- SurrealQL Query ---

    # The SurrealQL query string that calls the 'fn::pf_upsert' function.
    # This function is assumed to exist in the SurrealDB database and handles
    # the upsert (update or insert) logic for private fund records.


    insert_surql = """ 
    fn::pf_upsert(
        $filing_id,
        $fund_name,
        $fund_id,
        $fund_type,
        $feeder_fund,
        $gross_asset_value,
        $percentage_owned_you_or_related,
        $percentage_owned_funds,
        $percentage_invested,
        $unqualified_opinion,
        $master_fund_id,
        $master_fund_name,
        $state,
        $country,
        $fund_type_other
        )
    """
    # --- Parameter Construction and Validation ---

    # Check if all the required data fields are present.
    # These fields are considered essential for inserting a private fund record.

    if ("filing_id" in data 
        and "fund_name" in data
        and "fund_id" in data 
        and "fund_type" in data):

        # Construct the 'params' dictionary, which will be passed as parameters
        # to the SurrealQL query.
        params = {
            "filing_id": data["filing_id"],
            "fund_name": data["fund_name"],
            "fund_id": data["fund_id"],
            "fund_type": data["fund_type"],
        }
        if "feeder_fund" in data:
            params["feeder_fund"] = data["feeder_fund"]
        else:
            params["feeder_fund"] = "n"
            

        if "gross_asset_value" in data:
            params["gross_asset_value"] = data["gross_asset_value"]
        if "percentage_owned_you_or_related" in data:
            params["percentage_owned_you_or_related"] = data["percentage_owned_you_or_related"]
        if "percentage_owned_funds" in data:
            params["percentage_owned_funds"] = data["percentage_owned_funds"]
        if "percentage_invested" in data:
            params["percentage_invested"] = data["percentage_invested"]
        if "unqualified_opinion" in data:
            params["unqualified_opinion"] = data["unqualified_opinion"]
        if "master_fund_id" in data:
            params["master_fund_id"] = data["master_fund_id"]
        if "master_fund_name" in data:
            params["master_fund_name"] = data["master_fund_name"]
        if "state" in data:
            params["state"] = data["state"]
        if "country" in data:
            params["country"] = data["country"]
        if "fund_type_other" in data:
            params["fund_type_other"] = data["fund_type_other"]





        # --- Execute the Query ---

        try:
            # Execute the SurrealQL query with the constructed parameters.
            # 'SurrealParams.ParseResponseForErrors' is assumed to be a helper function
            # to handle potential errors in the SurrealDB response.
            SurrealParams.ParseResponseForErrors(
                connection.query_raw(insert_surql, params=params)
            )
        except Exception as e:
            # Log and raise an exception if there's an error during insertion. These errors are not recoverable so continue
            logger.error(f"Error inserting data into SurrealDB: {data}")
            # if e.message != "Error in results: Can not execute RELATE statement where property 'id' is: NONE":
            raise;


def filter_vc_hedge(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters a DataFrame to include only rows that meet the following criteria:
    - 'Fund Type' is 'Hedge Fund' or 'VC Fund' (case-insensitive)
    
    Args:
        df: The input pandas DataFrame.

    Returns:
        A new pandas DataFrame containing only the filtered rows.
    """

    # Ensure case-insensitive comparison and handle missing columns
    if 'Fund Type' in df.columns:
        fund_type_condition = df['Fund Type'].str.lower().isin(['venture capital fund', 'hedge fund'])
    else:
        fund_type_condition = pd.Series([False] * len(df))

    # Combine conditions using the OR operator
    combined_condition = fund_type_condition

    return df[combined_condition]
 

def process_filing_7b1_data_files():
    """
    Main function to process private fund data (Schedule D 7B1) from CSV files
    and insert it into SurrealDB.

    This function sets up logging, connects to SurrealDB, identifies relevant CSV files,
    calls the necessary functions to extract and insert the data, and filters the data
    to include only Venture Capital and Hedge Funds. It also sorts the data before
    insertion to improve matching.
    """
    logger = loggers.setup_logger("SurrealProcessD-5B1s")
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

        # Define regular expression patterns to identify relevant CSV files.
        
        file_pattern1 = re.compile(r"^IA_Schedule_D_7B1_.*\.csv$")
        file_pattern2 = re.compile(r"^ERA_Schedule_D_7B1_.*\.csv$")

        # Find all files in the directory that match either pattern.
        matching_files = [
            filename
            for filename in os.listdir(PART1_DIR)
            if file_pattern1.match(filename) or file_pattern2.match(filename)
        ]
        # Process the CSV files and insert data into SurrealDB.
        # The data is sorted by "Master Fund Name" and "Fund Name" to improve matching.
        SurrealDML.process_csv_files_and_extract(insert_data_into_surrealdb,FIELD_MAPPING,logger,connection,matching_files,
                                                 sort_by=["Master Fund Name","Fund Name"],filter_func=filter_vc_hedge) 

# --- Main execution block ---
if __name__ == "__main__":
    process_filing_7b1_data_files()
# --- End main execution block ---
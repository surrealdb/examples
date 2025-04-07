
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
args_loader = ArgsLoader("Input Glove embeddings model",db_params)
FIELD_MAPPING = [
    {"dataframe_field_name": "SEC#", "field_display_name": "SEC#", "surql_field_name": "section1.sec_number", "python_type": str},
    {"dataframe_field_name": "SEC Region", "field_display_name": "SEC Region", "surql_field_name": "section1.sec_region", "python_type": str},
    {"dataframe_field_name": "Organization CRD#", "field_display_name": "Organization CRD#", "surql_field_name": "section1.organization_crd", "python_type": int},
    {"dataframe_field_name": "Firm Type", "field_display_name": "Firm Type", "surql_field_name": "section1.firm_type", "python_type": str},
    {"dataframe_field_name": "CIK#", "field_display_name": "CIK#", "surql_field_name": "section1.cik", "python_type": int},
    {"dataframe_field_name": "Primary Business Name", "field_display_name": "Primary Business Name", "surql_field_name": "section1.primary_business_name", "python_type": str},
    {"dataframe_field_name": "Legal Name", "field_display_name": "Legal Name", "surql_field_name": "section1.legal_name", "python_type": str},
    {"dataframe_field_name": "Main Office Street Address 1", "field_display_name": "Main Office Street Address 1", "surql_field_name": "section1.main_office_street_address_1", "python_type": str},
    {"dataframe_field_name": "Main Office Street Address 2", "field_display_name": "Main Office Street Address 2", "surql_field_name": "section1.main_office_street_address_2", "python_type": str},
    {"dataframe_field_name": "Main Office City", "field_display_name": "Main Office City", "surql_field_name": "section1.main_office_city", "python_type": str},
    {"dataframe_field_name": "Main Office State", "field_display_name": "Main Office State", "surql_field_name": "section1.main_office_state", "python_type": str},
    {"dataframe_field_name": "Main Office Country", "field_display_name": "Main Office Country", "surql_field_name": "section1.main_office_country", "python_type": str},
    {"dataframe_field_name": "Main Office Postal Code", "field_display_name": "Main Office Postal Code", "surql_field_name": "section1.main_office_postal_code", "python_type": str},
    
    
    {"dataframe_field_name": "Chief Compliance Officer Name", "field_display_name": "Chief Compliance Officer Name", "surql_field_name": "section1.chief_compliance_officer_name", "python_type": str},
    {"dataframe_field_name": "Chief Compliance Officer Other Titles", "field_display_name": "Chief Compliance Officer Other Titles", "surql_field_name": "section1.chief_compliance_officer_other_titles", "python_type": str},
    {"dataframe_field_name": "Chief Compliance Officer E-mail", "field_display_name": "Chief Compliance Officer E-mail", "surql_field_name": "section1.chief_compliance_officer_e_mail", "python_type": str},
    
    {"dataframe_field_name": "Latest ADV Filing Date", "field_display_name": "Latest ADV Filing Date", "surql_field_name": "section1.latest_adv_filing_date", "python_type": datetime},
    {"dataframe_field_name": "Website Address", "field_display_name": "Website Address", "surql_field_name": "section1.website_address", "python_type": str},
    {"dataframe_field_name": "1O - If yes, approx. amount of assets", "field_display_name": "Approx. Amount of Assets", "surql_field_name": "section_5d.approx_amount_of_assets", "python_type": str},
    {"dataframe_field_name": "5D(a)(1)", "field_display_name": "Individuals (other than high net worth) - Number of Clients", "surql_field_name": "section_5d.individuals_other_than_high_net_worth_number_of_clients", "python_type": int},
    {"dataframe_field_name": "5D(a)(3)", "field_display_name": "Individuals (other than high net worth) - Regulatory Assets", "surql_field_name": "section_5d.individuals_other_than_high_net_worth_regulatory_assets", "python_type": float},
    {"dataframe_field_name": "5D(b)(1)", "field_display_name": "High net worth individuals - Number of Clients", "surql_field_name": "section_5d.high_net_worth_individuals_number_of_clients", "python_type": int},
    {"dataframe_field_name": "5D(b)(3)", "field_display_name": "High net worth individuals - Regulatory Assets", "surql_field_name": "section_5d.high_net_worth_individuals_regulatory_assets", "python_type": float},
    {"dataframe_field_name": "5D(c)(1)", "field_display_name": "Banking or thrift institutions - Number of Clients", "surql_field_name": "section_5d.banking_or_thrift_institutions_number_of_clients", "python_type": int},
    {"dataframe_field_name": "5D(c)(3)", "field_display_name": "Banking or thrift institutions - Regulatory Assets", "surql_field_name": "section_5d.banking_or_thrift_institutions_regulatory_assets", "python_type": float},
    {"dataframe_field_name": "5D(d)(1)", "field_display_name": "Investment companies - Number of Clients", "surql_field_name": "section_5d.investment_companies_number_of_clients", "python_type": int},
    {"dataframe_field_name": "5D(d)(3)", "field_display_name": "Investment companies - Regulatory Assets", "surql_field_name": "section_5d.investment_companies_regulatory_assets", "python_type": float},
    {"dataframe_field_name": "5D(e)(1)", "field_display_name": "Business development companies - Number of Clients", "surql_field_name": "section_5d.business_development_companies_number_of_clients", "python_type": int},
    {"dataframe_field_name": "5D(e)(3)", "field_display_name": "Business development companies - Regulatory Assets", "surql_field_name": "section_5d.business_development_companies_regulatory_assets", "python_type": float},
    {"dataframe_field_name": "5D(f)(1)", "field_display_name": "Pooled investment vehicles - Number of Clients", "surql_field_name": "section_5d.pooled_investment_vehicles_number_of_clients", "python_type": int},
    {"dataframe_field_name": "5D(f)(3)", "field_display_name": "Pooled investment vehicles - Regulatory Assets", "surql_field_name": "section_5d.pooled_investment_vehicles_regulatory_assets", "python_type": float},
    {"dataframe_field_name": "5D(g)(1)", "field_display_name": "Pension and profit sharing plans - Number of Clients", "surql_field_name": "section_5d.pension_and_profit_sharing_plans_number_of_clients", "python_type": int},
    {"dataframe_field_name": "5D(g)(3)", "field_display_name": "Pension and profit sharing plans - Regulatory Assets", "surql_field_name": "section_5d.pension_and_profit_sharing_plans_regulatory_assets", "python_type": float},
    {"dataframe_field_name": "5D(h)(1)", "field_display_name": "Charitable organizations - Number of Clients", "surql_field_name": "section_5d.charitable_organizations_number_of_clients", "python_type": int},
    {"dataframe_field_name": "5D(h)(3)", "field_display_name": "Charitable organizations - Regulatory Assets", "surql_field_name": "section_5d.charitable_organizations_regulatory_assets", "python_type": float},
    {"dataframe_field_name": "5D(i)(1)", "field_display_name": "State or municipal government entities - Number of Clients", "surql_field_name": "section_5d.state_or_municipal_government_entities_number_of_clients", "python_type": int},
    {"dataframe_field_name": "5D(i)(3)", "field_display_name": "State or municipal government entities - Regulatory Assets", "surql_field_name": "section_5d.state_or_municipal_government_entities_regulatory_assets", "python_type": float},
    {"dataframe_field_name": "5D(j)(1)", "field_display_name": "Other investment advisers - Number of Clients", "surql_field_name": "section_5d.other_investment_advisers_number_of_clients", "python_type": int},
    {"dataframe_field_name": "5D(j)(3)", "field_display_name": "Other investment advisers - Regulatory Assets", "surql_field_name": "section_5d.other_investment_advisers_regulatory_assets", "python_type": float},
    {"dataframe_field_name": "5D(k)(1)", "field_display_name": "Insurance companies - Number of Clients", "surql_field_name": "section_5d.insurance_companies_number_of_clients", "python_type": int},
    {"dataframe_field_name": "5D(k)(3)", "field_display_name": "Insurance companies - Regulatory Assets", "surql_field_name": "section_5d.insurance_companies_regulatory_assets", "python_type": float},
    {"dataframe_field_name": "5D(l)(1)", "field_display_name": "Sovereign wealth funds - Number of Clients", "surql_field_name": "section_5d.sovereign_wealth_funds_number_of_clients", "python_type": int},
    {"dataframe_field_name": "5D(l)(3)", "field_display_name": "Sovereign wealth funds - Regulatory Assets", "surql_field_name": "section_5d.sovereign_wealth_funds_regulatory_assets", "python_type": float},
    {"dataframe_field_name": "5D(m)(1)", "field_display_name": "Corporations or other businesses - Number of Clients", "surql_field_name": "section_5d.corporations_or_other_businesses_number_of_clients", "python_type": int},
    {"dataframe_field_name": "5D(m)(3)", "field_display_name": "Corporations or other businesses - Regulatory Assets", "surql_field_name": "section_5d.corporations_or_other_businesses_regulatory_assets", "python_type": float},
    {"dataframe_field_name": "5D(n)(1)", "field_display_name": "Other - Number of Clients", "surql_field_name": "section_5d.other_number_of_clients", "python_type": int},
    {"dataframe_field_name": "5D(n)(3)", "field_display_name": "Other - Regulatory Assets", "surql_field_name": "section_5d.other_regulatory_assets", "python_type": float},
    {"dataframe_field_name": "5D(n)(3) - Other", "field_display_name": "Other - Details", "surql_field_name": "section_5d.other_details", "python_type": str},
    {"dataframe_field_name": "5F(2)(a)", "field_display_name": "Discretionary Regulatory Assets", "surql_field_name": "section_5f.discretionary_regulatory_assets", "python_type": float},
    {"dataframe_field_name": "5F(2)(b)", "field_display_name": "Non-Discretionary Regulatory Assets", "surql_field_name": "section_5f.nondiscretionary_regulatory_assets", "python_type": float},
    {"dataframe_field_name": "5F(2)(c)", "field_display_name": "Total Regulatory Assets", "surql_field_name": "section_5f.total_regulatory_assets", "python_type": float},
    {"dataframe_field_name": "5F(2)(d)", "field_display_name": "Discretionary Accounts", "surql_field_name": "section_5f.discretionary_accounts", "python_type": int},
    {"dataframe_field_name": "5F(2)(e)", "field_display_name": "Non-Discretionary Accounts", "surql_field_name": "section_5f.nondiscretionary_accounts", "python_type": int},
    {"dataframe_field_name": "5F(2)(f)", "field_display_name": "Total Accounts", "surql_field_name": "section_5f.total_accounts", "python_type": int},
    {"dataframe_field_name": "5F(3)", "field_display_name": "Non-US Regulatory Assets", "surql_field_name": "section_5f.nonus_regulatory_assets", "python_type": float}
]

def insert_data_into_surrealdb(logger,connection:Surreal,data):
    """
    Inserts data into SurrealDB.

    Args:
        data: The data to be inserted.
    """
    insert_surql = """ 
    fn::firm_upsert(
        $name,
        $identifier,
        $firm_type,
        $legal_name,
        $city,
        $state,
        $country,
        $section1,
        $section_5d,
        $section_5f)
    """
    if ("section1" in data 
        and "primary_business_name" in data["section1"]
        and "sec_number" in data["section1"]
        and "firm_type" in data["section1"]):
        params = {
            "name": data["section1"]["primary_business_name"],
            "identifier": data["section1"]["sec_number"],
            "firm_type": data["section1"]["firm_type"],        
            "section1": data["section1"]
            }
        
        if "legal_name" in data["section1"]:
            params["legal_name"] = data["section1"]["legal_name"]
        if "main_office_city" in data["section1"]:
            params["city"] = data["section1"]["main_office_city"]
        if "main_office_state" in data["section1"]:
            params["state"] = data["section1"]["main_office_state"]
        if "main_office_country" in data["section1"]:
            params["country"] = data["section1"]["main_office_country"]
        if "section_5d" in data:
            params["section_5d"] = data["section_5d"]
        if "section_5f" in data:
            params["section_5f"] = data["section_5f"]

        try:
            SurrealParams.ParseResponseForErrors(connection.query_raw(
                insert_surql,params=params
            ))
        except Exception as e:
            logger.error(f"Error inserting data into SurrealDB: {data}: {e}")
            raise




def insert_dataframe_into_database(logger,connection:Surreal,df):
    """
    Extracts specified fields from a pandas DataFrame and returns an array of objects.

    Args:
        df: The pandas DataFrame.
        field_mapping: An array of objects, where each object has "field_display_name" and "dataframe_field_name".
    Returns:
        An array of objects, where each object contains the extracted field values.
    """
    if df is not None and not df.empty:
        for index, row in tqdm.tqdm(df.iterrows(), desc="Processing rows", total=len(df), unit="row",position=2):
            row_data = get_parsed_data_from_field_mapping(row, FIELD_MAPPING)
            insert_data_into_surrealdb(logger,connection,row_data)
            
def process_excel_file_and_extract(logger,connection:Surreal,filepath:str):
    """
    Processes an Excel file, extracts specified fields, and returns an array of objects.

    Args:
        filepath: The path to the Excel file.
        field_mapping: An array of objects, where each object has "field_display_name" and "dataframe_field_name".

    Returns:
        An array of objects, or None if an error occurs.
    """
    df = pd.read_excel(filepath)
    df = df.replace([np.nan], [None])
    insert_dataframe_into_database(logger,connection,df)
    



def process_adviser_firms():

    logger = loggers.setup_logger("SurrealProcessFirms")
    args_loader.LoadArgs() # Parse command-line arguments
    logger.info(args_loader.string_to_print())

    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info("Connected to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)

        logger.info(f"Processing adviser firms data in directory {INVESTMENT_ADVISER_FIRMS_DIR}")
        for filename in tqdm.tqdm(os.listdir(INVESTMENT_ADVISER_FIRMS_DIR), desc="Processing files", unit="file",position=1):
            if filename.endswith(".xlsx"):
                filepath = os.path.join(INVESTMENT_ADVISER_FIRMS_DIR, filename)
                process_excel_file_and_extract(logger,connection,filepath)
            
            

# --- Main execution block ---
if __name__ == "__main__":
    process_adviser_firms()
# --- End main execution block ---
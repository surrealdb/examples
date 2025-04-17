

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


def process_query():

    logger = loggers.setup_logger("SurrealProcessFilings")
    args_loader.LoadArgs() # Parse command-line arguments
    logger.info(args_loader.string_to_print())

    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info("Connected to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)

        logger.info(f"Processing part 1 adv base a firms data in directory {PART1_DIR}")
        query = """
SELECT in.name AS vendor,out.name AS customer, description,
out.chief_compliance_officer.full_name AS compliance_officer,
out.chief_compliance_officer.email AS compliance_officer_email,
out.section1.chief_compliance_officer_other_titles AS compliance_officer_title,
(IF out.section_5f.total_regulatory_assets IS NOT NONE THEN <float>out.section_5f.total_regulatory_assets ELSE NONE END) AS customer_assets
FROM
custodian_for WHERE in.name in [
'ADVISER COMPLIANCE ASSOCIATES, LLC','ACA TECHNOLOGY, LLC: ACA COMPLIANCE GROUP',
'SNOWFLAKE','CLEARWATER ANALYTICS, LLC','FORMIDIUM CORP.','ADVYZON - CLOUD','MY COMPLIANCE OFFICE TECHNOLOGIES','FACTSET',
'SS&C TECHNOLOGIES, LLC','COMPLY TECHNOLOGIES, INC.','ACA COMPLIANCEALPHA','IQEQ US INC.','MYCOMPLIANCEOFFICE LTD.',
'ACA TECHNOLOGY, LLC','THE ABACUS GROUP, LLC','CARTA, INC','SNOWFLAKE INC.','MARIADV SKYSQL']
;
"""

        results = connection.query(query)

        df = pd.DataFrame(results)

        df.to_csv(BASE_OUTPUT_DIR +  'vendors.csv', index=False)

            
            

# --- Main execution block ---
if __name__ == "__main__":
    process_query()
# --- End main execution block ---
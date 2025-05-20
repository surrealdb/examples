
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
WIP - Initial analysis of firm types.  This block is a multi-line
string, which is okay, but a triple-quoted string is usually used
for multi-line strings.  I've left it as is.

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


def process_hedges(connection: Surreal):
    """
    Processes hedge fund related data (WIP).

    This function is intended to process data related to hedge funds,
    but it's currently a placeholder.  It includes a SurrealQL query
    that is commented out.

    Args:
        connection: The SurrealDB connection object.
    """
    logger = loggers.setup_logger("Process Hedge Funds") #Added Logger
    top_hedge_surql = """

        LET $hedge_deals = SELECT in.name AS in, math::sum(assets_under_management) AS assets_under_management FROM custodian_for WHERE in.firm_type = firm_type:⟨Hedge Fund⟩ OR out.firm_type = firm_type:⟨Hedge Fund⟩
            GROUP BY in;
        LET $total_hedge_deals = $hedge_deals.len();
        RETURN $total_hedge_deals;

        SELECT * FROM $hedge_deals ORDER BY assets_under_management DESC LIMIT  <int>($total_hedge_deals/10);
    """
    try:
        # SurrealParams.ParseResponseForErrors(connection.query_raw(top_hedge_surql)) # commented out
        pass
    except Exception as e:
        logger.error(f"Error processing hedges: {e}")
        raise # re-raise the error so that it is caught in process_firm_consolidation
    return



def process_vcs(connection: Surreal):
    """
    Processes venture capital fund related data (WIP).

    This function is intended to process data related to venture capital funds,
    but it's currently a placeholder.

    Args:
        connection: The SurrealDB connection object.
    """
    logger = loggers.setup_logger("Process Venture Capital") #Added Logger
    try:
        pass
    except Exception as e:
        logger.error(f"Error processing VCs: {e}")
        raise  # re-raise the error
    return


def process_books_records_holders(connection: Surreal):
    """
    Processes books and records holders data (WIP).

    This function is intended to process data related to books and records holders,
    but it's currently a placeholder.

    Args:
        connection: The SurrealDB connection object.
    """
    logger = loggers.setup_logger("Process Book and Record Holders") #Added Logger

    try:
        pass
    except Exception as e:
        logger.error(f"Error processing book/record holders: {e}")
        raise # re-raise the error
    return


def dedupe_out_registered(connection: Surreal):
    """
    Deduplicates registered firms (WIP).

    This function is intended to deduplicate registered firms, but it's
    currently a placeholder.

    Args:
        connection: The SurrealDB connection object.
    """
    logger = loggers.setup_logger("Dedupe Registered Firms") #Added Logger
    try:
        pass
    except Exception as e:
        logger.error(f"Error deduplicating registered firms: {e}")
        raise # re-raise the error
    return


def process_custodian_subisdiaries(connection: Surreal):
    """
    Processes custodian subsidiaries data (WIP).

    This function is intended to process data related to custodian subsidiaries,
    but it's currently a placeholder.

    Args:
        connection: The SurrealDB connection object.
    """
    logger = loggers.setup_logger("Process Custodian Subsidaries") #Added Logger
    try:
        pass
    except Exception as e:
        logger.error(f"Error processing custodian subsidiaries: {e}")
        raise # re-raise the error
    return



def process_firm_consolidation(): 
    """
    Consolidates firm data in SurrealDB.

    This function connects to SurrealDB, retrieves firm data, and consolidates
    firms based on name similarity and other criteria.  It's the main function
    for firm consolidation.
    """

    logger = loggers.setup_logger("SurrealProcessFirms")
    args_loader.LoadArgs() # Parse command-line arguments
    logger.info(args_loader.string_to_print())

    with Surreal(db_params.DB_PARAMS.url) as connection:
        logger.info("Connected to SurrealDB")
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)

        simple_firm_reductiuon_surql = """
            LET $mean_reg_assets = (SELECT VALUE mean FROM
            (SELECT math::mean(section_5f.total_regulatory_assets) AS mean FROM firm WHERE section_5f.total_regulatory_assets IS NOT NONE GROUP ALL)[0])[0];
            RETURN $mean_reg_assets;

            LET $reduced_names = 
            SELECT id,
            name_clean,name,section_5f.total_regulatory_assets,section_5f.total_regulatory_assets> 10*$mean_reg_assets as _t,
            IF name_clean.words().len()>0 THEN
                IF name_clean.words()[0].len() > 5 THEN 
                    name_clean.words()[0]
                ELSE
                    IF section_5f.total_regulatory_assets > 10*$mean_reg_assets THEN
                        (name_clean.words()[0..2] ?? name_clean.words()[0..1]).join(' ')
                    ELSE
                        (name_clean.words()[0..2] ?? ['OTHER']).join(' ')
                    END
                END
            //ELSE ' __OTHER' END

            as _n FROM firm ORDER BY _n;

            FOR $parent_name in 
            $reduced_names._n.group()
            {
                IF $parent_name IS NOT NONE{
                UPSERT type::thing("parent_firm",$parent_name)  CONTENT{
                    name:$parent_name
                }
                };
            };


            FOR $firm in $reduced_names{
                UPDATE type::record($firm.id) SET parent_firm = type::thing("parent_firm",$firm._n); 
            };
            """

        # process_hedges(connection)
        # process_vcs(connection)
        # process_books_records_holders(connection)
        # dedupe_out_registered(connection)
        # process_custodian_subisdiaries(connection)
        try:
            # Execute the SurrealQL query with the constructed parameters.
            # 'SurrealParams.ParseResponseForErrors' is assumed to be a helper function
            # to handle potential errors in the SurrealDB response.
            SurrealParams.ParseResponseForErrors(
                connection.query_raw(simple_firm_reductiuon_surql)
            )
        except Exception as e:
            # Log and raise an exception if there's an error during insertion.
            logger.error(f"Error inserting data into SurrealDB: {e}")
            raise

            

# --- Main execution block ---
if __name__ == "__main__":
    process_firm_consolidation()
# --- End main execution block ---
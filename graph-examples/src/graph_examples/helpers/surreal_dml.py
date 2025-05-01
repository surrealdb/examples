from surrealdb import Surreal
from graph_examples.helpers.constants import *
import tqdm
import numpy as np


class SurrealDML():
    """
    This class contains SurrealQL Data Manipulation Language (DML) queries.

    These queries are used to interact with the SurrealDB database for data insertion,
    retrieval, and manipulation.
    """
        
    @staticmethod
    def insert_dataframe_into_database(insert_data_function,field_mapping,logger,connection:Surreal,df):
        """
        Iterates through rows of a pandas DataFrame and inserts data into SurrealDB.

        Args:
            insert_data_function: A function that handles the insertion of a single row into SurrealDB.
                                 It should accept a logger, a SurrealDB connection, and a dictionary of row data.
            field_mapping: A list of dictionaries defining how DataFrame columns map to SurrealDB fields.
                           Each dictionary should have keys like 'dataframe_field_name' and 'surql_field_name'.
            logger: A logger object for logging progress and errors.
            connection: A SurrealDB connection object.
            df: The pandas DataFrame containing the data to be inserted.
        """
        if df is not None and not df.empty:
            for index, row in tqdm.tqdm(df.iterrows(), desc="Processing rows", total=len(df), unit="row"):
                row_data = get_parsed_data_from_field_mapping(row, field_mapping)
                insert_data_function(logger,connection,row_data)


    
    @staticmethod
    def process_csv_files_and_extract(insert_data_function,field_mapping,logger,connection:Surreal,filenames:list[str],                    
                                      filter_func = None,
                                      sort_by=None,key=None,ascending=True):
       
        """
        Processes multiple CSV files, optionally filters and sorts the combined data,
        and then inserts it into SurrealDB.

        Args:
            insert_data_function: A function that handles the insertion of a single row into SurrealDB.
                                 It should accept a logger, a SurrealDB connection, and a dictionary of row data.
            field_mapping: A list of dictionaries defining how DataFrame columns map to SurrealDB fields.
                           Each dictionary should have keys like 'dataframe_field_name' and 'surql_field_name'.
            logger: A logger object for logging information and errors.
            connection: A SurrealDB connection object.
            filenames: A list of CSV filenames to process.
            filter_func: An optional function to filter the combined DataFrame.
                         It should accept a pandas DataFrame and return a filtered DataFrame.
            sort_by:   An optional column name to sort the combined DataFrame by.
            key:       An optional function to use for sorting (e.g., to sort by string length).
            ascending: An optional boolean indicating whether to sort in ascending order (default is True).
        """


        concat_df = extract_csv_data(
                logger,filenames,filter_func,sort_by,key,ascending
        )
        if concat_df is not None:
            SurrealDML.insert_dataframe_into_database(insert_data_function,field_mapping,logger,connection,concat_df)



        






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

        dfs: list[pd.DataFrame] = []  # List to store individual dataframes


        pbar = tqdm.tqdm(filenames, desc="Processing files", unit="file")

        for filename in pbar:

            filepath = os.path.join(PART1_DIR, filename)
            pbar.set_postfix(file=filename)  # Update progress bar with current file name

            encoding_hint = get_file_encoding(filepath)  # Get the encoding hint
            # Prioritize latin1/ISO-8859-1
            encodings_to_try = ['iso-8859-1', encoding_hint]  # Try iso-8859-1 first

            df = None
            for enc in encodings_to_try:
                try:
                    df = pd.read_csv(filepath, encoding=enc, encoding_errors='replace')  # Use errors='replace'
                    #if enc != encoding_hint:
                    #    logger.warning(f"Successfully read {filepath} using {enc} instead of {encoding_hint}.")
                    break  # If successful, stop trying other encodings
                except UnicodeDecodeError:
                    logger.warning(f"UnicodeDecodeError for {filepath} with {enc}.")
                except Exception as e:
                    logger.error(f"An unexpected error occurred while processing {filepath}: {e}")
                    break  # Stop trying if a different error occurs
                
            if df is not None:
                dfs.append(df)


        if dfs:
            concat_df = pd.concat(dfs, ignore_index=True)  # Concatenate all dataframes

            if concat_df is not None:
                if filter_func:
                    concat_df = filter_func(concat_df)


                if sort_by:
                    if key:
                        concat_df = concat_df.sort_values(by=sort_by, key=key, ascending=ascending)
                    else:
                        concat_df = concat_df.sort_values(by=sort_by, ascending=ascending)

                concat_df = concat_df.replace([np.nan], [None])
                SurrealDML.insert_dataframe_into_database(insert_data_function,field_mapping,logger,connection,concat_df)

        else:
            logger.error("No valid dataframes to process. Skipping.")
            return  # Exit if no dataframes were loaded

        






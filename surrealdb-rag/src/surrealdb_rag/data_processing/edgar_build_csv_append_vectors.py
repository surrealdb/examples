"""Append vectors to the EDGAR CSV file."""



from surrealdb_rag.helpers import loggers
import surrealdb_rag.helpers.constants as constants
import pandas as pd
import datetime
import re
import os
import tqdm
from surrealdb_rag.helpers.constants import ArgsLoader
from surrealdb_rag.helpers.params import DatabaseParams, ModelParams, SurrealParams
from surrealdb_rag.data_processing.embeddings import WordEmbeddingModel
import csv

# Initialize database and model parameters, and argument loader
db_params = DatabaseParams()
model_params = ModelParams()
args_loader = ArgsLoader("Input wiki data",db_params,model_params)


def has_array_overlap(row, array_field_name, filter_array):
    """
    Checks if there's any overlap between the two arrays in a DataFrame row.

    Args:
        row (pd.Series): A row from a pandas DataFrame.
        array_field_name (str): The name of the column in the row containing an array.
        filter_array (list): The array to check for overlap against.

    Returns:
        bool: True if there's any overlap, False otherwise.
    """
    cell = row[array_field_name]
    if not cell:
        return False
    
    # Convert row tickers to a set for efficient intersection
    try:
        cell_set = set(cell)
        # Check for intersection between row tickers and filter tickers
        return bool(cell_set.intersection(filter_array))
    except Exception as e:
        return False



# Preprocess the text (example - adjust as needed)
def preprocess_text(text):
    """
    Preprocesses the input text by converting to lowercase, removing punctuation, and normalizing whitespace.

    Args:
        text (str): The text to preprocess.

    Returns:
        str: The preprocessed text.
    """
    token = str(text).lower()
    token = re.sub(r'[^\w\s]', '', token)  # Remove punctuation
    token = re.sub(r'\s+', ' ', token)  # Normalize whitespace (replace multiple spaces, tabs, newlines with a single space)
    token = token.strip() 
    return token

def generate_chunks(input_text:str, chunk_size:int)-> list[str]:
    """
    Tokenizes the input text into chunks of approximately chunk_size tokens.
    Uses whitespace tokenization for simplicity.

    Args:
        input_text (str): The string to be chunked.
        chunk_size (int): The desired number of tokens in each chunk.

    Returns:
        List[str]: A list of strings, where each string is a chunk of tokenized text.
    """

    tokens = input_text.split()  # Basic whitespace tokenization

    if not tokens:
        return []  # Return empty list if no tokens

    chunks = []
    current_chunk = []
    current_token_count = 0

    for token in tokens:
        if current_token_count + 1 <= chunk_size: # Check if adding the next token keeps chunk within size
            current_chunk.append(token)
            current_token_count += 1
        else:
            # Chunk is full, finalize it and start a new chunk
            chunks.append(" ".join(current_chunk)) # Detokenize chunk back to string (whitespace join)
            current_chunk = [token] # Start new chunk with the current token
            current_token_count = 1 # Reset token count for the new chunk

    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def create_csv_from_folder(logger,file_index_df: pd.DataFrame , output_file_path, chunk_size:int) -> None:
    """
    Creates a CSV file from a folder of text files, embedding the content using GloVe and FastText models.

    Args:
        logger (logging.Logger): The logger object for logging messages.
        file_index_df (pd.DataFrame): DataFrame containing file metadata.
        output_file_path (str): The path to save the output CSV.
        chunk_size (int): The size of chunks to break each file into.
    """


    logger.info(f"Loading Glove embedding model {constants.DEFAULT_GLOVE_PATH}")
    try:
        gloveEmbeddingModel = WordEmbeddingModel(constants.DEFAULT_GLOVE_PATH,False)
    except Exception as e:
        logger.error(f"Error opening embedding model. please check the model file was downloaded using download_glove_model {e}")

    logger.info(f"Loading custom FastText embedding model {constants.FS_EDGAR_PATH}")
    try:
        fastTextEmbeddingModel = WordEmbeddingModel(constants.FS_EDGAR_PATH,True)
    except Exception as e:
        logger.error(f"Error opening embedding model. train the model using train_fastText {e}")


    file_keys = {
        "url":"",
        "company_name":"",
        "cik":"",
        "form":"",
        "accession_no":"",
        "company.tickers":"",
        "company.exchanges":"",
        "company.description":"",
        "company.category":"",
        "company.industry":"",
        "company.sic":"",
        "company.website":"",
        "filing_date":"",
        "file_path":"",
        "chunk":"",
        "content":"",
        "content_glove_vector":"",
        "content_fasttext_vector":"",
        }.keys()
    

    with open(output_file_path,"w", newline='') as f:
        dict_writer = csv.DictWriter(f, file_keys)
        dict_writer.writeheader()

        for index, file in tqdm.tqdm(file_index_df.iterrows(), total=len(file_index_df), desc=f"Processing files"): 
            if file["file_path"] and os.path.exists(file["file_path"]):
                with open(file["file_path"]) as source:
                    file_contents = source.read()
                    chunks = generate_chunks(file_contents,chunk_size)
                    chunk_number = 0
                    
                    for chunk in chunks:
                        content = f"""
{file["company.tickers"]}
{file["company_name"]}
-------------
{chunk}
"""
                        content_glove_vector = gloveEmbeddingModel.sentence_to_vec(chunk)
                        content_fasttext_vector = fastTextEmbeddingModel.sentence_to_vec(chunk)
                        row = {
                            "url":f"{file["url"]}#chunk{chunk_number}",
                            "company_name":file["company_name"],
                            "cik":file["cik"],
                            "form":file["form"],
                            "accession_no":file["accession_no"],
                            "company.tickers":file["company.tickers"],
                            "company.exchanges":file["company.exchanges"],
                            "company.description":file["company.description"],
                            "company.industry":file["company.industry"],
                            "company.sic":file["company.sic"],
                            "company.category":file["company.category"],
                            "company.website":file["company.website"],
                            "filing_date":file["filing_date"],
                            "file_path":file["file_path"],
                            "chunk":chunk_number,
                            "content":content,
                            "content_glove_vector":content_glove_vector,
                            "content_fasttext_vector":content_fasttext_vector,
                            }
                        chunk_number += 1
                        dict_writer.writerow(row)
            else:
                logger.error(f"File not found: '{file["file_path"]}'")
    

    logger.info(f"CSV generation complete. Corpus saved to '{output_file_path}'.")



def generate_edgar_csv() -> None:
    """
    Generates a CSV file from EDGAR filing data, embedding the content using GloVe and FastText models.
    This function processes filings based on specified criteria like date range, tickers, exchanges, SIC codes, and forms.
    """
    
    ticker_str = ""
    exchange_str = ""
    sic_str = ""
    form_str = ""
    index_file = constants.DEFAULT_EDGAR_FOLDER_FILE_INDEX
    output_file = constants.DEFAULT_EDGAR_PATH
    backup_output_file = True


    chunk_size = constants.DEFAULT_CHUNK_SIZE

    start_date_str = ""
    end_date_str = ""
    
    

    args_loader.AddArg("start_date","edsd","start_date","Start filing date in format '%Y-%m-%d' for filtering. (default{0} blank string doesn't filter)",start_date_str)
    args_loader.AddArg("end_date","eded","end_date","End filing date in format '%Y-%m-%d' for filtering. (default{0} blank string doesn't filter)",end_date_str)
    args_loader.AddArg("index_file","if","index_file","The path to the file that stores the file list and meta data. (default{0})",index_file)
    args_loader.AddArg("chunk_size","cs","chunk_size","The size of chunks to break each file into. (default{0})",chunk_size)
    args_loader.AddArg("output_file","of","output_file","The path to the csv output. (default{0})",output_file)
    args_loader.AddArg("ticker","tic","ticker","Tickers to filter by can be an array in format 'AAPL,MSFT,AMZN' leave blank for all tickers. (default{0})",ticker_str)
    args_loader.AddArg("exchange","ex","exchange","Exchanges to filter by can be an array in format 'Nasdaq,NYSE,OTC' leave blank for all exchanges. (default{0})",ticker_str)
    args_loader.AddArg("sic","sic","sic","Industries to filter by can be an array in format '3674,1234,5432' (refer to https://www.sec.gov/search-filings/standard-industrial-classification-sic-code-list) leave blank for all industries. (default{0})",sic_str)
    args_loader.AddArg("form","edf","form","Form type to filter can be an array in format '10-K,10-Q,SC 13D,SC 13G,S-1,S-4'. (default{0})",form_str)
    args_loader.AddArg("backup_output_file","buof","backup_output_file","If the ouptut file already exists backup or not with timestamp? If false program will exit if exists. (default{0})",backup_output_file)
    
    args_loader.LoadArgs()


    if args_loader.AdditionalArgs["form"]["value"]:
        form_str = args_loader.AdditionalArgs["form"]["value"]
        form = form_str.split(",")
    else:
        form = []

    if args_loader.AdditionalArgs["ticker"]["value"]:
        ticker_str = args_loader.AdditionalArgs["ticker"]["value"]
        ticker = ticker_str.split(",")
    else:
        ticker = []

    if args_loader.AdditionalArgs["exchange"]["value"]:
        exchange_str = args_loader.AdditionalArgs["exchange"]["value"]
        exchange = exchange_str.split(",")
    else:
        exchange = []


    if args_loader.AdditionalArgs["sic"]["value"]:
        sic_str = args_loader.AdditionalArgs["sic"]["value"]
        sic = sic_str.split(",")
    else:
        sic = []

    if args_loader.AdditionalArgs["index_file"]["value"]:
        index_file = args_loader.AdditionalArgs["index_file"]["value"]

    if args_loader.AdditionalArgs["output_file"]["value"]:
        output_file = args_loader.AdditionalArgs["output_file"]["value"]


    if args_loader.AdditionalArgs["backup_output_file"]["value"]:
        backup_output_file = str(args_loader.AdditionalArgs["backup_output_file"]["value"]).lower()in ("true","yes","1")



    if args_loader.AdditionalArgs["chunk_size"]["value"]:
        chunk_size = args_loader.AdditionalArgs["chunk_size"]["value"]


    logger = loggers.setup_logger("SurreaEdgarBuildCSV")

    logger.info(args_loader.string_to_print())


    logger.info(f"Loading EDGAR file index data to data frame '{index_file}'")

# row = {
#             "url":filing.filing_url,
#             "company_name":filing.company,
#             "cik":filing.cik,
#             "form":filing.form,
#             "accession_no":filing.accession_no,
#             "company.tickers":company.tickers,
#             "company.exchanges":company.exchanges,
#             "company.description":company.description,
#             "company.category":company.category,
#             "company.industry":company.industry,
#             "company.sic":company.sic,
#             "company.website":company.website,
#             "filing_date":filing.filing_date,
#             "file_path":file_path,
#         }

    file_index_df = pd.read_csv(index_file)

    if len(ticker) > 0:
        # Convert filter_tickers to a set for efficient lookup in the function
        filter_ticker_set = set(ticker)
        # 3. Apply the filtering function to each row
        file_index_df = file_index_df[file_index_df.apply(has_array_overlap, axis=1, args=("company.tickers",filter_ticker_set,))]

    if len(exchange) > 0:
        # Convert filter_tickers to a set for efficient lookup in the function
        filter_exchange_set = set(exchange)
        # 3. Apply the filtering function to each row
        file_index_df = file_index_df[file_index_df.apply(has_array_overlap, axis=1, args=("company.exchanges",filter_exchange_set,))]

    if len(form) > 0:
        file_index_df = file_index_df[file_index_df['form'].isin(form)]


    if len(sic) > 0:
        file_index_df = file_index_df[file_index_df['company.sic'].isin(sic)]

    file_index_df['filing_datetime'] = pd.to_datetime(file_index_df['filing_date'], errors='coerce')


    if args_loader.AdditionalArgs["start_date"]["value"]:
        start_date = datetime.datetime.strptime(args_loader.AdditionalArgs["start_date"]["value"], '%Y-%m-%d')
        file_index_df = file_index_df[file_index_df["filing_datetime"] >= start_date]
    
    if args_loader.AdditionalArgs["end_date"]["value"]:
        end_date = datetime.datetime.strptime(args_loader.AdditionalArgs["end_date"]["value"], '%Y-%m-%d')
        file_index_df = file_index_df[file_index_df["filing_datetime"] >= end_date]


    if backup_output_file and os.path.exists(output_file):
        backup_output_file_path = output_file.replace(".csv",f"_backup_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
        logger.info(f"Backing up index file to {backup_output_file_path}")
        os.rename(output_file,backup_output_file_path)
    else:
        if os.path.exists(output_file):
            logger.info(f"File already exists... skipping (delete it if you want to regenerate or set buif to true): '{output_file}'.")
            return

    create_csv_from_folder(logger,file_index_df,output_file,chunk_size)




if __name__ == "__main__":
    generate_edgar_csv()
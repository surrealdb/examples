"""Train a fasttext with the wiki data """



from surrealdb_rag import loggers
import surrealdb_rag.constants as constants
import pandas as pd
import fasttext
import re
import os
import tqdm
from surrealdb_rag.constants import DatabaseParams, ModelParams, ArgsLoader, SurrealParams
from surrealdb_rag.embeddings import WordEmbeddingModel
import csv

# Initialize database and model parameters, and argument loader
db_params = DatabaseParams()
model_params = ModelParams()
args_loader = ArgsLoader("Input wiki data",db_params,model_params)

TARGET_TOKEN_COUNT = 5000

# Preprocess the text (example - adjust as needed)
def preprocess_text(text):
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


def create_csv_from_folder(logger,file_index_df: pd.DataFrame , output_file_path):
    

    if os.path.exists(output_file_path):
        logger.info(f"File already exists... skipping (delete it if you want to regenerate): '{output_file_path}'.")
        return

    logger.info(f"Loading Glove embedding model {constants.GLOVE_PATH}")
    try:
        gloveEmbeddingModel = WordEmbeddingModel(constants.GLOVE_PATH,False)
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
        "company.ticker_display":"",
        "company.description":"",
        "company.category":"",
        "company.industry":"",
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
            if file["url"] != "error" and os.path.exists(file["file_path"]):
                with open(file["file_path"]) as source:
                    file_contents = source.read()
                    chunks = generate_chunks(file_contents,TARGET_TOKEN_COUNT)
                    chunk_number = 0
                    
                    for chunk in chunks:
                        content = f"""
company_name:{file["company_name"]}
ticker:{file["company.ticker_display"]}
form:{file["form"]}
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
                            "company.ticker_display":file["company.ticker_display"],
                            "company.description":file["company.description"],
                            "company.industry":file["company.industry"],
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

    logger.info(f"CSV generation complete. Corpus saved to '{output_file_path}'.")



def generate_edgar_csv() -> None:
    # Add command-line argument for embedding models
    args_loader.LoadArgs()
    logger = loggers.setup_logger("SurrealWikiInsert")

    logger.info(args_loader.string_to_print())


    logger.info(f"Loading EDGAR file index data to data frame '{constants.EDGAR_FOLDER_FILE_INDEX}'")
    file_index_df = pd.read_csv(constants.EDGAR_FOLDER_FILE_INDEX)

    create_csv_from_folder(logger,file_index_df,constants.EDGAR_PATH)


    # traning_data_file = constants.FS_EDGAR_PATH + "_train.txt"
    # model_bin_file = constants.FS_EDGAR_PATH + ".bin"
    # model_txt_file = constants.FS_EDGAR_PATH
    # logger.info(f"Concatenating corpus '{traning_data_file}'.")
    # concatenate_text_files_in_folder(logger,constants.EDGAR_FOLDER,traning_data_file)
    # logger.info(f"Training model.")
    # train_model(logger,traning_data_file,model_bin_file,model_txt_file)



if __name__ == "__main__":
    generate_edgar_csv()
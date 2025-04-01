"""Train a fasttext with the wiki data """


import fasttext

from surrealdb_rag.helpers import loggers
import surrealdb_rag.helpers.constants as constants
import fasttext
import os
import tqdm

from surrealdb_rag.data_processing.embeddings import WordEmbeddingModel

def concatenate_text_files_in_folder(logger,folder_path, output_file_path):
    """
    Concatenates the text content of all text files in a folder into a single output file.
    Avoids loading all files into memory at once and ensures UTF-8 encoding for output.

    Args:
        logger (logging.Logger): Logger for logging information and errors.
        folder_path (str): Path to the folder containing text files (e.g., constants.EDGAR_FOLDER).
        output_file_path (str, optional): Path to the output corpus file. Defaults to "corpus.txt".
    """
    if os.path.exists(output_file_path):
        logger.info(f"File already exists... skipping (delete it if you want to regenerate): '{output_file_path}'.")
        return
    
    if not os.path.isdir(folder_path):
        logger.info(f"Error: Folder '{folder_path}' does not exist: '{folder_path}'")
        return

    text_files = [f for f in os.listdir(folder_path)]
    if not text_files:
        logger.info(f"Warning: No files found in folder: '{folder_path}'.")
        return



    logger.info(f"Concatenating text files from folder: '{folder_path}'...")

    try:
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            for filename in tqdm.tqdm(text_files, desc="Concatenating corpus"):
                input_file_path = os.path.join(folder_path, filename)
                try:
                    with open(input_file_path, 'r') as infile:
                        for line in infile:
                            outfile.write(line)
                except Exception as e:
                    logger.info(f"Error reading file '{filename}': {e}")
    except Exception as e_output:
        logger.info(f"Error opening or writing to output file '{output_file_path}': {e_output}")
        return

    logger.info(f"Concatenation complete. Corpus saved to '{output_file_path}' (UTF-8 encoded).")


def train_model(logger,traning_data_file, model_bin_file):

    """
    Trains a FastText unsupervised model on the given training data.

    If the model already exists, it loads the existing model. Otherwise, it trains a new
    skipgram model and saves it. The training data file is then removed.

    Args:
        logger (logging.Logger): Logger for logging information and errors.
        traning_data_file (str): Path to the training data file.
        model_bin_file (str): Path to save the trained model (.bin file).

    Returns:
        fasttext.FastText._FastText: The trained FastText model.
    """
    if os.path.exists(model_bin_file):
        logger.info(f"Model already exists delete if you want to regenerate '{model_bin_file}'")
        return fasttext.load_model(model_bin_file)
    else:
        logger.info("Training model")
        model = fasttext.train_unsupervised(traning_data_file, model='skipgram')
        model.save_model(model_bin_file) 
        os.remove(traning_data_file)
        return model
    
def write_model_to_text_file(logger,model,model_txt_file):

    """
    Writes the trained FastText model vectors to a text file.

    This function extracts word vectors from the FastText model and saves them in a text
    format, suitable for use with other embedding libraries.

    Args:
        logger (logging.Logger): Logger for logging information.
        model (fasttext.FastText._FastText): The trained FastText model.
        model_txt_file (str): Path to save the model in text format.
    """


    logger.info(f"Writing model to {model_txt_file}")
    model_dim = model.get_dimension()
    with open(model_txt_file, "w") as f:
        words = model.words
        for word in tqdm.tqdm(words, desc=f"Writing model to {model_txt_file}"):
            vector = model.get_word_vector(word)
            # Clean the token
            word = WordEmbeddingModel.process_token_text_for_txt_file(word)
            #ensure its not an empty string
            if word and len(vector) == model_dim:
                vector_str = " ".join([str(v) for v in vector]) # More robust conversion to string
                f.write(f"{word} {vector_str}\n") 
    

def edgar_train_fastText() -> None:
    """
    Trains a FastText model on EDGAR data and saves it in both binary and text formats.

    This function orchestrates the training process:
    1.  Sets up logging.
    2.  Defines file paths for training data and models.
    3.  Concatenates text files from the EDGAR folder into a training corpus.
    4.  Trains the FastText model.
    5.  Writes the model vectors to a text file.
    """
    
    logger = loggers.setup_logger("Train FastText Embedding Model") 



    traning_data_file = constants.FS_EDGAR_PATH + "_train.txt"
    model_bin_file = constants.FS_EDGAR_PATH + ".bin"
    model_txt_file = constants.FS_EDGAR_PATH
    logger.info(f"Concatenating corpus '{traning_data_file}'.")
    concatenate_text_files_in_folder(logger,constants.EDGAR_FOLDER,traning_data_file)
    model = train_model(logger,traning_data_file,model_bin_file)
    write_model_to_text_file(logger,model,model_txt_file)



if __name__ == "__main__":
    edgar_train_fastText()
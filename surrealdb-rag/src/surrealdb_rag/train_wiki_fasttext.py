"""Train a fasttext with the wiki data """


import fasttext

from surrealdb_rag import loggers
import surrealdb_rag.constants as constants
import pandas as pd
import fasttext
import re
import os

# Preprocess the text (example - adjust as needed)
def preprocess_text(text):
    token = str(text).lower()
    token = re.sub(r'[^\w\s]', '', token)  # Remove punctuation
    token = re.sub(r'\s+', ' ', token)  # Normalize whitespace (replace multiple spaces, tabs, newlines with a single space)
    token = token.strip() 
    return token


def train_wiki_fastText() -> None:
    logger = loggers.setup_logger("Train FastText Embedding Model") 

    usecols=[
        "title",
        "text"
    ]


    logger.info(f"Loading Wiki data {constants.WIKI_PATH} to data frame")
    wiki_records_df = pd.read_csv(constants.WIKI_PATH,usecols=usecols)

    # Combine relevant columns
    wiki_records_df['combined_text'] = 'title:' + wiki_records_df['title'] + '\ntext:\n' + wiki_records_df['text']
    all_text = wiki_records_df['combined_text'].apply(preprocess_text)

    logger.info(all_text.head())
    logger.info(all_text.describe())
    logger.info(len(all_text))

    traning_data_file = constants.FS_WIKI_PATH + "_train.txt"
    model_bin_file = constants.FS_WIKI_PATH + ".bin"
    model_txt_file = constants.FS_WIKI_PATH
    # Save the combined text to a file
    with open(traning_data_file, "w") as f:
        for text in all_text:
            f.write(text + "\n")

    # # Train the FastText model
    model = fasttext.train_unsupervised(traning_data_file, model='skipgram')
    model.save_model(model_bin_file) 
    model_dim = model.get_dimension()

    print("Model dimension:", model_dim)

    with open(model_txt_file, "w") as f:
        words = model.words
        for word in words:
            #ensure its not an empty string
            word = preprocess_text(word)  # Clean the token
            if word:
                vector = model.get_word_vector(word)
                if(len(vector) == model_dim):
                    vector_str = " ".join([str(v) for v in vector]) # More robust conversion to string
                    f.write(f"{word} {vector_str}\n") 
    os.remove(traning_data_file)
    



if __name__ == "__main__":
    train_wiki_fastText()
"""Train a fasttext with the wiki data """


import fasttext

from surrealdb_rag import loggers
import surrealdb_rag.constants as constants
import pandas as pd
import fasttext
import os
import tqdm

from surrealdb_rag.embeddings import WordEmbeddingModel


def wiki_train_fastText() -> None:
    logger = loggers.setup_logger("Train FastText Embedding Model") 

    usecols=[
        "title",
        "text"
    ]


    logger.info(f"Loading Wiki data {constants.DEFAULT_WIKI_PATH} to data frame")
    wiki_records_df = pd.read_csv(constants.DEFAULT_WIKI_PATH,usecols=usecols)

    # Combine relevant columns
    wiki_records_df['combined_text'] = 'title:' + wiki_records_df['title'] + '\ntext:\n' + wiki_records_df['text']
    #all_text = wiki_records_df['combined_text'].apply(WordEmbeddingModel.process_token_text_for_txt_file)
    all_text = wiki_records_df['combined_text']

    logger.info(all_text.head())
    logger.info(all_text.describe())
    logger.info(len(all_text))

    traning_data_file = constants.DEFAULT_FS_WIKI_PATH + "_train.txt"
    model_bin_file = constants.DEFAULT_FS_WIKI_PATH + ".bin"
    model_txt_file = constants.DEFAULT_FS_WIKI_PATH
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
        for word in tqdm.tqdm(words, desc=f"Writing model to {model_txt_file}"):
            vector = model.get_word_vector(word)
            # Clean the token
            word = WordEmbeddingModel.process_token_text_for_txt_file(word)
            #ensure its not an empty string
            if word and len(vector) == model_dim:
                vector_str = " ".join([str(v) for v in vector]) # More robust conversion to string
                f.write(f"{word} {vector_str}\n") 

                
    os.remove(traning_data_file)
    



if __name__ == "__main__":
    wiki_train_fastText()
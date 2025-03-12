
import subprocess


def run_process(command: list):
    subprocess.run(command, check=True)
    print(f"Successfully executed command: \n{command}")

# python ./src/surrealdb_rag/create_database.py
def create_database():
    run_process(["python", "./src/surrealdb_rag/create_database.py"])


# python ./src/surrealdb_rag/download_glove.py
def download_glove():
    run_process(["python", "./src/surrealdb_rag/download_glove.py"])


# python ./src/surrealdb_rag/insert_embedding_model.py -emtr GLOVE -emv "6b 300d" -emp data/glove.6B.300d.txt -des "Wikipedia 2014 + Gigaword 5 (6B tokens, 400K vocab, uncased) https://nlp.stanford.edu/projects/glove/" -cor "Wikipedia 2014 + Gigaword 5 (6B tokens, 400K vocab, uncased)"
def insert_glove(): # Alias definition IN this file
    """Runs the embedding model insertion for GLOVE."""
    command = [
        "python",
        "./src/surrealdb_rag/insert_embedding_model.py", # Path to THIS script
        "-emtr",
        "GLOVE",
        "-emv",
        "6b 300d",
        "-emp",
        "data/glove.6B.300d.txt",
        "-des",
        "Wikipedia 2014 + Gigaword 5 (6B tokens, 400K vocab, uncased) https://nlp.stanford.edu/projects/glove/", # NO quotes needed here
        "-cor",
        "Wikipedia 2014 + Gigaword 5 (6B tokens, 400K vocab, uncased)", # NO quotes needed here
    ]
    run_process(command)


# python ./src/surrealdb_rag/download_wiki_data.py
def download_wiki():
    run_process(["python", "./src/surrealdb_rag/download_wiki_data.py"])

# python ./src/surrealdb_rag/wiki_train_fasttext.py
def train_wiki():
    run_process(["python", "./src/surrealdb_rag/wiki_train_fasttext.py"])


# python ./src/surrealdb_rag/insert_embedding_model.py -emtr FASTTEXT -emv "wiki" -emp data/custom_fast_wiki_text.txt -des "Custom trained model using fasttext based on OPENAI wiki example download" -cor "https://cdn.openai.com/API/examples/data/vector_database_wikipedia_articles_embedded.zip"
def insert_wiki_fs(): # Alias definition IN this file
    """Runs the embedding model insertion for GLOVE."""
    command = [
        "python",
        "./src/surrealdb_rag/insert_embedding_model.py", # Path to THIS script
        "-emtr",
        "FASTTEXT",
        "-emv",
        "wiki",
        "-emp",
        "data/custom_fast_wiki_text.txt",
        "-des",
        "Custom trained model using fasttext based on OPENAI wiki example download", # NO quotes needed
        "-cor",
        "https://cdn.openai.com/API/examples/data/vector_database_wikipedia_articles_embedded.zip", # NO quotes needed
    ]
    run_process(command)


# python ./src/surrealdb_rag/wiki_append_vectors_to_csv.py
def add_vectors_to_wiki():
    run_process(["python", "./src/surrealdb_rag/wiki_append_vectors_to_csv.py"])

# python ./src/surrealdb_rag/insert_wiki.py -fsv "wiki" -ems GLOVE,FASTTEXT,OPENAI
def insert_wiki(): # Alias definition IN this file
    """Runs the embedding model insertion for GLOVE."""
    command = [
        "python",
        "./src/surrealdb_rag/insert_wiki.py", # Path to THIS script
        "-fsv",
        "wiki", # NO quotes needed
        "-ems",
        "GLOVE,FASTTEXT,OPENAI", # NO quotes needed
    ]
    run_process(command)


# python ./src/surrealdb_rag/download_edgar_data.py
def download_edgar():
    run_process(["python", "./src/surrealdb_rag/download_edgar_data.py"])

# python ./src/surrealdb_rag/edgar_train_fasttext.py
def train_edgar():
    run_process(["python", "./src/surrealdb_rag/download_edgar_data.py"])

# python ./src/surrealdb_rag/insert_embedding_model.py -emtr FASTTEXT -emv "EDGAR 10ks" -emp data/custom_fast_edgar_text.txt -des "Model trained on 10-K filings for 30 days prior to March 11 2025" -cor "10k filing data from https://www.sec.gov/edgar/search/"
def insert_edgar_fs(): # Alias definition IN this file
    """Runs the embedding model insertion for GLOVE."""
    command = [
        "python",
        "./src/surrealdb_rag/insert_embedding_model.py", # Path to THIS script
        "-emtr",
        "FASTTEXT",
        "-emv",
        "EDGAR 10ks",
        "-emp",
        "data/custom_fast_edgar_text.txt",
        "-des",
        "Model trained on 10-K filings", # NO quotes needed
        "-cor",
        "10k filing data from https://www.sec.gov/edgar/search/", # NO quotes needed
    ]
    run_process(command)


# python ./src/surrealdb_rag/edgar_build_csv_append_vectors.py
def add_vectors_to_edgar():
    run_process(["python", "./src/surrealdb_rag/edgar_build_csv_append_vectors.py"])


# python ./src/surrealdb_rag/insert_edgar.py -fsv "EDGAR 10ks" -ems GLOVE,FASTTEXT
def insert_edgar(): # Alias definition IN this file
    """Runs the embedding model insertion for EDGAR data."""
    command = [
        "python",
        "./src/surrealdb_rag/insert_edgar.py",  # Path to the script
        "-fsv",  # Flag for fast_text_version
        "EDGAR 10ks", # Value for fast_text_version (NO quotes needed)
        "-ems",  # Flag for embed_models
        "GLOVE,FASTTEXT", # Value for embed_models (NO quotes needed)
    ]
    run_process(command)


# python ./src/surrealdb_rag/insert_edgar.py -fsv "EDGAR 10ks" -ems GLOVE,FASTTEXT
def app(): # Alias definition IN this file
    """Runs UX for the app."""
    command = [
        "python",
        "./src/surrealdb_rag/app.py",  # Path to the script
    ]
    run_process(command)
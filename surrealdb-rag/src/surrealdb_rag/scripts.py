
import subprocess
import surrealdb_rag.constants as constants
import datetime


URL = ""

def run_process(command: list):
    subprocess.run(command, check=True)
    print(f"Successfully executed command: \n{command}")

# python ./src/surrealdb_rag/create_database.py
def create_database():
    run_process(["python", "./src/surrealdb_rag/create_database.py", 
        "-url",
        URL])


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
        "Wikipedia 2014 + Gigaword 5 (6B tokens, 400K vocab, uncased)", 
        "-url",
        URL
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
        "https://cdn.openai.com/API/examples/data/vector_database_wikipedia_articles_embedded.zip", 
        "-url",
        URL
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
        "GLOVE,FASTTEXT,OPENAI", 
        "-url",
        URL
    ]
    run_process(command)



def setup_wiki():
    create_database()
    download_glove()
    insert_glove()
    download_wiki()
    train_wiki()
    insert_wiki_fs()
    add_vectors_to_wiki()
    insert_wiki()


def setup_edgar():
    create_database()
    download_edgar()
    train_edgar()
    insert_edgar_fs()
    add_vectors_to_edgar()
    insert_edgar()







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
        "10k filing data from https://www.sec.gov/edgar/search/", 
        "-url",
        URL
    ]
    run_process(command)


# python ./src/surrealdb_rag/edgar_build_csv_append_vectors.py
def add_vectors_to_edgar():
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=7) 
    start_date_str = start_date.strftime('%Y-%m-%d')
    run_process(["python", "./src/surrealdb_rag/edgar_build_csv_append_vectors.py",
                 "-edsd",start_date_str,
                 "-edf","10-K,10-Q",])


# python ./src/surrealdb_rag/insert_edgar.py -fsv "EDGAR 10ks" -ems GLOVE,FASTTEXT
def insert_edgar(): # Alias definition IN this file
    """Runs the embedding model insertion for EDGAR data."""
    command = [
        "python",
        "./src/surrealdb_rag/insert_edgar.py",  # Path to the script
        "-fsv",  # Flag for fast_text_version
        "EDGAR 10ks", # Value for fast_text_version (NO quotes needed)
        "-ems",  # Flag for embed_models
        "GLOVE,FASTTEXT", # Value for embed_models (NO quotes needed),
        "-tn","embedded_edgar",
        "-dn","Latest SEC filings", 
        "-url", URL
    ]
    run_process(command)


AI_EDGAR_FILE = constants.DEFAULT_EDGAR_PATH.replace(".csv", "_ai.csv")
def add_vectors_to_ai_industry_edgar():
    ai_related_sic = [
        "3674",  # Semiconductors and Related Devices (e.g., Nvidia)
        "7371",  # Custom Computer Programming Services (AI algorithm development)
        "7372",  # Software Publishers (AI platforms, machine learning software, Database Management Software)
        "7379"   # Computer Systems Design Services (AI implementation, integration, consulting)
    ]
    run_process(["python", "./src/surrealdb_rag/edgar_build_csv_append_vectors.py",
                 "-sic", ",".join(ai_related_sic),
                 "-of", AI_EDGAR_FILE
                 ])

def insert_ai_industry_edgar():
    command = [
        "python",
        "./src/surrealdb_rag/insert_edgar.py",  # Path to the script
        "-fsv",  # Flag for fast_text_version
        "EDGAR 10ks", # Value for fast_text_version (NO quotes needed)
        "-ems",  # Flag for embed_models
        "GLOVE,FASTTEXT", # Value for embed_models (NO quotes needed),
        "-tn","embedded_edgar_ai",
        "-td","Latest AI filings",
        "-if", AI_EDGAR_FILE, 
        "-url",
        URL
    ]
    run_process(command)


def add_ai_edgar_data():
    add_vectors_to_ai_industry_edgar()
    insert_ai_industry_edgar()


LARGE_CHUNK_EDGAR_FILE = constants.DEFAULT_EDGAR_PATH.replace(".csv", "_lc.csv")
def add_vectors_to_large_chunk_edgar():
    run_process(["python", "./src/surrealdb_rag/edgar_build_csv_append_vectors.py"
                 "-of", LARGE_CHUNK_EDGAR_FILE,
                 "-cs", 1000
                 ])
    

def insert_large_chunk_edgar():
    command = [
        "python",
        "./src/surrealdb_rag/insert_edgar.py",  # Path to the script
        "-fsv",  # Flag for fast_text_version
        "EDGAR 10ks", # Value for fast_text_version (NO quotes needed)
        "-ems",  # Flag for embed_models
        "GLOVE,FASTTEXT", # Value for embed_models (NO quotes needed),
        "-tn","embedded_edgar_lc",
        "-td","Latest filings 1k token chunks",
        "-if", LARGE_CHUNK_EDGAR_FILE
    ]
    run_process(command)  


def add_large_chunk_edgar_data():
    add_vectors_to_large_chunk_edgar()
    insert_large_chunk_edgar()


# args_loader.AddArg("start_date","edsd","start_date","Start filing date in format '%Y-%m-%d' for filtering. (default{0} blank string doesn't filter)",start_date_str)
# args_loader.AddArg("end_date","eded","end_date","End filing date in format '%Y-%m-%d' for filtering. (default{0} blank string doesn't filter)",end_date_str)
# args_loader.AddArg("index_file","if","index_file","The path to the file that stores the file list and meta data. (default{0})",index_file)
# args_loader.AddArg("chunk_size","cs","chunk_size","The size of chunks to break each file into. (default{0})",chunk_size)
# args_loader.AddArg("output_file","of","output_file","The path to the csv output. (default{0})",output_file)
# args_loader.AddArg("ticker","tic","ticker","Tickers to filter by can be an array in format 'AAPL,MSFT,AMZN' leave blank for all tickers. (default{0})",ticker_str)
# args_loader.AddArg("exchange","ex","exchange","Exchanges to filter by can be an array in format 'Nasdaq,NYSE,OTC' leave blank for all exchanges. (default{0})",ticker_str)
# args_loader.AddArg("sic","sic","sic","Industries to filter by can be an array in format '3674,1234,5432' (refer to https://www.sec.gov/search-filings/standard-industrial-classification-sic-code-list) leave blank for all industries. (default{0})",sic_str)
    


# python ./src/surrealdb_rag/insert_edgar.py -fsv "EDGAR 10ks" -ems GLOVE,FASTTEXT
def app(): # Alias definition IN this file
    """Runs UX for the app."""
    command = [
        "python",
        "./src/surrealdb_rag/app.py",  # Path to the script
    ]
    run_process(command)
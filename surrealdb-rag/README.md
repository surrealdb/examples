# SurrealDB RAG Exploration: Knowledge Graphs, Advanced RAG, and Flexible Data Pipelines

Welcome to a comprehensive RAG (Retrieval Augmented Generation) experimentation platform built with SurrealDB! This project provides robust tools for building and evaluating RAG systems, with a focus on knowledge graph integration, flexible data pipelines, and granular control over LLM interactions. We leverage SurrealDB's speed and flexibility to combine large language models (LLMs) with rich data sources (Wikipedia, SEC Edgar filings) and structured knowledge extracted from them.

## Key Capabilities

* **Data Ingestion and Processing:** Import and process data from diverse sources (Wikipedia, SEC Edgar filings).
* **Knowledge Graph Extraction:** Extract structured knowledge (entities and relationships) from text.
* **Knowledge Graph-Augmented RAG:** Explore different strategies for incorporating knowledge graphs into RAG pipelines.
* **Embedding Model Flexibility:** Integrate and manage multiple embedding models (GloVe, FastText, OpenAI).
* **LLM Integration:** Support for both API-hosted and locally hosted LLMs, with configurable invocation methods.
* **Advanced RAG Techniques:** Fine-grained control over context management, prompt engineering, and response generation.
* **User Interface:** A dynamic UI for chat interactions, message inspection, and graph visualization.

The backend is built with FastAPI, the UI with Jinja2, and dynamic interactivity is achieved with htmx.

## Data Sources

* **Wikipedia (Simple English):** For broad knowledge retrieval. The data is downloaded from [OpenAI Wikipedia articles](https://cdn.openai.com/API/examples/data/vector_database_wikipedia_articles_embedded.zip).
* **SEC Edgar Filings:** Detailed financial and business data. Filings are retrieved from the official [SEC's EDGAR database](https://www.sec.gov/edgar/searchedgar/companysearch.html) using the [EDGAR tools library](https://github.com/dgunning/edgartools/)

## Knowledge Graph Features

* **Extraction:** An NLP pipeline extracts entities and relationships from text, forming knowledge graphs using the [spaCy library](https://spacy.io/).
* **Visualization:** The UI visualizes the extracted knowledge graphs and allows you to explore how the entities are related.

## Embedding Model Support

* **Supported Models:**
    * OpenAI's `text-embedding-ada-002`: A strong general-purpose model. [OpenAI Embeddings Documentation](https://platform.openai.com/docs/guides/embeddings)
    * GloVe (Global Vectors for Word Representation): A classic word embedding model. (Sentence embeddings are created by averaging word vectors). [GloVe Project Page](https://nlp.stanford.edu/projects/glove/)
    * FastText: Efficient word representations, particularly good with morphology [FastText Project Page](https://fasttext.cc/).
    * Integrate other models by modifying `surrealdb_rag/data_processing/embeddings.py`.
* **Configuration:** You can configure which embedding models are used for different corpus tables, allowing for tailored retrieval strategies.
* **Extensibility:** Easily integrate other embedding models.

##   LLM Integration

* **LLM Providers:**
    * **API-hosted:** ChatGPT, Gemini, etc. (API keys are required).
        * ChatGPT: [OpenAI Developer Quickstart](https://platform.openai.com/docs/quickstart)
        * Gemini: [Google AI Studio](https://ai.google.dev/)
    * **Locally hosted (Ollama):** Any LLM from `ollama pull`. [Ollama](https://ollama.ai/) and [Ollama Model Library](https://ollama.ai/library)
    * LLM calls can be made via API calls or HTTP requests within SurrealDB.
* **Control:**
    * Prompt engineering via the UI
    * Context management (chat history, chunk count)

##   User Interface

* Chat history management
* Detailed message inspection
* Knowledge graph visualization
* RAG parameter configuration

##   Setup

* **Hardware:** A modern machine with sufficient RAM is recommended, especially for local LLM execution and handling large embedding models. An Apple M2 Pro was used for development.
* **SurrealDB:** Version 2.2.x or later or [SurrealDB Cloud](https://surrealdb.com/cloud) is required. [SurrealDB Installation](https://surrealdb.com/install).
* **Python:** Version 3.11 is recommended. 
* **LLM API Keys:**
    * OpenAI: Required for using OpenAI's embedding and LLM models. Obtain one from the [OpenAI Developer Quickstart](https://platform.openai.com/docs/quickstart).
    * Google Gemini: Required if using Gemini. Obtain from [Google AI Studio](https://ai.google.dev/).
* **Environment Variables:**
    * Set these in your shell configuration (e.g., `.bashrc`, `.zshrc`) or use a `.env` file.
    ```
    SURREAL_RAG_USER=<SurrealDB username>
    SURREAL_RAG_PASS=<SurrealDB password>
    SURREAL_RAG_DB_URL=<SurrealDB connection URL> (e.g., ws://localhost:8000 or wss://xxx_cloud_id_xxx.surreal.cloud)
    SURREAL_RAG_DB_NS=<SurrealDB namespace> (e.g. RAG_NS)
    SURREAL_RAG_DB_DB=<SurrealDB namespace> (e.g. RAG_DB)

    OPENAI_API_KEY     # OpenAI API Key (if using ChatGPT)
    GOOGLE_GENAI_API_KEY # Google Gemini API Key (if using Gemini)
    ```
    * **Crucially:** Ensure your OpenAI and Gemini keys are also added to the `surrealdb_rag/schema/common_function_ddl.surql` file. This allows SurrealDB functions to access them when making external API calls.

##   Getting Started

1.  **Clone:**

    ```bash
    git clone [https://github.com/apireno/examples.git](https://github.com/apireno/examples.git)
    cd examples/surrealdb-rag
    ```

2.  **Install:**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ./
    ```

3.  **Run Scripts:**

    Execute scripts using the script names defined in `pyproject.toml` (under `[project.scripts]`). You no longer need to explicitly call `python3 surrealdb_rag/scripts.py`.

    **Important Notes:**

    * Replace `<SURREALDB_URL>`, `<START_DATE>`, `<END_DATE>`, `<FORM_TYPES>`, and `<TICKERS>` with your actual values.
    * Dates should be in the format `YYYY-MM-DD`.
    * Form types and tickers should be comma-separated lists (e.g., `"10-K,10-Q"`, `"AAPL,MSFT"`).

    Here are some examples of how to run the scripts.

    ###   Wikipedia Setup (End-to-End)


    ```bash
    create_db -url http://localhost:8000
    download_glove
    insert_glove -url http://localhost:8000 -emtr GLOVE -emv "6b 300d" -emp data/glove.6B.300d.txt -des "Wikipedia 2014 + Gigaword 5 (6B tokens, 400K vocab, uncased) [https://nlp.stanford.edu/projects/glove/](https://nlp.stanford.edu/projects/glove/)" -cor "Wikipedia 2014 + Gigaword 5 (6B tokens, 400K vocab, uncased)"
    download_wiki
    train_wiki
    insert_wiki_fs
    add_wiki_vectors
    insert_wiki -fsv "wiki" -ems GLOVE,FASTTEXT,OPENAI -url http://localhost:8000
    ```

    Or Just run the script which will call the commands above in order

    ```bash
        setup_wiki
    ```


    ###   Edgar Data Setup (End-to-End)

    ```bash
    create_db -url http://localhost:8000
    download_edgar -edsd 2025-01-01 -edf "10-K,10-Q"
    train_edgar
    insert_edgar_fs -url http://localhost:8000
    add_edgar_vectors -edsd 2025-01-01 -edf "10-K,10-Q" 
    insert_edgar -fsv "EDGAR Data" -ems GLOVE,FASTTEXT -tn embedded_edgar -dn "Latest SEC filings" -url http://localhost:8000 -il False
    ```

    Or Just run the script which will call the commands above in order

    ```bash
        setup_edgar
    ```

    You can also incrimentally add new data to the EDGAR data source 

    ```bash
        download_edgar -edsd <some date as of last load> -edf "10-K,10-Q"
        add_edgar_vectors -edsd <some date as of last load>
        insert_edgar -fsv "EDGAR Data" -ems GLOVE,FASTTEXT -tn embedded_edgar -dn "Latest SEC filings" -url http://localhost:8000 -il True
    ```

    Running the following will incrementally load data from 5 days prior

    ```bash
        incriment_latest_edgar
    ```



    ###   Edgar Graph Setup (End-to-End) 


    ```bash
        #First run the setup for edgar data processing
        edgar_graph_extraction
        insert_edgar_graph -il False -edsd 2025-01-01
    ```

    Or Just run the script which will call the commands above in order

    ```bash
        #First run the setup for edgar data processing
        setup_edgar_graph
    ```

    You can also incrimentally add new data to the EDGAR graph data source 

    ```bash
        download_edgar -edsd <some date as of last load> -edf "10-K,10-Q" -url http://localhost:8000
        insert_edgar_graph -il True -edsd <some date as of last load>
    ```

    Running the following will incrementally load data from 5 days prior

    ```bash
        incriment_latest_edgar_graph
    ```




    ###   Other samples scripts to be found:
    * add_ai_edgar: Creates an Edgar data set limited to certain industries
    * add_large_edgar: Creates an Edgar data set with a large chunking strategy

    ###   Script Details with Arguments

    * **`create_db`:**
        * Creates the SurrealDB database and schema.
        * Arguments:
            * `-url` or `--url`: The URL of the SurrealDB instance.
            * `-u` or `--username`: The database username.
            * `-p` or `--password`: The database password.
            * `-ns` or `--namespace`: The SurrealDB namespace.
            * `-db` or `--database`: The SurrealDB database.
            * `-urlenv` or `--url_env`: The environment variable name for the SurrealDB URL.
            * `-uenv` or `--user_env`: The environment variable name for the database username.
            * `-penv` or `--pass_env`: The environment variable name for the database password.
            * `-nsenv` or `--namespace_env`: The environment variable name for the SurrealDB namespace.
            * `-dbenv` or `--database_env`: The environment variable name for the SurrealDB database.
    * **`download_glove`:**
        * Downloads the GloVe word embeddings.
        * Arguments: None
    * **`insert_glove`:**
        * Inserts GloVe embeddings into SurrealDB.
        * Arguments:
            * `-url` or `--url`: The URL of the SurrealDB instance.
            * `-u` or `--username`: The database username.
            * `-p` or `--password`: The database password.
            * `-ns` or `--namespace`: The SurrealDB namespace.
            * `-db` or `--database`: The SurrealDB database.
            * `-urlenv` or `--url_env`: The environment variable name for the SurrealDB URL.
            * `-uenv` or `--user_env`: The environment variable name for the database username.
            * `-penv` or `--pass_env`: The environment variable name for the database password.
            * `-nsenv` or `--namespace_env`: The environment variable name for the SurrealDB namespace.
            * `-dbenv` or `--database_env`: The environment variable name for the SurrealDB database.
            * `-emtr` or `--model_trainer`: The training algorithm ("GLOVE").
            * `-emv` or `--model_version`: The model version ("6b 300d").
            * `-emp` or `--model_path`: Path to the GloVe text file.
            * `-des` or `--description`: Description of the model.
            * `-cor` or `--corpus`: Description of the training corpus.
    * **`download_wiki`:**
        * Downloads the Wikipedia dataset from [OpenAI Wikipedia articles](https://cdn.openai.com/API/examples/data/vector_database_wikipedia_articles_embedded.zip).
        * Arguments: None
    * **`train_wiki`:**
        * Trains a FastText model on the Wikipedia dataset.
        * Arguments: None
    * **`insert_wiki_fs`:**
        * Inserts the FastText model for Wikipedia data.
        * Arguments:
            * `-url` or `--url`: The URL of the SurrealDB instance.
            * `-u` or `--username`: The database username.
            * `-p` or `--password`: The database password.
            * `-ns` or `--namespace`: The SurrealDB namespace.
            * `-db` or `--database`: The SurrealDB database.
            * `-urlenv` or `--url_env`: The environment variable name for the SurrealDB URL.
            * `-uenv` or `--user_env`: The environment variable name for the database username.
            * `-penv` or `--pass_env`: The environment variable name for the database password.
            * `-nsenv` or `--namespace_env`: The environment variable name for the SurrealDB namespace.
            * `-dbenv` or `--database_env`: The environment variable name for the SurrealDB database.
            * `-emtr` or `--model_trainer`: The training algorithm ("FASTTEXT").
            * `-emv` or `--model_version`: The model version ("wiki").
            * `-emp` or `--model_path`: Path to the FastText model text file.
            * `-des` or `--description`: Description of the model.
            * `-cor` or `--corpus`: Description of the training corpus.
    * **`add_vectors_to_wiki`:**
        * Calculates and appends GloVe and FastText vectors to the Wikipedia CSV.
        * Arguments: None
    * **`insert_wiki`:**
        * Inserts the Wikipedia data (including vectors) into SurrealDB.
        * Arguments:
            * `-url` or `--url`: The URL of the SurrealDB instance.
            * `-u` or `--username`: The database username.
            * `-p` or `--password`: The database password.
            * `-ns` or `--namespace`: The SurrealDB namespace.
            * `-db` or `--database`: The SurrealDB database.
            * `-urlenv` or `--url_env`: The environment variable name for the SurrealDB URL.
            * `-uenv` or `--user_env`: The environment variable name for the database username.
            * `-penv` or `--pass_env`: The environment variable name for the database password.
            * `-nsenv` or `--namespace_env`: The environment variable name for the SurrealDB namespace.
            * `-dbenv` or `--database_env`: The environment variable name for the SurrealDB database.
            * `-fsv` or `--fast_text_version`: The FastText model version ("wiki").
            * `-ems` or `--embed_models`: Comma-separated list of embedding models ("GLOVE,FASTTEXT,OPENAI").
    * **`setup_wiki`:**
        * Runs the complete Wikipedia data pipeline.
        * Arguments:
            * `-url` or `--url`: The URL of the SurrealDB instance.
            * `-u` or `--username`: The database username.
            * `-p` or `--password`: The database password.
            * `-ns` or `--namespace`: The SurrealDB namespace.
            * `-db` or `--database`: The SurrealDB database.
            * `-urlenv` or `--url_env`: The environment variable name for the SurrealDB URL.
            * `-uenv` or `--user_env`: The environment variable name for the database username.
            * `-penv` or `--pass_env`: The environment variable name for the database password.
            * `-nsenv` or `--namespace_env`: The environment variable name for the SurrealDB namespace.
            * `-dbenv` or `--database_env`: The environment variable name for the SurrealDB database.
    * **`download_edgar`:**
        * Downloads SEC Edgar filings from the official [SEC's EDGAR database](https://www.sec.gov/edgar/searchedgar/companysearch.html).
        * Arguments:
            * `-url` or `--url`: The URL of the SurrealDB instance.
            * `-u` or `--username`: The database username.
            * `-p` or `--password`: The database password.
            * `-ns` or `--namespace`: The SurrealDB namespace.
            * `-db` or `--database`: The SurrealDB database.
            * `-urlenv` or `--url_env`: The environment variable name for the SurrealDB URL.
            * `-uenv` or `--user_env`: The environment variable name for the database username.
            * `-penv` or `--pass_env`: The environment variable name for the database password.
            * `-nsenv` or `--namespace_env`: The environment variable name for the SurrealDB namespace.
            * `-dbenv` or `--database_env`: The environment variable name for the SurrealDB database.
            * `-edsd` or `--start_date`: Start date for filing retrieval (YYYY-MM-DD).
            * `-eded` or `--end_date`: End date for filing retrieval (YYYY-MM-DD).
            * `-edf` or `--form`: Comma-separated list of form types (e.g., "10-K,10-Q").
            * `-tic` or `--ticker`: Comma-separated list of ticker symbols (e.g., "AAPL,MSFT").
    * **`train_edgar`:**
        * Trains a FastText model on the Edgar filings.
        * Arguments:
            * `-url` or `--url`: The URL of the SurrealDB instance.
            * `-u` or `--username`: The database username.
            * `-p` or `--password`: The database password.
            * `-ns` or `--namespace`: The SurrealDB namespace.
            * `-db` or `--database`: The SurrealDB database.
            * `-urlenv` or `--url_env`: The environment variable name for the SurrealDB URL.
            * `-uenv` or `--user_env`: The environment variable name for the database username.
            * `-penv` or `--pass_env`: The environment variable name for the database password.
            * `-nsenv` or `--namespace_env`: The environment variable name for the SurrealDB namespace.
            * `-dbenv` or `--database_env`: The environment variable name for the SurrealDB database.
    * **`insert_edgar_fs`:**
        * Inserts the FastText model for Edgar data.
        * Arguments:
            * `-url` or `--url`: The URL of the SurrealDB instance.
            * `-u` or `--username`: The database username.
            * `-p` or `--password`: The database password.
            * `-ns` or `--namespace`: The SurrealDB namespace.
            * `-db` or `--database`: The SurrealDB database.
            * `-urlenv` or `--url_env`: The environment variable name for the SurrealDB URL.
            * `-uenv` or `--user_env`: The environment variable name for the database username.
            * `-penv` or `--pass_env`: The environment variable name for the database password.
            * `-nsenv` or `--namespace_env`: The environment variable name for the SurrealDB namespace.
            * `-dbenv` or `--database_env`: The environment variable name for the SurrealDB database.
            * `-emtr` or `--model_trainer`: The training algorithm ("FASTTEXT").
            * `-emv` or `--model_version`: The model version ("EDGAR Data").
            * `-emp` or `--model_path`: Path to the FastText model text file.
            * `-des` or `--description`: Description of the model.
            * `-cor` or `--corpus`: Description of the training corpus.
    * **`add_vectors_to_edgar`:**
        * Calculates and appends GloVe and FastText vectors to the Edgar CSV.
        * Arguments:
            * `-url` or `--url`: The URL of the SurrealDB instance.
            * `-u` or `--username`: The database username.
            * `-p` or `--password`: The database password.
            * `-ns` or `--namespace`: The SurrealDB namespace.
            * `-db` or `--database`: The SurrealDB database.
            * `-urlenv` or `--url_env`: The environment variable name for the SurrealDB URL.
            * `-uenv` or `--user_env`: The environment variable name for the database username.
            * `-penv` or `--pass_env`: The environment variable name for the database password.
            * `-nsenv` or `--namespace_env`: The environment variable name for the SurrealDB namespace.
            * `-dbenv` or `--database_env`: The environment variable name for the SurrealDB database.
            * `-edsd` or `--start_date`: Start date for filtering filings (YYYY-MM-DD).
            * `-edf` or `--form`: Comma-separated list of form types (e.g., "10-K,10-Q").
    * **`insert_edgar`:**
        * Inserts the Edgar data (including vectors) into SurrealDB.
        * Arguments:
            * `-url` or `--url`: The URL of the SurrealDB instance.
            * `-u` or `--username`: The database username.
            * `-p` or `--password`: The database password.
            * `-ns` or `--namespace`: The SurrealDB namespace.
            * `-db` or `--database`: The SurrealDB database.
            * `-urlenv` or `--url_env`: The environment variable name for the SurrealDB URL.
            * `-uenv` or `--user_env`: The environment variable name for the database username.
            * `-penv` or `--pass_env`: The environment variable name for the database password.
            * `-nsenv` or `--namespace_env`: The environment variable name for the SurrealDB namespace.
            * `-dbenv` or `--database_env`: The environment variable name for the SurrealDB database.
            * `-fsv` or `--fast_text_version`: The FastText model version ("EDGAR Data").
            * `-ems` or `--embed_models`: Comma-separated list of embedding models ("GLOVE,FASTTEXT").
            * `-tn` or `--table_name`: Name of the SurrealDB table.
            * `-dn` or `--display_name`: Display name for the data.
            * `-il` or `--incrimental_load`: Boolean flag for incremental load (True/False).
    * **`edgar_graph_extraction`:**
        * Extracts knowledge graphs from the processed Edgar filings.
        * Arguments:
            * `-url` or `--url`: The URL of the SurrealDB instance.
            * `-u` or `--username`: The database username.
            * `-p` or `--password`: The database password.
            * `-ns` or `--namespace`: The SurrealDB namespace.
            * `-db` or `--database`: The SurrealDB database.
            * `-urlenv` or `--url_env`: The environment variable name for the SurrealDB URL.
            * `-uenv` or `--user_env`: The environment variable name for the database username.
            * `-penv` or `--pass_env`: The environment variable name for the database password.
            * `-nsenv` or `--namespace_env`: The environment variable name for the SurrealDB namespace.
            * `-dbenv` or `--database_env`: The environment variable name for the SurrealDB database.
    * **`insert_edgar_graph`:**
        * Inserts the extracted knowledge graphs into SurrealDB.
        * Arguments:
            * `-url` or `--url`: The URL of the SurrealDB instance.
            * `-u` or `--username`: The database username.
            * `-p` or `--password`: The database password.
            * `-ns` or `--namespace`: The SurrealDB namespace.
            * `-db` or `--database`: The SurrealDB database.
            * `-urlenv` or `--url_env`: The environment variable name for the SurrealDB URL.
            * `-uenv` or `--user_env`: The environment variable name for the database username.
            * `-penv` or `--pass_env`: The environment variable name for the database password.
            * `-nsenv` or `--namespace_env`: The environment variable name for the SurrealDB namespace.
            * `-dbenv` or `--database_env`: The environment variable name for the SurrealDB database.
            * `-edsd` or `--start_date`: Start date for filtering filings (YYYY-MM-DD).
            * `-tn` or `--table_name`: Name of the SurrealDB table.
            * `-il` or `--incrimental_load`: Boolean flag for incremental load (True/False).
    * **`setup_edgar`:**
        * Runs the complete Edgar data pipeline.
        * Arguments:
            * `-url` or `--url`: The URL of the SurrealDB instance.
            * `-u` or `--username`: The database username.
            * `-p` or `--password`: The database password.
            * `-ns` or `--namespace`: The SurrealDB namespace.
            * `-db` or `--database`: The SurrealDB database.
            * `-urlenv` or `--url_env`: The environment variable name for the SurrealDB URL.
            * `-uenv` or `--user_env`: The environment variable name for the database username.
            * `-penv` or `--pass_env`: The environment variable name for the database password.
            * `-nsenv` or `--namespace_env`: The environment variable name for the SurrealDB namespace.
            * `-dbenv` or `--database_env`: The environment variable name for the SurrealDB database.
    * **`incriment_latest_edgar_graph`:**
        * Downloads and inserts the latest Edgar data and its knowledge graph.
        * Arguments:
            * `-url` or `--url`: The URL of the SurrealDB instance.
            * `-u` or `--username`: The database username.
            * `-p` or `--password`: The database password.
            * `-ns` or `--namespace`: The SurrealDB namespace.
            * `-db` or `--database`: The SurrealDB database.
            * `-urlenv` or `--url_env`: The environment variable name for the SurrealDB URL.
            * `-uenv` or `--user_env`: The environment variable name for the database username.
            * `-penv` or `--pass_env`: The environment variable name for the database password.
            * `-nsenv` or `--namespace_env`: The environment variable name for the SurrealDB namespace.
            * `-dbenv` or `--database_env`: The environment variable name for the SurrealDB database.
    * **`app`:**
        * Starts the FastAPI application.
        * Arguments:
            * `-url` or `--url`: The URL of the SurrealDB instance.
            * `-u` or `--username`: The database username.
            * `-p` or `--password`: The database password.
            * `-ns` or `--namespace`: The SurrealDB namespace.
            * `-db` or `--database`: The SurrealDB database.
            * `-urlenv` or `--url_env`: The environment variable name for the SurrealDB URL.
            * `-uenv` or `--user_env`: The environment variable name for the database username.
            * `-penv` or `--pass_env`: The environment variable name for the database password.
            * `-nsenv` or `--namespace_env`: The environment variable name for the SurrealDB namespace.
            * `-dbenv` or `--database_env`: The environment variable name for the SurrealDB database.

##   Key Libraries

This project leverages several powerful libraries to achieve its functionality:

* **FastAPI:** A modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints.
* **Jinja2:** A fast, expressive, and extensible templating engine. HTML, XML or other markup formats can be generated via templates.
* **htmx:** Allows you to access AJAX, CSS Transitions, WebSockets and Server Sent Events directly in HTML, using attributes.
* **SurrealDB:** A multi-model database system that supports SQL, graph queries, and real-time collaboration. [SurrealDB Installation](https://surrealdb.com/install)
* **edgar:** A Python library to interact with the SEC EDGAR database.
* **Transformers:** Provides general-purpose architectures for Natural Language Understanding (NLU) and Natural Language Generation (NLG).
* **SpaCy:** A library for advanced Natural Language Processing in Python.
* **FuzzyWuzzy:** A library for string matching and fuzzy string comparison.
* **python-Levenshtein:** A Python extension for fast computation of the Levenshtein distance and string similarity.
* **Ollama:** A tool for running Language Models locally. [Ollama](https://ollama.ai/) and [Ollama Model Library](https://ollama.ai/library)
* **google.generativeai:** Google's library for interacting with their generative AI models (e.g., Gemini).
* **openai:** OpenAI's Python library for accessing their models and APIs.
* **wget:** A non-interactive network downloader.
* **pandas:** A fast, powerful, flexible and easy to use open source data analysis and manipulation tool, built on top of the Python programming language.
* **pandas-stubs:** Type hints for pandas.
* **python-multipart:** A parser for multipart/form-data content in Python.

##   UI Libraries

* **Lightpick:** A lightweight, customizable date range picker. [https://wakirin.github.io/Lightpick/](https://wakirin.github.io/Lightpick/)
* **VivaGraphJS:** A graph drawing library. [https://github.com/anvaka/VivaGraphJS/](https://github.com/anvaka/VivaGraphJS/)


##   Acknowledgments

This project builds upon and extends the original work by [Ce11an](https://github.com/Ce11an). Thanks for the initial inspiration and codebase!
# SurrealDB RAG Exploration: Wikipedia, SEC Filings, and Beyond!

Welcome to a hands-on exploration of Retrieval Augmented Generation (RAG) using SurrealDB! This project is designed to be a playground where you can experiment with different aspects of RAG, combining the power of large language models (LLMs) with the flexibility and speed of SurrealDB's vector database capabilities. We'll start with a foundation of Wikipedia articles and SEC Edgar filings, and show you how to customize everything from the corpus to the LLM.

## What's the Big Idea?

This project is all about understanding and experimenting with RAG. We'll import datasets (Wikipedia articles and SEC filings), create vector embeddings using various models, and then build a simple RAG-powered question-answering system. You'll be able to see firsthand how different choices affect the quality and relevance of the results.

We use a FastAPI server for the backend, Jinja2 for templating, and htmx to create a dynamic chat interface.

Also, this project shows how you can completely eliminate *external* API calls by hosting everything locally and in-database, while still having the flexibility to call external APIs when desired.

## Key Features & Experimentation

This project isn't just a demo; it's a toolkit for RAG experimentation. Here's what you can tweak and explore:

*   **Different Corpuses:** We've included examples for:
    *   **Wikipedia (Simple English):** A broad knowledge base, great for general questions.
    *   **SEC Edgar Filings (10-K, 10-Q, etc.):** Focus on financial and business information.
        *   Download filings using the `download_edgar` command, with optional arguments to specify the types of forms (e.g., 10-K, 10-Q), ticker symbols, and date ranges. See the `scripts.py` file and the `surrealdb_rag.edgar.download_edgar_data` function for details on the arguments you can use. We use the `edgartools` library ([https://github.com/dgunning/edgartools/tree/ffe18c511c9e29616fc6a000699e01c06d48586a](https://github.com/dgunning/edgartools/tree/ffe18c511c9e29616fc6a000699e01c06d48586a)) to interact with the SEC EDGAR database.

*   **Embedding Models:** Experiment with:
    *   **OpenAI's `text-embedding-ada-002`:** A powerful, general-purpose embedding model. [OpenAI Embeddings Documentation](https://platform.openai.com/docs/guides/embeddings)
    *   **GloVe (Global Vectors for Word Representation):** A classic word embedding model. See how it compares to a more modern approach. (Note: GloVe is primarily for word embeddings; sentence embeddings are created by averaging word vectors). [GloVe Project Page](https://nlp.stanford.edu/projects/glove/)
    *   Any other embedding model that can take in some text and return a vector. You can modify the `surrealdb_rag/embeddings.py` file to integrate other embedding models.

*   **LLM Models:**
    *   **API-hosted models like ChatGPT and Gemini:** Easily call these models via API requests. You'll need API keys (see Setup). For ChatGPT, see [OpenAI Developer Quickstart](https://platform.openai.com/docs/quickstart). For Gemini, see [Google AI Studio](https://ai.google.dev/).
    *   **Locally hosted LLMs via Ollama:** Any LLM you install with `ollama pull` should work. See [Ollama](https://ollama.ai/) for installation and [Ollama Model Library](https://ollama.ai/library) for a list of available models and instructions on how to pull them. This allows for completely offline operation.
    *   **Call API LLMs via API calls or via HTTP calls within the database:** 
    *   **(Future - Currently in Development)** Call locally hosted LLM models directly within the database (without external network requests).

*   **RAG Parameters:**
    *   **Chat History:** Control the number of included previous conversation to see how it affects the context and coherence of responses.
    *   **Number of Chunks:** Adjust how many relevant text chunks are included in the prompt sent to the LLM. More chunks provide more context but can also introduce noise.

*   **Prompt Engineering:** Modify the prompt sent to the LLM to fine-tune the style and content of the responses. Experiment with different instructions and see how the LLM's behavior changes.  The prompt can be adjusted in the web UI, and there are a few pre-canned prompts to choose from.
## Setup and Requirements

*   **Hardware:** While an Apple M2 Pro was used for initial development, the project should run on any reasonably modern machine with sufficient RAM (especially for loading embeddings).
*   **SurrealDB:** Running on the SurrealDB Cloud will limit you to Local and API-only LLM calls without an enterprise license. Version 2.2.x or later is required for local runs. [SurrealDB Installation](https://surrealdb.com/install).
*   **Python:** Version 3.11 is used. `pyenv` is recommended for managing Python versions. [pyenv GitHub](https://github.com/pyenv/pyenv)
*   **OpenAI API Key:** Required for using OpenAI's embedding and LLM models. Obtain one from the [OpenAI Developer Quickstart](https://platform.openai.com/docs/quickstart).
*   **Google Gemini API Key:** Required if using Gemini. Obtain from [Google AI Studio](https://ai.google.dev/).

## Getting Started

1.  **Clone the Repository:**

    ```bash
    git clone [https://github.com/surrealdb/examples.git](https://github.com/surrealdb/examples.git)
    cd examples/surrealdb-rag
    ```

2.  **Install Dependencies:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Set up your Environment Variables:**

    The following environment variables are used:

    ```
    SURREAL_RAG_USER  # SurrealDB username
    SURREAL_RAG_PASS  # SurrealDB password
    SURREAL_RAG_DB_URL # SurrealDB connection URL (e.g., http://localhost:8000)
    SURREAL_RAG_DB_NS  # SurrealDB namespace
    SURREAL_RAG_DB_DB  # SurrealDB database

    OPENAI_API_KEY     # Your OpenAI API Key
    GOOGLE_GENAI_API_KEY # Your Google Gemini API Key (if using Gemini)
    ```
    You can set these in your shell's configuration file (e.g., `.bashrc`, `.zshrc`), or you can create a `.env` file in the project root and use a library like `python-dotenv` (though this is not explicitly included in this project to keep dependencies minimal). *Crucially, ensure your OpenAI and Gemini keys are also added to `surrealdb_rag/db/queries/chats.surql` as described in the original README, for use within SurrealQL functions.*

4.  **Running the Scripts**

    The `scripts.py` file contains all the commands to manage data, the database, and the application. Run them using:

    ```bash
    python3 surrealdb_rag/scripts.py <command_name>
    ```

    Here's a breakdown of the available commands, in a recommended order of execution for different scenarios:

    **Database Setup (Run these first):**

    *   `create_db`: Starts SurrealDB and sets up the necessary tables, indexes, and functions. This *must* be run before inserting any data.

    **Wikipedia Data:**

    *   `download_glove`: Downloads the GloVe word embeddings.
    *   `insert_glove`: Inserts the GloVe embeddings into SurrealDB.
    *   `download_wiki`: Downloads the Simple English Wikipedia dataset.
    *   `train_wiki`: Processes the Wikipedia dataset and generates OpenAI embeddings.
    *   `insert_wiki_fs`: **(Deprecated)** Inserts the raw Wikipedia data (without vectors) using the filesystem loader. Less efficient than `insert_wiki`.
    *   `add_wiki_vectors`: Adds OpenAI vector embeddings to existing Wikipedia data (if you used `insert_wiki_fs`).
    *   `insert_wiki`: Inserts the Wikipedia data *with* OpenAI embeddings directly into SurrealDB.
    *   `setup_wiki`: A convenience command that runs `download_glove`, `insert_glove`, `download_wiki`, `train_wiki`, and `insert_wiki` in the correct order. This is the easiest way to get started with the Wikipedia data.

    **SEC Edgar Filings Data:**

    *   `download_edgar`: Downloads SEC Edgar filings. You can specify form types, tickers, and dates.
    *   `train_edgar`: Processes the Edgar filings and generates OpenAI embeddings.
    *   `insert_edgar_fs`: **(Deprecated)** Inserts the raw Edgar data (without vectors).
    *   `add_edgar_vectors`: Adds OpenAI vector embeddings to existing Edgar data.
    *   `insert_edgar`: Inserts the Edgar data *with* OpenAI embeddings.
    *   `setup_edgar`: A convenience command that runs `download_edgar`, `train_edgar`, and `insert_edgar`.
    *   `add_ai_edgar`: Downloads, processes, and inserts a smaller dataset of AI-related Edgar filings (faster for initial experimentation).
    *   `add_ai_edgar_vectors`: Adds vectors to the AI industry Edgar data.
    *   `insert_ai_edgar`: Inserts the AI industry Edgar filings *with* embeddings.
    *   `add_large_edgar`: Processes a larger Edgar dataset with *larger* chunk sizes.
    *   `add_large_edgar_vectors`: Adds vectors to the large-chunk Edgar data.
    *   `insert_large_edgar`: Inserts the large-chunk Edgar filings *with* embeddings.

    **Running the Application:**

    *   `app`: Starts the FastAPI application, which provides the chat interface.

## Shout-outs

This project builds upon and extends the original work by [Ce11an](https://github.com/Ce11an). Thanks for the initial inspiration and codebase!

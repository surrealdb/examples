# Simple RAG bot using Python, SurrealDB, Ollama and Streamlit 

<img width="800" height="1001" alt="simpleragbot" src="https://github.com/user-attachments/assets/43f74f7e-6205-40ea-99d2-0ba10bd22b20" />

## Setup

```bash
# sync uv virtual environment with dependencies
uv sync

# or manually add the dependencies
uv add surrealdb streamlit ollama python-dotenv
```

## Run

```bash
# Launch in a new window
streamlit run app.py 

# Launch silently
streamlit run app.py --server.headless true
```

## Context

You can use the `florgflorg.txt` as a sample text file to evaluate that the RAG bot works.

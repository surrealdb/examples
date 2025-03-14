




export OPENAI_API_KEY=xxxx
export GOOGLE_GENAI_API_KEY=xxxx

export SURREAL_RAG_USER=xxx
export SURREAL_RAG_PASS=xxx

#Encrypted surreal cloud
export SURREAL_RAG_DB_URL=wss://<instanceid>.aws-use1.surreal.cloud

#local hosted
export SURREAL_RAG_DB_URL=ws://<ip_address>:<port 8000 by default>

export SURREAL_RAG_DB_NS=rag_example
export SURREAL_RAG_DB_DB=rag_example

export EDGAR_IDENTITY="youremail@domain.com"





python ./src/surrealdb_rag/create_database.py



python ./src/surrealdb_rag/download_glove.py

python ./src/surrealdb_rag/insert_embedding_model.py -emtr GLOVE -emv "6b 300d" -emp data/glove.6B.300d.txt -des "Wikipedia 2014 + Gigaword 5 (6B tokens, 400K vocab, uncased) https://nlp.stanford.edu/projects/glove/" -cor "Wikipedia 2014 + Gigaword 5 (6B tokens, 400K vocab, uncased)"





python ./src/surrealdb_rag/download_wiki_data.py

python ./src/surrealdb_rag/wiki_train_fasttext.py

python ./src/surrealdb_rag/insert_embedding_model.py -emtr FASTTEXT -emv "wiki" -emp data/custom_fast_wiki_text.txt -des "Custom trained model using fasttext based on OPENAI wiki example download" -cor "https://cdn.openai.com/API/examples/data/vector_database_wikipedia_articles_embedded.zip"

python ./src/surrealdb_rag/wiki_append_vectors_to_csv.py

python ./src/surrealdb_rag/insert_wiki.py -fsv "wiki" -ems GLOVE,FASTTEXT,OPENAI





python ./src/surrealdb_rag/download_edgar_data.py

python ./src/surrealdb_rag/edgar_train_fasttext.py

python ./src/surrealdb_rag/insert_embedding_model.py -emtr FASTTEXT -emv "EDGAR 10ks" -emp data/custom_fast_edgar_text.txt -des "Model trained on 10-K filings for 30 days prior to March 11 2025" -cor "10k filing data from https://www.sec.gov/edgar/search/"

python ./src/surrealdb_rag/edgar_build_csv_append_vectors.py

python ./src/surrealdb_rag/insert_edgar.py -fsv "EDGAR 10ks" -ems GLOVE,FASTTEXT
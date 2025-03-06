"""Insert Wikipedia data into SurrealDB."""

import ast

import pandas as pd
from surrealdb import Surreal
import tqdm

from surrealdb_rag import loggers
import surrealdb_rag.constants as constants


from surrealdb_rag.constants import DatabaseParams, ModelParams, ArgsLoader, SurrealParams

db_params = DatabaseParams()
model_params = ModelParams()
args_loader = ArgsLoader("Input wiki data",db_params,model_params)
args_loader.LoadArgs()




INSERT_WIKI_RECORDS = """
    FOR $row IN $records {
        CREATE type::thing("embedded_wiki",$row.url)  CONTENT {
        url : $row.url,
        title: $row.title,
        text: $row.text,
        content_glove_vector: $row.content_glove_vector,
        content_openai_vector: $row.content_openai_vector,
        content_fasttext_vector: $row.content_fasttext_vector
        } RETURN NONE;
    };
"""

DELETE_WIKI_RECORDS = "DELETE embedded_wiki;"


CHUNK_SIZE = 50



def surreal_wiki_insert() -> None:
    """Main entrypoint to insert Wikipedia embeddings into SurrealDB."""
    logger = loggers.setup_logger("SurrealWikiInsert")

    logger.info(args_loader.string_to_print())

    
    logger.info(f"Loading file {constants.WIKI_PATH}")

    usecols=[
                        "url",
                        "title",
                        "text",
                        "content_vector",
                        "content_glove_vector",
                        "content_fasttext_vector"
                    ]

    wiki_records_df = pd.read_csv(constants.WIKI_PATH,usecols=usecols)
    
    
    total_rows = len(wiki_records_df)
    total_chunks = total_rows // CHUNK_SIZE + (
        1 if total_rows % CHUNK_SIZE else 0
    )   
    with Surreal(db_params.DB_PARAMS.url) as connection:
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)
        logger.info("Connected to SurrealDB")

        logger.info("Deleting any existing wiki rows from SurrealDB")
        #remove any data from the table
        SurrealParams.ParseResponseForErrors(connection.query_raw(DELETE_WIKI_RECORDS))

        logger.info("Inserting rows into SurrealDB")
        with tqdm.tqdm(total=total_chunks, desc="Inserting") as pbar:
            for i in range(0, total_rows, CHUNK_SIZE):
                chunk = wiki_records_df.iloc[i:i + CHUNK_SIZE]
                formatted_rows = [
                        {
                            "url":str(row["url"]),
                            "title":str(row["title"]),
                            "text":str(row["text"]),
                            "content_openai_vector":ast.literal_eval(row["content_vector"]),
                            "content_glove_vector":ast.literal_eval(row["content_glove_vector"]),
                            "content_fasttext_vector":ast.literal_eval(row["content_fasttext_vector"])
                        }
                        for _, row in chunk.iterrows()
                    ]
                try:
                    SurrealParams.ParseResponseForErrors(connection.query_raw(
                        INSERT_WIKI_RECORDS, params={"records": formatted_rows}
                    ))
                except Exception as e:
                    print (formatted_rows)
                    return
                
                pbar.update(1)



if __name__ == "__main__":
    surreal_wiki_insert()
"""Insert Wikipedia data into SurrealDB."""

import ast

import pandas as pd
from surrealdb import Surreal
import tqdm

from surrealdb_rag import loggers
import surrealdb_rag.constants as constants


from surrealdb_rag.constants import DatabaseParams, ModelParams, ArgsLoader, SurrealParams

# Initialize database and model parameters, and argument loader
db_params = DatabaseParams()
model_params = ModelParams()
args_loader = ArgsLoader("Input wiki data",db_params,model_params)

# Define table name and display name
TABLE_NAME = "embedded_wiki"
DISPLAY_NAME = "Wikipedia"

# SurrealQL query to get embedding model definitions
GET_EMBED_MODEL_DESCRIPTIONS = """
    SELECT * FROM embedding_model_definition;
"""


# Mapping of embedding models to their field names and definitions
EMBED_MODEL_DEFINITIONS = {
    "GLOVE":{"field_name":"content_glove_vector","model_definition":[
        'GLOVE',
        '6b 300d'
        ]},
    "OPENAI":{"field_name":"content_openai_vector","model_definition":[
        'OPENAI',
        'text-embedding-ada-002'
        ]},
    "FASTTEXT":{"field_name":"content_fasttext_vector","model_definition":[
        'FASTTEXT',
        'wiki'
        ]},
}




# SurrealQL query to update corpus table information    
UPDATE_CORPUS_TABLE_INFO = f"""
    DELETE FROM corpus_table_model WHERE corpus_table = corpus_table:{TABLE_NAME};
    FOR $model IN $embed_models {{
        LET $model_definition = type::thing("embedding_model_definition",$model.model_id);
        UPSERT corpus_table_model:[corpus_table:{TABLE_NAME},$model_definition] SET model = $model_definition,field_name = $model.field_name, corpus_table=corpus_table:{TABLE_NAME};
    }};
    UPSERT corpus_table:{TABLE_NAME} SET table_name = '{TABLE_NAME}', display_name = '{DISPLAY_NAME}', 
        embed_models = (SELECT value id FROM corpus_table_model WHERE corpus_table = corpus_table:{TABLE_NAME}) RETURN NONE;
        
"""


# SurrealQL query to insert Wikipedia records
INSERT_WIKI_RECORDS = f"""
    FOR $row IN $records {{
        CREATE type::thing("{TABLE_NAME}",$row.url)  CONTENT {{
            url : $row.url,
            title: $row.title,
            text: $row.text,
            content_glove_vector: $row.content_glove_vector,
            content_openai_vector: $row.content_openai_vector,
            content_fasttext_vector: $row.content_fasttext_vector
        }} RETURN NONE;
    }};
"""

# SurrealQL query to delete all Wikipedia records
DELETE_WIKI_RECORDS = f"DELETE {TABLE_NAME};"


# Chunk size for batch processing
CHUNK_SIZE = 50



"""Main entrypoint to insert Wikipedia embeddings into SurrealDB."""
def surreal_wiki_insert() -> None:
    # Add command-line argument for embedding models
    args_loader.AddArg(
        "embed_models",
        "ems",
        "embed_models",
        "The Embed models you'd like to calculate sepearated by , can be GLOVE,FASTTEXT,OPENAI eg -ems OPENAI,GLOVE will calculate both OPENAI and GLOVE. (default{})",
        "GLOVE,FASTTEXT,OPENAI"
    )
    # Parse command-line arguments
    args_loader.LoadArgs()

    logger = loggers.setup_logger("SurrealWikiInsert")

    logger.info(args_loader.string_to_print())

    # Retrieve embedding models from arguments
    embed_models_str = args_loader.AdditionalArgs["embed_models"]["value"]
    embed_models = embed_models_str.split(",")
    
    # Validate embedding models
    if len(embed_models)<1:
        raise Exception("You must specify at least one valid model of GLOVE,FASTTEXT,OPENAI with the -ems flag")


    using_openai = False
    using_fasttext = False
    using_glove = False
    for embed_model in embed_models:
        if embed_model=="OPENAI":
            using_openai = True
        if embed_model=="FASTTEXT":
            using_fasttext = True
        if embed_model=="GLOVE":
            using_glove = True
        if embed_model not in EMBED_MODEL_DEFINITIONS:
              raise Exception(f"{embed_model} is invalid, You must specify at least one valid model of GLOVE,FASTTEXT,OPENAI with the -ems flag")
    
    # Create embedding model mappings
    embed_model_mappings = []
    for embed_model in embed_models:
        if embed_model in EMBED_MODEL_DEFINITIONS:
            field_name = EMBED_MODEL_DEFINITIONS[embed_model]["field_name"]
            model_definition = EMBED_MODEL_DEFINITIONS[embed_model]["model_definition"]
            embed_model_mappings.append({"model_id": model_definition, "field_name": field_name})

    logger.info(f"Loading file {constants.WIKI_PATH}")

    # Define columns to read from CSV
    usecols=[
                        "url",
                        "title",
                        "text",
                        "content_vector",
                        "content_glove_vector",
                        "content_fasttext_vector"
                    ]

    # Read Wikipedia records from CSV
    wiki_records_df = pd.read_csv(constants.WIKI_PATH,usecols=usecols)
    
    
    # Calculate total rows and chunks
    total_rows = len(wiki_records_df)
    total_chunks = total_rows // CHUNK_SIZE + (
        1 if total_rows % CHUNK_SIZE else 0
    )   
    with Surreal(db_params.DB_PARAMS.url) as connection:

        
        connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
        connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)
        logger.info("Connected to SurrealDB")


    
        

        # Read and execute table DDL that creates the tables and indexes if missing
        with open("./schema/table_ddl.surql") as f: 
            surlql_to_execute = f.read()
            surlql_to_execute = surlql_to_execute.format(corpus_table = "embedded_wiki")
            SurrealParams.ParseResponseForErrors( connection.query_raw(surlql_to_execute))


        logger.info("Deleting any existing wiki rows from SurrealDB")
        # Delete existing wiki records
        SurrealParams.ParseResponseForErrors(connection.query_raw(DELETE_WIKI_RECORDS))

        logger.info("Inserting rows into SurrealDB")
        # Iterate through chunks and insert records
        with tqdm.tqdm(total=total_chunks, desc="Inserting") as pbar:
            for i in range(0, total_rows, CHUNK_SIZE):
                chunk = wiki_records_df.iloc[i:i + CHUNK_SIZE]
                formatted_rows = [
                        {
                            "url":str(row["url"]),
                            "title":str(row["title"]),
                            "text":str(row["text"]),
                            "content_openai_vector":ast.literal_eval(row["content_vector"]) if using_openai else None,
                            "content_glove_vector":ast.literal_eval(row["content_glove_vector"]) if using_glove else None,
                            "content_fasttext_vector":ast.literal_eval(row["content_fasttext_vector"]) if using_fasttext else None
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

        

        # Update corpus table information
        logger.info(f"Updating corpus table info for {TABLE_NAME}")
        SurrealParams.ParseResponseForErrors( connection.query_raw(UPDATE_CORPUS_TABLE_INFO,params={"embed_models":embed_model_mappings}))





if __name__ == "__main__":
    surreal_wiki_insert()
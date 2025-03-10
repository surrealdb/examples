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

TABLE_NAME = "embedded_wiki"
DISPLAY_NAME = "Wikipedia"


GET_EMBED_MODEL_DESCRIPTIONS = """
    SELECT * FROM embedding_model_definition;
"""


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



    
UPDATE_CORPUS_TABLE_INFO = f"""
    DELETE FROM corpus_table_model WHERE corpus_table = corpus_table:{TABLE_NAME};
    FOR $model IN $embed_models {{
        LET $model_definition = type::thing("embedding_model_definition",$model.model_id);
        UPSERT corpus_table_model:[corpus_table:{TABLE_NAME},$model_definition] SET model = $model_definition,field_name = $model.field_name, corpus_table=corpus_table:{TABLE_NAME};
    }};
    UPSERT corpus_table:{TABLE_NAME} SET table_name = '{TABLE_NAME}', display_name = '{DISPLAY_NAME}', 
        embed_models = (SELECT value id FROM corpus_table_model WHERE corpus_table = corpus_table:{TABLE_NAME}) RETURN NONE;
        
"""


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

DELETE_WIKI_RECORDS = f"DELETE {TABLE_NAME};"


CHUNK_SIZE = 50



def surreal_wiki_insert() -> None:
    args_loader.AddArg(
        "embed_models",
        "ems",
        "embed_models",
        "The Embed models you'd like to calculate sepearated by , can be GLOVE,FASTTEXT,OPENAI eg -ems OPENAI,GLOVE will calculate both OPENAI and GLOVE. (default{})",
        "GLOVE,FASTTEXT,OPENAI"
    )
    args_loader.LoadArgs()

    """Main entrypoint to insert Wikipedia embeddings into SurrealDB."""
    logger = loggers.setup_logger("SurrealWikiInsert")

    logger.info(args_loader.string_to_print())

    embed_models_str = args_loader.AdditionalArgs["embed_models"]["value"]
    embed_models = embed_models_str.split(",")
    
    if len(embed_models)<1:
        raise Exception("You must specify at least one valid model of GLOVE,FASTTEXT,OPENAI with the -ems flag")
    



    for embed_model in embed_models:
        if embed_model not in EMBED_MODEL_DEFINITIONS:
              raise Exception(f"{embed_model} is invalid, You must specify at least one valid model of GLOVE,FASTTEXT,OPENAI with the -ems flag")
    

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


    
        embed_model_mappings = []
        for embed_model in embed_models:
            if embed_model in EMBED_MODEL_DEFINITIONS:
                field_name = EMBED_MODEL_DEFINITIONS[embed_model]["field_name"]
                model_definition = EMBED_MODEL_DEFINITIONS[embed_model]["model_definition"]
                embed_model_mappings.append({"model_id": model_definition, "field_name": field_name})
        

        # logger.info(f"Updating corpus table info for {TABLE_NAME}")
        # SurrealParams.ParseResponseForErrors( connection.query_raw(UPDATE_CORPUS_TABLE_INFO,params={"embed_models":embed_model_mappings}))
        # return

        with open("./schema/table_ddl.surql") as f: 
            surlql_to_execute = f.read()
            surlql_to_execute = surlql_to_execute.format(corpus_table = "embedded_wiki")
            SurrealParams.ParseResponseForErrors( connection.query_raw(surlql_to_execute))


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

        

        logger.info(f"Updating corpus table info for {TABLE_NAME}")
        SurrealParams.ParseResponseForErrors( connection.query_raw(UPDATE_CORPUS_TABLE_INFO,params={"embed_models":embed_model_mappings}))





if __name__ == "__main__":
    surreal_wiki_insert()
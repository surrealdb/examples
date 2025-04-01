"""Backend for SurrealDB chat interface."""

import contextlib
import datetime
from collections.abc import AsyncGenerator
import fastapi
from surrealdb import AsyncSurreal,RecordID
from fastapi import responses, staticfiles, templating
from surrealdb_rag.helpers.llm_handler import RAGChatHandler,ModelListHandler

import uvicorn
import ast
from urllib.parse import urlencode

from surrealdb_rag.helpers.constants import ArgsLoader
from surrealdb_rag.helpers.params import DatabaseParams, ModelParams, SurrealParams

from surrealdb_rag.helpers.ux_helpers import *

from surrealdb_rag.helpers.prompt_templates import PROMPT_TEXT_TEMPLATES

from surrealdb_rag.helpers.corpus_data_handler import CorpusTableListHandler,CorpusDataHandler

from surrealdb_rag.helpers.chat_handler import ChatHandler


# Load configuration parameters
db_params = DatabaseParams()
model_params = ModelParams()
args_loader = ArgsLoader("LLM Model Handler",db_params,model_params)
args_loader.LoadArgs()

GRAPH_SIZE_LIMIT = 1000




templates = templating.Jinja2Templates(directory="templates")
templates.env.filters["extract_id"] = extract_id
templates.env.filters["format_url_id"] = format_url_id
templates.env.filters["convert_timestamp_to_date"] = convert_timestamp_to_date
life_span = {}


@contextlib.asynccontextmanager
async def lifespan(_: fastapi.FastAPI) -> AsyncGenerator:
    """FastAPI lifespan to create and destroy objects.

    Initializes and closes the SurrealDB connection and loads LLM and corpus data.
    """
    connection = AsyncSurreal(db_params.DB_PARAMS.url)
    await connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
    await connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)
    life_span["surrealdb"] = connection


    model_list = ModelListHandler(model_params,life_span["surrealdb"])

    corpus_list = CorpusTableListHandler(life_span["surrealdb"],model_params)
    
    
    life_span["llm_models"] = await model_list.available_llm_models()
    life_span["corpus_tables"] = await corpus_list.available_corpus_tables()


    yield
    life_span.clear()


# Initialize FastAPI application
app = fastapi.FastAPI(lifespan=lifespan)
app.mount("/static", staticfiles.StaticFiles(directory="static"), name="static")




@app.get("/", response_class=responses.HTMLResponse)
async def index(request: fastapi.Request) -> responses.HTMLResponse:

    """Render the main chat interface."""

    available_llm_models = life_span["llm_models"]
    available_corpus_tables = life_span["corpus_tables"]
    #default_prompt_text = RAGChatHandler.DEFAULT_PROMPT_TEXT

    default_llm_model = life_span["llm_models"][next(iter(life_span["llm_models"]))]
    default_corpus_table = life_span["corpus_tables"][next(iter(life_span["corpus_tables"]))]

    default_prompt_text = PROMPT_TEXT_TEMPLATES[next(iter(PROMPT_TEXT_TEMPLATES))]["text"]

    return templates.TemplateResponse("index.html", {
            "request": request, 
                                                     "available_llm_models": available_llm_models, 
                                                     "available_corpus_tables": available_corpus_tables,
                                                     "default_llm_model": default_llm_model,
                                                     "default_corpus_table": default_corpus_table,
                                                     "default_prompt_text":default_prompt_text,
                                                     "prompt_text_templates":PROMPT_TEXT_TEMPLATES
                                                     })

@app.get("/get_corpus_table_details", response_class=responses.HTMLResponse)
async def get_corpus_table_details(
    request: fastapi.Request,corpus_table: str = fastapi.Query(...)):
    """Retrieve and return details of a corpus table."""
    corpus_table_detail = life_span["corpus_tables"].get(corpus_table)
    default_embed_model = corpus_table_detail["embed_models"][0]
    if corpus_table_detail:
        s = f"Table: {corpus_table_detail['table_name']}"
    else:
        s = "Corpus table details not found."

    
    return templates.TemplateResponse(
        "corpus_table_detail.html",
        {
            "request": request,
            "corpus_table_detail": corpus_table_detail,
            "default_embed_model": default_embed_model
        },
    )
    


@app.get("/get_additional_data_query", response_class=responses.HTMLResponse)
async def get_additional_data_query(
    request: fastapi.Request,corpus_table: str = fastapi.Query(...),additional_data_field: str = fastapi.Query(...)):
    """Retrieve simple table from a corpus table."""

    corpus_table_detail = life_span["corpus_tables"].get(corpus_table)
    corpus_data_handler = CorpusDataHandler(life_span["surrealdb"],corpus_table_detail)
    query_results = await corpus_data_handler.query_additional_data(additional_data_field)


    return templates.TemplateResponse(
        "query_results.html",
        {
            "request": request,
            "query_results": query_results,
        },
    )



@app.get("/get_llm_model_details")
async def get_llm_model_details(llm_model: str = fastapi.Query(...)):
    """Retrieve and return details of an LLM model."""
    model_data = life_span["llm_models"].get(llm_model)
    if model_data:
        s = f" Platform: {model_data['platform']},  Host: {model_data['host']} <br> Version: {model_data['model_version']}"
    else:
        s = "Model details not found."
    return fastapi.Response(s, media_type="text/html") #Return response object
    
@app.get("/get_embed_model_details")
async def get_embed_model_details(corpus_table: str = fastapi.Query(...),embed_model: str = fastapi.Query(...)):
    """Retrieve and return details of an embedding model."""
    embed_models = life_span["corpus_tables"][corpus_table]["embed_models"]
    embed_model_detail = None
    embed_model = ast.literal_eval(embed_model)
    for model in embed_models:
        #arrays are passed as csv from the html
        if embed_model == model["model"]:
            embed_model_detail = model
            break
    if embed_model_detail==None :
        raise Exception(f"Invalid embedd model {embed_model}")
    else:
        s = f""" 
            Dimensions: {embed_model_detail['dimensions']}, Host: {embed_model_detail['host']}<br> 
            Corpus: {embed_model_detail['corpus']}<br>  
            Description: {embed_model_detail['description']}
        """
    
    return fastapi.Response(s, media_type="text/html") #Return response object
    


@app.post("/chats", response_class=responses.HTMLResponse)
async def create_chat(request: fastapi.Request) -> responses.HTMLResponse:
    """Create a new chat."""

    chat_handler = ChatHandler(life_span["surrealdb"])
    chat_record = await chat_handler.create_chat()

    return templates.TemplateResponse(
        "create_chat.html",
        {
            "request": request,
            "chat_id": chat_record["id"],
            "chat_title": chat_record["title"],
        },
    )


@app.delete("/chats/{chat_id}/delete", response_class=responses.HTMLResponse)
async def delete_chat(
    request: fastapi.Request, chat_id: str
) -> responses.HTMLResponse:
    
    """Delete a chat."""

    chat_handler = ChatHandler(life_span["surrealdb"])
    await chat_handler.delete_chat(chat_id)

    return fastapi.Response(status_code=fastapi.status.HTTP_204_NO_CONTENT)

@app.get("/chats/{chat_id}", response_class=responses.HTMLResponse)
async def load_chat(
    request: fastapi.Request, chat_id: str
) -> responses.HTMLResponse:

    """Load a chat."""

    chat_handler = ChatHandler(life_span["surrealdb"])
    chat_detail = await chat_handler.chat_detail(chat_id)

    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "messages": chat_detail["messages"],
            "chat": chat_detail["chat"]
        },
    )


@app.get("/messages/{message_id}", response_class=responses.HTMLResponse)
async def load_message(
    request: fastapi.Request, message_id: str
) -> responses.HTMLResponse:
    

    """Load a message"""

    chat_handler = ChatHandler(life_span["surrealdb"])
    message_detail = await chat_handler.message_detail(message_id)


    return templates.TemplateResponse(
        "message_detail.html",
        {
            "request": request,
            "message": message_detail["message"],
            "message_id": message_id,
            "corpus_table": message_detail["corpus_table"],
            "graph_data": message_detail["graph_data"],
            "graph_size_limit": GRAPH_SIZE_LIMIT,
            "graph_size": message_detail["graph_size"],
            "graph_id": message_detail["graph_id"]
        },
    )
			
@app.get("/chats", response_class=responses.HTMLResponse)
async def load_all_chats(request: fastapi.Request) -> responses.HTMLResponse:
    """Load all chats."""

    chat_handler = ChatHandler(life_span["surrealdb"])
    chat_records = await chat_handler.all_chats()
    return templates.TemplateResponse(
        "chats.html", {"request": request, "chats": chat_records}
    )


@app.post(
    "/chats/{chat_id}/send-user-message", response_class=responses.HTMLResponse
)
async def send_user_message(
    request: fastapi.Request,
    chat_id: str,
    content: str = fastapi.Form(...),
    embed_model: str = fastapi.Form(...),
    corpus_table: str = fastapi.Form(...),
    number_of_chunks: int = fastapi.Form(...),
    graph_mode: str | None = fastapi.Form(...)
) -> responses.HTMLResponse:
    """Send user message. The UX will post then call a send_system_message to query the LLM."""

    embed_model = ast.literal_eval(embed_model)
    chat_handler = ChatHandler(life_span["surrealdb"])
  
    
    message = await chat_handler.create_user_message(
        chat_id, corpus_table, content, embed_model, number_of_chunks, graph_mode,model_params.openai_token
    )

    return templates.TemplateResponse(
        "message.html",
        {
            "request": request,
            "chat_id": chat_id,
            "new_message": True,
            "message" : message["message"]
        },
    )



@app.post(
    "/chats/{chat_id}/send-system-message",
    response_class=responses.HTMLResponse,
)
async def send_system_message(
    request: fastapi.Request, 
    chat_id: str,
    llm_model: str = fastapi.Form(...),
    prompt_template: str = fastapi.Form(...),
    number_of_chats: int = fastapi.Form(...)
) -> responses.HTMLResponse:
    """Send system message. This queries the LLM with the relevant context and inputs"""

    
    chat_handler = ChatHandler(life_span["surrealdb"])

    model_data = life_span["llm_models"].get(llm_model)
    if not model_data:
            raise SystemError(f"Error in outcome: Invalid model {llm_model}") 
    
    llm_handler = RAGChatHandler(model_data,model_params,life_span["surrealdb"])

    message = await chat_handler.create_system_message(
        chat_id, llm_model, prompt_template, number_of_chats,llm_handler)
    return templates.TemplateResponse(
        "message.html",
        {
            "request": request,
            "new_title": message["new_title"],
            "chat_id": chat_id,
            "new_message": True,
            "message": message["message"]
        },
    )



                                                                   

@app.get("/relation_detail", response_class=responses.HTMLResponse)
async def load_relation_detail(
    request: fastapi.Request, 
    corpus_table: str = fastapi.Query(...), 
    identifier_in: str = fastapi.Query(...), 
    identifier_out: str = fastapi.Query(...), 
    relationship: str = fastapi.Query(...)
) -> responses.HTMLResponse:
    """Load a relation info for 2 identifiers and a relation keyword."""

    corpus_table_detail = life_span["corpus_tables"].get(corpus_table)
    corpus_data_handler = CorpusDataHandler(life_span["surrealdb"],corpus_table_detail)
    relation_info = await corpus_data_handler.relation_detail(corpus_table_detail,identifier_in,identifier_out,relationship)

    return templates.TemplateResponse(
        "relation.html",
        {
            "request": request,
            "corpus_table": corpus_table,
            "relation_info": relation_info,
        },
    )



                                                                                        

@app.get("/entity_detail", response_class=responses.HTMLResponse)
async def load_entity_detail(
    request: fastapi.Request, 
    corpus_table: str = fastapi.Query(...), 
    identifier: str = fastapi.Query(...)
) -> responses.HTMLResponse:
    """Load a entity info for an identifier."""

    corpus_table_detail = life_span["corpus_tables"].get(corpus_table)
    corpus_data_handler = CorpusDataHandler(life_span["surrealdb"],corpus_table_detail)
    entity_detail  = await corpus_data_handler.entity_detail(corpus_table_detail,identifier)
 


    return templates.TemplateResponse(
        "entity.html",
        {
            "request": request,
            "corpus_table": corpus_table,
            "entity_mentions": entity_detail["entity_mentions"],
            "entity_relations": entity_detail["entity_relations"],
            "entity_info": entity_detail["entity_info"]
        },
    )






@app.get("/source_documents/{url}", response_class=responses.HTMLResponse)
async def load_source_document(
    request: fastapi.Request,
    url: str,
    corpus_table: str = fastapi.Query(...), 
) -> responses.HTMLResponse:
    
    """Load a source document and related info"""

    corpus_table_detail = life_span["corpus_tables"].get(corpus_table)
    corpus_data_handler = CorpusDataHandler(life_span["surrealdb"],corpus_table_detail)
    source_document_details = await corpus_data_handler.source_document_details(corpus_table_detail,url)

    return templates.TemplateResponse(
        "source_document_contexts.html",
        {
            "request": request,
            "entities": source_document_details["entities"],
            "relations": source_document_details["relations"],
            "source_document_info": source_document_details["source_document_info"],
            "url": url
        },
    )




@app.get("/load_graph", response_class=responses.HTMLResponse)
async def load_corpus_graph(
    request: fastapi.Request, 
    corpus_table: str = fastapi.Query(...), 
    graph_start_date: str | None = fastapi.Query(None), 
    graph_end_date: str | None = fastapi.Query(None), 
    identifier: str | None = fastapi.Query(None), 
    relationship: str | None = fastapi.Query(None), 
    url: str | None = fastapi.Query(None), 
    name_filter: str | None = fastapi.Query(None), 
    graph_size_limit: int | None = fastapi.Query(None)
) -> responses.HTMLResponse:
    """Load a graph for a data source with different filtering parameters."""


    if graph_size_limit is None:
        graph_size_limit = GRAPH_SIZE_LIMIT

    corpus_table_detail = life_span["corpus_tables"].get(corpus_table)
    corpus_data_handler = CorpusDataHandler(life_span["surrealdb"],corpus_table_detail)

    corpus_graph_data = await corpus_data_handler.corpus_graph_data(
        corpus_table_detail,
        graph_start_date,
        graph_end_date,
        identifier,
        relationship,
        url,
        name_filter,
        graph_size_limit
    )
    
    return templates.TemplateResponse(
        "graph.html",
        {
            "request": request,
            "corpus_table": corpus_table,
            "graph_data": corpus_graph_data["graph_data"],
            "graph_size_limit": graph_size_limit,
            "graph_size": corpus_graph_data["graph_size"],
            "graph_title": corpus_graph_data["graph_title"],
            "graph_id": corpus_graph_data["graph_id"],
        },
    )


@app.get("/documents/{document_id}", response_class=responses.HTMLResponse)
async def load_document(
    request: fastapi.Request, document_id: str,
    corpus_table: str = fastapi.Query(...)
) -> responses.HTMLResponse:
    """Load a document detail for a context search."""
    
    corpus_table_detail = life_span["corpus_tables"].get(corpus_table)
    corpus_data_handler = CorpusDataHandler(life_span["surrealdb"],corpus_table_detail)
    document_id = unformat_url_id(document_id)
    document = await corpus_data_handler.source_document_detail(corpus_table_detail,document_id)

    return templates.TemplateResponse(
        "document.html",
        {
            "request": request,
            "document": document,
            "document_id": document_id
        },
    )






def run_app():
    uvicorn.run("__main__:app", host="0.0.0.0", port=8081, reload=True)
    # uvicorn.run(
    #     "__main__:app",  reload=True
    # )


if __name__ == "__main__":
    run_app()
"""Backend for SurrealDB chat interface."""

import contextlib
import datetime
from collections.abc import AsyncGenerator
import fastapi
from surrealdb import AsyncSurreal,RecordID
from fastapi import responses, staticfiles, templating
from surrealdb_rag.llm_handler import LLMModelHander,ModelListHandler
from urllib.parse import quote
import json

import uvicorn
import ast
from urllib.parse import urlencode
from surrealdb_rag.constants import DatabaseParams, ModelParams, ArgsLoader, SurrealParams


# Load configuration parameters
db_params = DatabaseParams()
model_params = ModelParams()
args_loader = ArgsLoader("LLM Model Handler",db_params,model_params)
args_loader.LoadArgs()


"""Format a SurrealDB RecordID for use in a URL.

    Replaces '/' with '|' and URL-encodes the ID.

    Args:
        surrealdb_id: SurrealDB RecordID.

    Returns:
        Formatted string for use in a URL.
    """
def format_url_id(surrealdb_id: RecordID) -> str:

    if RecordID == type(surrealdb_id):
        str_to_format = surrealdb_id.id
    else:
        str_to_format = surrealdb_id
    return quote(str_to_format).replace("/","|")
    
"""Unformat a URL-encoded SurrealDB RecordID.

    Replaces '|' with '/'.

    Args:
        surrealdb_id: URL-encoded SurrealDB RecordID.

    Returns:
        Unformatted string.
    """
def unformat_url_id(surrealdb_id: str) -> str:
    return surrealdb_id.replace("|","/")

"""Extract numeric ID from SurrealDB record ID.

    SurrealDB record ID comes in the form of `<table_name>:<unique_id>`.
    CSS classes cannot be named with a `:` so for CSS we extract the ID.

    Args:
        surrealdb_id: SurrealDB record ID.

    Returns:
        ID with ':' replaced by '-'.
    """
def extract_id(surrealdb_id: RecordID) -> str:
    
    if RecordID == type(surrealdb_id):
    #return surrealdb_id.id
        return surrealdb_id.id.replace(":","-")
    else:
        return surrealdb_id.replace(":","-")


"""Convert a SurrealDB `datetime` to a readable string.

    Args:
        timestamp: SurrealDB `datetime` value.

    Returns:
        Date as a string.
    """
def convert_timestamp_to_date(timestamp: str) -> str:
    
    # parsed_timestamp = datetime.datetime.fromisoformat(timestamp.rstrip("Z"))
    # return parsed_timestamp.strftime("%B %d %Y, %H:%M")
    return timestamp




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
    
    
    life_span["llm_models"] = await model_list.available_llm_models()
    life_span["corpus_tables"] = await model_list.available_corpus_tables()


    yield
    life_span.clear()


# Initialize FastAPI application
app = fastapi.FastAPI(lifespan=lifespan)
app.mount("/static", staticfiles.StaticFiles(directory="static"), name="static")


@app.get("/", response_class=responses.HTMLResponse)
async def index(request: fastapi.Request) -> responses.HTMLResponse:

    """Render the main chat interface."""

    available_llm_models_json = json.dumps(life_span["llm_models"])
    available_corpus_tables_json = json.dumps(life_span["corpus_tables"])
    #default_prompt_text_json = json.dumps(LLMModelHander.DEFAULT_PROMPT_TEXT, ensure_ascii=False)

    default_llm_model = life_span["llm_models"][next(iter(life_span["llm_models"]))]
    default_corpus_table = life_span["corpus_tables"][next(iter(life_span["corpus_tables"]))]
    default_embed_model = default_corpus_table["embed_models"][0]

    default_prompt_text = LLMModelHander.PROMPT_TEXT_TEMPLATES[next(iter(LLMModelHander.PROMPT_TEXT_TEMPLATES))]["text"]
   

    return templates.TemplateResponse("index.html", {
            "request": request, 
                                                     "available_llm_models": available_llm_models_json, 
                                                     "available_corpus_tables": available_corpus_tables_json,
                                                     "default_llm_model": default_llm_model,
                                                     "default_corpus_table": default_corpus_table,
                                                     "default_embed_model":default_embed_model,
                                                     "default_prompt_text":default_prompt_text,
                                                     "prompt_text_templates":LLMModelHander.PROMPT_TEXT_TEMPLATES
                                                     })

@app.get("/get_corpus_table_details")
async def get_corpus_table_details(corpus_table: str = fastapi.Query(...)):
    """Retrieve and return details of a corpus table."""
    corpus_table_detail = life_span["corpus_tables"].get(corpus_table)
    if corpus_table_detail:
        s = f"Table: {corpus_table_detail['table_name']}"
    else:
        s = "Corpus table details not found."
    return fastapi.Response(s, media_type="text/html") 
    


@app.get("/get_additional_data_query", response_class=responses.HTMLResponse)
async def get_additional_data_query(
    request: fastapi.Request,corpus_table: str = fastapi.Query(...),additional_data_field: str = fastapi.Query(...)):
    query_results = await life_span["surrealdb"].query(
        """RETURN fn::select_additional_data($corpus_table,$key)""",params = {"corpus_table":corpus_table,"key":additional_data_field}    
    )
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
    chat_record = await life_span["surrealdb"].query(
        """RETURN fn::create_chat();"""
    )
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
    
    """Delete a chat and its messages."""
    SurrealParams.ParseResponseForErrors( await life_span["surrealdb"].query_raw(
        """RETURN fn::delete_chat($chat_id)""",params = {"chat_id":chat_id}    
    ))
    return fastapi.Response(status_code=fastapi.status.HTTP_204_NO_CONTENT)

@app.get("/chats/{chat_id}", response_class=responses.HTMLResponse)
async def load_chat(
    request: fastapi.Request, chat_id: str
) -> responses.HTMLResponse:
    """Load a chat."""
    message_records = await life_span["surrealdb"].query(
        """RETURN fn::load_chat($chat_id)""",params = {"chat_id":chat_id}    
    )

    title = await life_span["surrealdb"].query(
        """RETURN fn::get_chat_title($chat_id);""",params = {"chat_id":chat_id}
    )

    for i, message in enumerate(message_records):
        message_think = LLMModelHander.parse_llm_response_content(message["content"])
        message_records[i]["content"] = message_think["content"]
        if message_think["think"]:
            message_records[i]["think"] = message_think["think"]

    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "messages": message_records,
            "chat": {"id":chat_id,"title": title }
        },
    )


@app.get("/messages/{message_id}", response_class=responses.HTMLResponse)
async def load_message(
    request: fastapi.Request, message_id: str
) -> responses.HTMLResponse:
    """Load a message."""
    message = await life_span["surrealdb"].query(
        """RETURN fn::load_message_detail($message_id)""",params = {"message_id":message_id}    
    )
    message_think = LLMModelHander.parse_llm_response_content(message["content"])
    message["content"] = message_think["content"]
    if message_think["think"]:
        message["think"] = message_think["think"]
    
    return templates.TemplateResponse(
        "message_detail.html",
        {
            "request": request,
            "message": message,
            "message_id": message_id,
        },
    )


@app.get("/documents/{document_id}", response_class=responses.HTMLResponse)
async def load_document(
    request: fastapi.Request, document_id: str,
    corpus_table: str = fastapi.Query(...)
) -> responses.HTMLResponse:
    """Load a chat."""
    document_id = unformat_url_id(document_id)
    document = await life_span["surrealdb"].query(
        """RETURN fn::load_document_detail($corpus_table,$document_id)""",params = {"corpus_table":corpus_table,"document_id":document_id}    
    )
    return templates.TemplateResponse(
        "document.html",
        {
            "request": request,
            "document": document[0],
            "document_id": document_id
        },
    )




@app.get("/chats", response_class=responses.HTMLResponse)
async def load_all_chats(request: fastapi.Request) -> responses.HTMLResponse:
    """Load all chats."""
    chat_records = await life_span["surrealdb"].query(
        """RETURN fn::load_all_chats();"""
    )
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
    number_of_chunks: int = fastapi.Form(...)
) -> responses.HTMLResponse:
    """Send user message."""

    embed_model = ast.literal_eval(embed_model)
    # # need to fix for model_trainer
    # if embed_model[0] == "OPENAI":
    #      outcome = SurrealParams.ParseResponseForErrors( await life_span["surrealdb"].query_raw(
    #         """RETURN fn::create_user_message($chat_id,$corpus_table, $content,type::thing('embedding_model_definition',$embedding_model),$openaitoken,$number_of_chunks);""",params = {"chat_id":chat_id,"corpus_table":corpus_table,"content":content,"embedding_model":embed_model,"openaitoken":model_params.openai_token,"number_of_chunks":number_of_chunks}    
    #     ))
    # else:
    #     outcome = SurrealParams.ParseResponseForErrors( await life_span["surrealdb"].query_raw(
    #         """RETURN fn::create_user_message($chat_id,$corpus_table, $content,type::thing('embedding_model_definition',$embedding_model));""",
    #         params = {"chat_id":chat_id,"corpus_table":corpus_table,"content":content,"embedding_model":embed_model}    
    #     ))


    outcome = SurrealParams.ParseResponseForErrors( await life_span["surrealdb"].query_raw(
            """RETURN fn::create_user_message($chat_id,$corpus_table, $content,type::thing('embedding_model_definition',$embedding_model),$openaitoken,$number_of_chunks);""",
            params = {
                "chat_id":chat_id,
                "corpus_table":corpus_table,
                "content":content,
                "embedding_model":embed_model,
                "openaitoken":model_params.openai_token,
                "number_of_chunks":number_of_chunks
                }    
        ))
    

    message = outcome["result"][0]["result"]
    return templates.TemplateResponse(
        "message.html",
        {
            "request": request,
            "chat_id": chat_id,
            "new_message": True,
            "message" : message
        },
    )


@app.post(
    "/chats/{chat_id}/send-system-message",
    response_class=responses.HTMLResponse,
)
async def send_system_message(
    request: fastapi.Request, chat_id: str,
    llm_model: str = fastapi.Form(...),
    prompt_template: str = fastapi.Form(...),
    number_of_chats: int = fastapi.Form(...)
) -> responses.HTMLResponse:
    """Send system message."""

    
    

    # outcome = SurrealParams.ParseResponseForErrors( await life_span["surrealdb"].query_raw(
    #     """RETURN fn::get_last_user_message_input_and_prompt($chat_id,$prompt,$message_memory_length);""",params = {"chat_id":chat_id,"prompt":LLMModelHander.DEFAULT_PROMPT_TEXT,"message_memory_length":5}
    # ))
    outcome = SurrealParams.ParseResponseForErrors( await life_span["surrealdb"].query_raw(
        """RETURN fn::get_last_user_message_input_and_prompt($chat_id,$prompt,$message_memory_length);""",params = {"chat_id":chat_id,"prompt":prompt_template,"message_memory_length":number_of_chats}
    ))
    result =  outcome["result"][0]["result"]
    prompt_text = result["prompt_text"]
    content = result["content"]
    #call the LLM
    model_data = life_span["llm_models"].get(llm_model)
    if not model_data:
            raise SystemError(f"Error in outcome: Invalid model {llm_model}") 
    
    llm_handler = LLMModelHander(model_data,model_params,life_span["surrealdb"])

    llm_response = await llm_handler.get_chat_response(prompt_text,content)
    
    #save the response in the DB
    outcome = SurrealParams.ParseResponseForErrors(await life_span["surrealdb"].query_raw(
        """RETURN fn::create_system_message($chat_id,$llm_response,$llm_model,$prompt_text);""",params = {"chat_id":chat_id,"llm_response":llm_response,"llm_model":llm_model,"prompt_text":prompt_text}
        ))
    
    title = await life_span["surrealdb"].query(
        """RETURN fn::get_chat_title($chat_id);""",params = {"chat_id":chat_id}
    )
    new_title = ""
    if title == "Untitled chat":
        first_message_text = await life_span["surrealdb"].query(
            "RETURN fn::get_first_message($chat_id);",params={"chat_id":chat_id}
        )
        system_prompt = "You are a conversation title generator for a ChatGPT type app. Respond only with a simple title using the user input."
        new_title = await llm_handler.get_short_plain_text_response(system_prompt,first_message_text)
        #update chat title in database
        SurrealParams.ParseResponseForErrors(await life_span["surrealdb"].query_raw(
            """UPDATE type::record($chat_id) SET title=$title;""",params = {"chat_id":chat_id,"title":new_title}    
        ))



    message = outcome["result"][0]["result"]

    
    message_think = LLMModelHander.parse_llm_response_content(message["content"])
    message["content"] = message_think["content"]
    if message_think["think"]:
        message["think"] = message_think["think"]
    return templates.TemplateResponse(
        "message.html",
        {
            "request": request,
            "new_title": new_title.strip(),
            "chat_id": chat_id,
            "new_message": True,
            "message": message
        },
    )



def run_app():
    
    uvicorn.run(
        "__main__:app",  reload=True
    )


if __name__ == "__main__":
    run_app()
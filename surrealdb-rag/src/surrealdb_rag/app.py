"""Backend for SurrealDB chat interface."""

import contextlib
import datetime
from collections.abc import AsyncGenerator
import fastapi
from surrealdb import AsyncSurreal,RecordID
from fastapi import responses, staticfiles, templating
from surrealdb_rag.llm_handler import LLMModelHander,ModelListHandler

import uvicorn

from surrealdb_rag.constants import DatabaseParams, ModelParams, ArgsLoader, SurrealParams
db_params = DatabaseParams()
model_params = ModelParams()
args_loader = ArgsLoader("LLM Model Handler",db_params,model_params)
args_loader.LoadArgs()




def extract_id(surrealdb_id: RecordID) -> str:
    """Extract numeric ID from SurrealDB record ID.

    SurrealDB record ID comes in the form of `<table_name>:<unique_id>`.
    CSS classes cannot be named with a `:` so for CSS we extract the ID.

    Args:
        surrealdb_id: SurrealDB record ID.

    Returns:
        ID.
    """
    if RecordID == type(surrealdb_id):
    #return surrealdb_id.id
        return surrealdb_id.id.replace(":","-")
    else:
        return surrealdb_id.replace(":","-")



def convert_timestamp_to_date(timestamp: str) -> str:
    """Convert a SurrealDB `datetime` to a readable string.

    The result will be of the format: `April 05 2024, 15:30`.

    Args:
        timestamp: SurrealDB `datetime` value.

    Returns:
        Date as a string.
    """
    # parsed_timestamp = datetime.datetime.fromisoformat(timestamp.rstrip("Z"))
    # return parsed_timestamp.strftime("%B %d %Y, %H:%M")
    return timestamp

templates = templating.Jinja2Templates(directory="templates")
templates.env.filters["extract_id"] = extract_id
templates.env.filters["convert_timestamp_to_date"] = convert_timestamp_to_date
life_span = {}


@contextlib.asynccontextmanager
async def lifespan(_: fastapi.FastAPI) -> AsyncGenerator:
    """FastAPI lifespan to create and destroy objects."""

    connection = AsyncSurreal(db_params.DB_PARAMS.url)
    await connection.signin({"username": db_params.DB_PARAMS.username, "password": db_params.DB_PARAMS.password})
    await connection.use(db_params.DB_PARAMS.namespace, db_params.DB_PARAMS.database)
    life_span["surrealdb"] = connection


    model_list = ModelListHandler(model_params,life_span["surrealdb"])

    life_span["llm_models"] = await model_list.available_llm_models()
    life_span["embed_models"] = await model_list.available_embed_models()

    yield
    life_span.clear()


app = fastapi.FastAPI(lifespan=lifespan)
app.mount("/static", staticfiles.StaticFiles(directory="static"), name="static")


@app.get("/", response_class=responses.HTMLResponse)
async def index(request: fastapi.Request) -> responses.HTMLResponse:


    return templates.TemplateResponse("index.html", {
            "request": request, 
                                                     "available_llm_models": life_span["llm_models"], 
                                                     "available_embed_models": life_span["embed_models"],
                                                     "default_llm_model": life_span["llm_models"][next(iter(life_span["llm_models"]))],
                                                     "default_embed_model":life_span["embed_models"][next(iter(life_span["embed_models"]))]
                                                     })

@app.get("/get_llm_model_details")
async def get_llm_model_details(llm_model: str = fastapi.Query(...)):
    model_data = life_span["llm_models"].get(llm_model)
    if model_data:
        s = f"Version: {model_data['model_version']}, Host: {model_data['host']}"
    else:
        s = "Model details not found."
    return fastapi.Response(s, media_type="text/html") #Return response object
    
@app.get("/get_embed_model_details")
async def get_embed_model_details(embed_model: str = fastapi.Query(...)):
    model_data = life_span["embed_models"].get(embed_model)
    if model_data:
        s = f"Dimensions: {model_data['dimensions']}, Host: {model_data['host']}"
    else:
        s = "Model details not found."
    return fastapi.Response(s, media_type="text/html") #Return response object
    


@app.post("/chats", response_class=responses.HTMLResponse)
async def create_chat(request: fastapi.Request) -> responses.HTMLResponse:
    """Create a chat."""
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
    return templates.TemplateResponse(
        "load_chat.html",
        {
            "request": request,
            "messages": message_records,
            "chat_id": chat_id,
        },
    )
@app.get("/messages/{message_id}", response_class=responses.HTMLResponse)
async def load_chat(
    request: fastapi.Request, message_id: str
) -> responses.HTMLResponse:
    """Load a chat."""
    message = await life_span["surrealdb"].query(
        """RETURN fn::load_message_detail($message_id)""",params = {"message_id":message_id}    
    )
    return templates.TemplateResponse(
        "load_message_detail.html",
        {
            "request": request,
            "message": message,
            "message_id": message_id,
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
    embed_model: str = fastapi.Form(...)
) -> responses.HTMLResponse:
    """Send user message."""
    if embed_model == "OPENAI":
         message = SurrealParams.ParseResponseForErrors( await life_span["surrealdb"].query_raw(
            """RETURN fn::create_user_message($chat_id, $content,$embedding_model,$openaitoken);""",params = {"chat_id":chat_id,"content":content,"embedding_model":embed_model,"openaitoken":model_params.openai_token}    
        ))
    else:
        message = SurrealParams.ParseResponseForErrors( await life_span["surrealdb"].query_raw(
            """RETURN fn::create_user_message($chat_id, $content,$embedding_model);""",params = {"chat_id":chat_id,"content":content,"embedding_model":embed_model}    
        ))


    return templates.TemplateResponse(
        "send_user_message.html",
        {
            "request": request,
            "chat_id": chat_id,
            "content": message["result"][0]["result"]["content"],
            "timestamp": message["result"][0]["result"]["timestamp"]
        },
    )


@app.post(
    "/chats/{chat_id}/send-system-message",
    response_class=responses.HTMLResponse,
)
async def send_system_message(
    request: fastapi.Request, chat_id: str,
    llm_model: str = fastapi.Form(...)
) -> responses.HTMLResponse:
    """Send system message."""

    
    

    message = SurrealParams.ParseResponseForErrors( await life_span["surrealdb"].query_raw(
        """RETURN fn::get_last_user_message_input_and_prompt($chat_id);""",params = {"chat_id":chat_id}
    ))
    result =  message["result"][0]["result"]
    prompt_text = result["prompt_text"]
    content = result["content"]
    #call the LLM
    model_data = life_span["llm_models"].get(llm_model)
    if not model_data:
            raise SystemError(f"Error in outcome: Invalid model {llm_model}") 
    
    llm_handler = LLMModelHander(model_data,model_params,life_span["surrealdb"])

    llm_response = llm_handler.get_chat_response(prompt_text,content)
    
    #save the response in the DB
    message = SurrealParams.ParseResponseForErrors(await life_span["surrealdb"].query_raw(
        """RETURN fn::create_message($chat_id, "system", $llm_response);""",params = {"chat_id":chat_id,"llm_response":llm_response}
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
        new_title = llm_handler.get_chat_response(system_prompt,first_message_text)
        #update chat title in database
        SurrealParams.ParseResponseForErrors(await life_span["surrealdb"].query_raw(
            """UPDATE type::record($chat_id) SET title=$title;""",params = {"chat_id":chat_id,"title":new_title}    
        ))



    result =  message["result"][0]["result"]



    return templates.TemplateResponse(
        "send_system_message.html",
        {
            "request": request,
            "content": result["content"],
            "timestamp": result["timestamp"],
            "new_title": new_title.strip(),
            "chat_id": chat_id,
        },
    )



def run_app():
    
    uvicorn.run(
        "__main__:app",  reload=True
    )


if __name__ == "__main__":
    run_app()
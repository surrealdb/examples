"""Load and insert Wikipedia embeddings into SurrealDB"""

import ast
import contextlib
import datetime
import logging
import os
import string
from typing import AsyncGenerator
import zipfile

import fastapi
import pandas as pd
import surrealdb
import tqdm
import wget
from fastapi import templating, responses, staticfiles

from dotenv import load_dotenv
load_dotenv()

FORMATTED_RECORD_FOR_INSERT_WIKI_EMBEDDING = string.Template(
    """{url: "$url", title: s"$title", text: s"$text", title_vector: $title_vector, content_vector: $content_vector}"""
)

INSERT_WIKI_EMBEDDING_QUERY = string.Template(
    """
    INSERT INTO wiki_embedding [\n $records\n];
    """
)

TOTAL_ROWS = 25000
CHUNK_SIZE = 100


def extract_id(surrealdb_id: str) -> str:
    """Extract numeric ID from SurrealDB record ID.
    SurrealDB record ID comes in the form of `<table_name>:<unique_id>`.
    CSS classes cannot be named with a `:` so for CSS we extract the ID.
    Args:
        surrealdb_id: SurrealDB record ID.
    Returns:
        ID.
    """
    return surrealdb_id.split(":")[1]


def convert_timestamp_to_date(timestamp: str) -> str:
    """Convert a SurrealDB `datetime` to a readable string.
    The result will be of the format: `April 05 2024, 15:30`.
    Args:
        timestamp: SurrealDB `datetime` value.
    Returns:
        Date as a string.
    """
    parsed_timestamp = datetime.datetime.fromisoformat(timestamp.rstrip("Z"))
    return parsed_timestamp.strftime("%B %d %Y, %H:%M")


templates = templating.Jinja2Templates(directory="templates")
templates.env.filters["extract_id"] = extract_id
templates.env.filters["convert_timestamp_to_date"] = convert_timestamp_to_date
life_span = {}


@contextlib.asynccontextmanager
async def lifespan(_: fastapi.FastAPI) -> AsyncGenerator:
    """FastAPI lifespan to create and destroy objects."""
    connection = surrealdb.Surreal(url="ws://localhost:8080/rpc")
    await connection.connect()
    await connection.signin({"user": "root", "pass": "root"})
    await connection.use("test", "test")

    openai_token = os.getenv("OPENAI_API_KEY")
    print(openai_token)
    await connection.set("openai_token", openai_token)
    life_span["surrealdb"] = connection
    yield
    life_span.clear()


app = fastapi.FastAPI(lifespan=lifespan)
app.mount("/static", staticfiles.StaticFiles(directory="static"), name="static")


@app.get("/", response_class=responses.HTMLResponse)
async def index(request: fastapi.Request) -> responses.HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/create-chat", response_class=responses.HTMLResponse)
async def create_chat(request: fastapi.Request) -> responses.HTMLResponse:
    chat_record = await life_span["surrealdb"].query(
        """RETURN fn::create_chat();"""
    )
    return templates.TemplateResponse(
        "create_chat.html",
        {
            "request": request,
            "chat_id": chat_record[0]['result']['id'],
            "chat_title": chat_record[0]['result']['title'],
        },
    )


@app.get("/load-chat/{chat_id}", response_class=responses.HTMLResponse)
async def load_chat(
    request: fastapi.Request, chat_id: str
) -> responses.HTMLResponse:
    data = {
        'tb': 'person'
    }
    result = await life_span["surrealdb"].query('CREATE person; SELECT * FROM type::table($tb);',vars=data)
    print(result)
    message_records = await life_span["surrealdb"].query('fn::load_chat($ch);', {
        'ch': chat_id,
    })
    print(message_records)
    return templates.TemplateResponse(
        "load_chat.html",
        {
            "request": request,
            "messages": message_records[0]['result'],
            "chat_id": chat_id,
        },
    )


@app.get("/chats", response_class=responses.HTMLResponse)
async def chats(request: fastapi.Request) -> responses.HTMLResponse:
    """Load all chats."""
    chat_records = await life_span["surrealdb"].query(
        """RETURN fn::load_all_chats();"""
    )
    return templates.TemplateResponse(
        "chats.html", {"request": request, "chats": chat_records}
    )


@app.post("/send-user-message", response_class=responses.HTMLResponse)
async def send_user_message(
    request: fastapi.Request,
    chat_id: str = fastapi.Form(...),
    content: str = fastapi.Form(...),
) -> responses.HTMLResponse:
    """Send user message."""
    message = await life_span["surrealdb"].query(
       """RETURN fn::create_user_message($chat_id, $content);""",
        {"chat_id": chat_id, "content": content}
    )
    return templates.TemplateResponse(
        "send_user_message.html",
        {
            "request": request,
            "chat_id": chat_id,
            "content": message[0]['result']['content'],
            "timestamp": message[0]['result']['timestamp'],
        },
    )


@app.get("/send-system-message/{chat_id}", response_class=responses.HTMLResponse)
async def send_system_message(
    request: fastapi.Request, chat_id: str
) -> responses.HTMLResponse:
    message = await life_span["surrealdb"].query(
        """RETURN fn::create_system_message($chat_id);""",
        {"chat_id": chat_id}
    )

    title = await life_span["surrealdb"].query(
        """RETURN fn::generate_chat_title($chat_id);""",
        {"chat_id": chat_id}
    )

    return templates.TemplateResponse(
        "send_system_message.html",
        {
            "request": request,
            "content": message[0]['result']['content'],
            "timestamp": message[0]['result']['timestamp'],
            "create_title": title == "Untitled chat",
            "chat_id": chat_id,
        },
    )


@app.get("/create-title/{chat_id}", response_class=responses.PlainTextResponse)
async def create_title(chat_id: str) -> responses.PlainTextResponse:
    title = await life_span["surrealdb"].query(
        """RETURN fn::generate_chat_title($chat_id);""",
        {"chat_id": chat_id}
    )
    return responses.PlainTextResponse(title.strip('"'))


def setup_logger(name: str) -> logging.Logger:
    """Configure and return a logger with the given name."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def get_data() -> None:
    """Extract `vector_database_wikipedia_articles_embedded.csv` to `/data`."""
    logger = setup_logger("get-data")

    logger.info("Downloading Wikipedia")
    wget.download(
        url="https://cdn.openai.com/API/examples/data/"
        "vector_database_wikipedia_articles_embedded.zip",
        out="data/vector_database_wikipedia_articles_embedded.zip",
    )

    logger.info("Extracting")
    with zipfile.ZipFile(
        "data/vector_database_wikipedia_articles_embedded.zip", "r"
    ) as zip_ref:
        zip_ref.extractall("data")

    logger.info("Extracted file successfully. Please check the data folder")


async def surreal_insert() -> None:
    """Main entrypoint to insert Wikipedia embeddings into SurrealDB."""
    logger = setup_logger("surreal_insert")

    total_chunks = TOTAL_ROWS // CHUNK_SIZE + (
        1 if TOTAL_ROWS % CHUNK_SIZE else 0
    )

    logger.info("Connecting to SurrealDB")
    connection = surrealdb.Surreal(url="ws://localhost:8080/rpc")
    await connection.connect()
    await connection.signin({"user": "root", "pass": "root"})
    await connection.use("test", "test")

    logger.info("Inserting rows into SurrealDB")
    with tqdm.tqdm(total=total_chunks, desc="Inserting") as pbar:
        for chunk in tqdm.tqdm(
            pd.read_csv(
                "data/vector_database_wikipedia_articles_embedded.csv",
                usecols=[
                    "url",
                    "title",
                    "text",
                    "title_vector",
                    "content_vector",
                ],
                chunksize=CHUNK_SIZE,
            ),
        ):
            formatted_rows = [
                FORMATTED_RECORD_FOR_INSERT_WIKI_EMBEDDING.substitute(
                    url=row["url"],
                    title=row["title"]
                    .replace("\\", "\\\\")
                    .replace('"', '\\"'),
                    text=row["text"].replace("\\", "\\\\").replace('"', '\\"'),
                    title_vector=ast.literal_eval(row["title_vector"]),
                    content_vector=ast.literal_eval(row["content_vector"]),
                )
                for _, row in chunk.iterrows()  # type: ignore
            ]
            connection.query(
                INSERT_WIKI_EMBEDDING_QUERY.substitute(
                    records=",\n ".join(formatted_rows)
                )
            )
            pbar.update(1)
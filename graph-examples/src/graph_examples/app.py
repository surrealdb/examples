"""Backend for SurrealDB chat interface."""

import contextlib
import datetime
from collections.abc import AsyncGenerator
import fastapi
from surrealdb import AsyncSurreal,RecordID
from fastapi import responses, staticfiles, templating
from fastapi.exceptions import RequestValidationError

import uvicorn
import ast
from urllib.parse import urlencode

from graph_examples.helpers.constants import * 
from graph_examples.helpers import loggers     

from graph_examples.helpers.ux_helpers import *

from graph_examples.helpers.adv_data_handler import ADVDataHandler

from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from graph_examples.data_processing.process_adviser_firms import FIELD_MAPPING as firm_field_mapping


# Load configuration parameters
db_params = DatabaseParams()
args_loader = ArgsLoader("Handler",db_params)
args_loader.LoadArgs()

GRAPH_SIZE_LIMIT = 1000




templates = templating.Jinja2Templates(directory="templates")
templates.env.filters["extract_id"] = extract_id
templates.env.filters["convert_timestamp_to_date"] = convert_timestamp_to_date
templates.env.filters["extract_field_value"] = extract_field_value
templates.env.filters["format_url_id"] = format_url_id


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

    yield
    life_span.clear()


# Initialize FastAPI application
app = fastapi.FastAPI(lifespan=lifespan)
app.mount("/static", staticfiles.StaticFiles(directory="static"), name="static")




@app.get("/", response_class=responses.HTMLResponse)
async def index(request: fastapi.Request) -> responses.HTMLResponse:


    return templates.TemplateResponse("index.html", {
            "request": request })


@app.get("/firms", response_class=responses.HTMLResponse)
async def firms(request: fastapi.Request) -> responses.HTMLResponse:

    data_handler = ADVDataHandler(life_span["surrealdb"])
    firms = await data_handler.get_firms()
    return templates.TemplateResponse("firms.html", {
            "request": request,"firms":firms})



@app.get("/firms/{firm_id}", response_class=responses.HTMLResponse)
async def firm(request: fastapi.Request,firm_id: str) -> responses.HTMLResponse:

    data_handler = ADVDataHandler(life_span["surrealdb"])
    firm = await data_handler.get_firm(firm_id)
    return templates.TemplateResponse("firm.html", {
            "request": request,"firm":firm,
            "field_mapping": firm_field_mapping})


@app.get("/firms/{firm_id}/people/{full_name}", response_class=responses.HTMLResponse)
async def person(request: fastapi.Request,firm_id: str,full_name: str) -> responses.HTMLResponse:

    data_handler = ADVDataHandler(life_span["surrealdb"])
    full_name = unformat_url_id(full_name)
    person = await data_handler.get_person(firm_id,full_name)
    return templates.TemplateResponse("person.html", {
            "request": request,"person":person})




@app.get("/people", response_class=responses.HTMLResponse)
async def people(request: fastapi.Request) -> responses.HTMLResponse:
    data_handler = ADVDataHandler(life_span["surrealdb"])
    people = await data_handler.get_people()
    return templates.TemplateResponse("people.html", {
            "request": request,"people":people})

@app.get("/filings", response_class=responses.HTMLResponse)
async def filings(request: fastapi.Request) -> responses.HTMLResponse:

    data_handler = ADVDataHandler(life_span["surrealdb"])
    filings = await data_handler.get_filings()
    return templates.TemplateResponse("filings.html", {
            "request": request,"filings":filings})



@app.get("/filings/{filing_id}", response_class=responses.HTMLResponse)
async def filing(request: fastapi.Request,filing_id: int) -> responses.HTMLResponse:

    data_handler = ADVDataHandler(life_span["surrealdb"])
    filing = await data_handler.get_filing(filing_id)
    return templates.TemplateResponse("filing.html", {
            "request": request,"filing":filing})


@app.get("/graph", response_class=responses.HTMLResponse)
async def graph(request: fastapi.Request,filing_id: int) -> responses.HTMLResponse:

    data_handler = ADVDataHandler(life_span["surrealdb"])
    graph_data = await data_handler.get_custodian_graph()
    ux_graph_data  = convert_adv_custodian_graph_to_ux_data(graph_data)
    return templates.TemplateResponse("graph.html", {
            "request": request,"graph_data":ux_graph_data})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: fastapi.Request, exc: RequestValidationError):
	exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
	#logging.error(f"{request}: {exc_str}")
	content = {'status_code': 10422, 'message': exc_str, 'data': None}
	return JSONResponse(content=content, status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY)



def run_app():
    uvicorn.run("__main__:app", host="0.0.0.0", port=8082, reload=True)
    # uvicorn.run(
    #     "__main__:app",  reload=True
    # )


if __name__ == "__main__":
    run_app()
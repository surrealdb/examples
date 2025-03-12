"""Download OpenAI Wikipedia data."""

import zipfile

import wget
import os

from surrealdb_rag import loggers

import surrealdb_rag.constants as constants

from surrealdb_rag.embeddings import WordEmbeddingModel

import pandas as pd
import tqdm
import datetime

from surrealdb_rag.constants import DatabaseParams, ModelParams, ArgsLoader, SurrealParams

import csv
from bs4 import BeautifulSoup
import ast

import edgar

# Initialize database and model parameters, and argument loader
db_params = DatabaseParams()
model_params = ModelParams()
args_loader = ArgsLoader("Download SEC data with edgar",db_params,model_params)

#https://pypi.org/project/sec-api/
# gen an api key here https://sec-api.io/profile

def extract_text_from_html(html_content):
    """
    Extracts text content from an HTML 10-K filing, mimicking browser rendering.

    Args:
        html_content (str): The HTML content of the 10-K filing.

    Returns:
        str: The extracted text content, with HTML tags removed and basic formatting preserved.
    """
    soup = BeautifulSoup(html_content, 'html.parser')  # Parse the HTML

    # 1. Extract text from the <body> tag (most content is here)
    body_text = soup.body.get_text(separator='\n', strip=True)
    # separator='\n' puts a newline between different block-level elements, improving readability
    # strip=True removes leading/trailing whitespace

    # 2. (Optional but Recommended) Further refine by focusing on main content areas
    # 10-Ks often have header/footer and navigation that you might want to exclude.
    # You might need to inspect the HTML of a few 10-Ks to identify consistent
    # container divs or sections that hold the main content.
    # For example, if you find a main content div with a specific ID or class, you could do:
    # main_content_div = soup.find('div', {'id': 'document'}) # Example ID, inspect your HTML
    # if main_content_div:
    #     body_text = main_content_div.get_text(separator='\n', strip=True)
    # else:
    #     body_text = soup.body.get_text(separator='\n', strip=True) # Fallback to body if main content not found

    # 3. (Optional) Handle Tables more explicitly (if needed for your NLP tasks)
    # If tables are important and you want to preserve their structure somewhat, you could:
    table_texts = []
    for table in soup.find_all('table'):
        table_text = ""
        for row in table.find_all('tr'):
            row_text = " | ".join([cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])])
            table_text += row_text + "\n"
        table_texts.append(table_text)
    body_text += "\n\n" + "\n\n".join(table_texts) # Add table text back in, separated

    return body_text

def file_name_from_url(url:str):
    return url.replace("https://","").replace("http://","").replace(".","_").replace("/","_")

def process_filing(filing:edgar.Filing,dict_writer:csv.DictWriter):

    try:
        #get the company for more details
        company = edgar.Company(filing.cik)
        file_path = f"{constants.EDGAR_FOLDER}{file_name_from_url(filing.filing_url)}.txt"
        if not os.path.exists(file_path):
            html_file = filing.html()
            text_content = extract_text_from_html(html_file)
            with open(file_path, "w") as f:
                f.write(text_content)

        row = {
            "url":filing.filing_url,
            "company_name":filing.company,
            "cik":filing.cik,
            "form":filing.form,
            "accession_no":filing.accession_no,
            "company.ticker_display":company.ticker_display,
            "company.description":company.description,
            "company.category":company.category,
            "company.industry":company.industry,
            "company.website":company.website,
            "filing_date":filing.filing_date,
            "file_path":file_path,
        }
        dict_writer.writerow(row)
        return row
    except:
        row = {
            "url":"error",
            "company_name":"",
            "cik":"",
            "form":"",
            "accession_no":"",
            "company.ticker_display":"",
            "company.description":"",
            "company.category":"",
            "company.industry":"",
            "company.website":"",
            "filing_date":"",
            "file_path":""}
        dict_writer.writerow(row)
        return row



# def filter(self, *,

#         :param form: The form or list of forms to filter by
#         :param amendments: Whether to include amendments to the forms e.g. include "10-K/A"
#         :param filing_date: The filing date
#         :param date: An alias for the filing date
#         :param cik: The CIK or list of CIKs to filter by
#         :param exchange: The exchange or list of exchanges to filter by
#         :param ticker: The ticker or list of tickers to filter by
#         :param accession_number: The accession number or list of accession numbers to filter by

def download_edgar_data() -> None:
    
    logger = loggers.setup_logger("DownloadData")
    
#     tickers = [
#     # --- Mega-Cap Tech & Core AI Players (Expanding on previous list) ---
#     "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "TSLA", "NVDA", "META", "TSM", "AVGO",
#     "ADBE", "CRM", "ORCL", "INTC", "QCOM", "IBM", "TXN", "AMD", "MU", "DELL",
#     "HPQ", "CSCO", "SAP", "ACN", "INFY", "WIT", "NTES", "SNPS", "CDNS", "KLAC",
#     "LRCX", "ASML", "AMAT", "ADI", "MCHP", "NXPI", "ON", "SWKS", "QRVO", "XLNX", # Semiconductor Expansion
#     "COUP", "WDAY", "SNOW", "DDOG", "ZS", "CRWD", "OKTA", "PANW", "FTNT", "CHKP", # Software & Cybersecurity with AI
#     "SHOP", "SQ", "PYPL", "MELI", "SE", "GDDY", "EBAY", "DOCU", "ADSK", "ANSS",  # E-commerce, Fintech, Design Software using AI
#     "UBER", "LYFT", "GRAB", "CPNG", "JD", "BABA", "PDD", "BIDU", "TCEHY", "DOYU", # Mobility, Chinese Tech & E-commerce (AI in China is massive)
#     "CRM", "NOW", "WORK", "ZS", "OKTA", "DOCU", "ADSK", "ANSS", "SPLK", "MDB",  # Enterprise Software & Cloud AI
#     "RBLX", "U", "TTWO", "ATVI", "EA", "NTDOY", "SONY", "MSI", "CTSH", "DXC",   # Gaming, IT Services, System Integration
#     "ERIC", "NOK", "KEYS", "TEL", "APH", "TE", "FFIV", "JNPR", "CIEN", "VIAV",   # Telecom Infrastructure, Networking (5G, AI at Edge)
#     "ABB", "SIEMENS", "HON", "GE", "MMM", "ROK", "EMR", "IRM", "TYL", "PTC",      # Industrial Automation, Manufacturing, Smart Industry with AI
#     "GOOG", "GOOGL", "MSFT", "AMZN", "IBM", "ORCL", "SNOW", "DDOG", "ZS", "MDB",  # Cloud Infrastructure & Data Management (Repeat some cloud names for emphasis)
#     "CRM", "ADBE", "NOW", "WDAY", "SHOP", "SQ", "PYPL", "MELI", "SE", "GDDY",     # AI Applications in SaaS and Business Software (Repeat some SaaS names)

#     # --- AI Specific Companies & Robotics ---
#     "AI",   # C3.ai, Inc. - pure-play AI software
#     "PLTR", # Palantir Technologies Inc. - Data analytics & AI for government/enterprise
#     "UIP",  # UiPath Inc. - Robotic Process Automation (RPA) - related to AI
#     "PATH", # UiPath Inc. (duplicate - keeping both in case of ticker variations)
#     "ABBY", # Abbyy - Intelligent Process Automation - OCR, related to AI
#     "BLUE", # blueprism - Robotic Process Automation - RPA - related to AI
#     "MNDY", # Monday.com - Work OS with AI features
#     "SMCI", # Super Micro Computer, Inc. - Server hardware for AI/ML workloads
#     "ARMH", # Arm Holdings plc - Chip designs crucial for mobile and AI
#     "INTU", # Intuit Inc. - Financial software with AI (TurboTax, QuickBooks)
#     "FICO", # Fair Isaac Corporation - Credit scoring, analytics, AI in finance
#     "CPAY", # Corpore Pay - Payments processing with AI for fraud detection
#     "COHR", # Coherent Corp. - Lasers and photonics (components for AI systems)
#     "IONQ", # IonQ, Inc. - Quantum Computing (future of certain AI types)
#     "LIDR", # AEye, Inc. - LiDAR sensors for autonomous vehicles and robotics
#     "LAZR", # Luminar Technologies, Inc. - LiDAR sensors for autonomous vehicles
#     "VLDR", # Velodyne Lidar, Inc. - LiDAR sensors (another lidar company)
#     "RBRK", # SPDR S&P
#  #Global Robotics and Automation ETF (ticker for Robotics ETF itself, can look at holdings)
#     "BOTZ", # Global X Robotics & Artificial Intelligence ETF (ticker for AI/Robotics ETF itself, can check holdings)
#     "ROBO", # ROBO Global Robotics and Automation Index ETF (another Robotics ETF)
#     "ARKQ", # ARK Autonomous Technology & Robotics ETF (ARK Innovation focused on disruptive tech including AI)
#     "XAI",  # Global X Artificial Intelligence ETF (Pure AI ETF ticker)
#     "AIQ",  # Global X AI & Big Data ETF (AI and Big Data focused ETF)
#     "CTEC", # Global X Future Analytics Tech ETF (Analytics, data, AI)
#     "IRBO", # iShares Robotics and Artificial Intelligence ETF (Another major Robotics/AI ETF)

#     # ---  Chinese AI & Tech (Important for global AI landscape) ---
#     "BABA", # Alibaba Group Holding Ltd - E-commerce, Cloud, AI in China
#     "BIDU", # Baidu, Inc. - Search Engine, AI leader in China
#     "TCEHY",# Tencent Holdings Ltd - Gaming, Social Media, AI in China
#     "JD",   # JD.com, Inc. - E-commerce, Logistics, AI in China
#     "PDD",  # PDD Holdings Inc. (Pinduoduo) - E-commerce, AI for personalization
#     "XPEV", # XPeng Inc. - Electric Vehicles, Autonomous Driving (Chinese EV maker)
#     "NIO",  # NIO Inc. - Electric Vehicles, Autonomous Driving (Chinese EV maker)
#     "LI",   # Li Auto Inc. - Electric Vehicles, Autonomous Driving (Chinese EV maker)
#     "BYDDY",# BYD Co. Ltd. - Electric Vehicles, Batteries, AI in automotive (Chinese giant)
#     "0700.HK", # Tencent (Hong Kong Ticker - if your data source needs it)
#     "9988.HK", # Alibaba (Hong Kong Ticker - if needed)

#     # ---  Semiconductor Companies (Detailed List) ---
#     "NVDA", "TSM", "AVGO", "QCOM", "INTC", "TXN", "AMD", "MU", "ADI", "MCHP", "NXPI", "ON", "SWKS", "QRVO", "ASML",
#     "AMAT", "LRCX", "KLAC", "TER", "KLA", "COHR", "IPGP", "MKS", "VECO", "ENTEG", "UCTT", "MKSI", "ACMR", "AXTI",  # Broad range of semi equipment and materials
#     "SOXX", # iShares PHLX Semiconductor ETF (Ticker for the ETF itself - can check holdings)
#     "SMH",  # VanEck Semiconductor ETF (another major Semi ETF)


#     # --- Cloud Computing Companies (Detailed List) ---
#     "AMZN", "MSFT", "GOOGL", "GOOG", "IBM", "ORCL", "SNOW", "DDOG", "ZS", "MDB", # Core Cloud Providers (Repeating some for emphasis)
#     "CRM",  "NOW",  "WDAY", "ADBE", "SAP",  "VMW", "CTSH", "INFY", "WIT", "FTNT", # Cloud Software & Services
#     "AKAM", "CDK", "FSLY", "NET",  "VRSN", "EQIX", "DLR",  "AMT",  "CCI", "SBAC", # Cloud Infrastructure, CDN, Data Centers (Some REITs included)
#     "WCLD", # WisdomTree Cloud Computing Fund (Ticker for Cloud ETF itself)
#     "SKYY", # First Trust Cloud Computing ETF (Another Cloud ETF)
#     "CLOU", # Global X Cloud Computing ETF (Yet another Cloud ETF)
#     "PAGS", # PagSeguro Digital Ltd. - Fintech/Payments Cloud-based
#     "MELI", # MercadoLibre, Inc. - E-commerce/Fintech Cloud-based

#     # ---  Data Analytics & Big Data Companies (Fueling AI) ---
#     "SNOW", "DDOG", "MDB", "PLTR", "FICO", "SPLK", "Qlik", "SNPS", "CDNS", "ANSS", # Analytics Platforms & Tools (Repeating some analytics-heavy names)
#     "ADBE", "CRM", "ORCL", "SAP", "WDAY", "NOW", "INTU", "ACN", "IBM", "GOOGL", # Enterprise Software & Cloud with Data Focus
#     "GDDY", "EBAY", "SHOP", "SQ", "PYPL", "MELI", "SE", "GRAB", "CPNG", "JD",     # Data-rich E-commerce & Fintech
#     "TWTR", "SNAP", "PINS", "MTCH", "BMBL", "SPOT", "NFLX", "DIS", "ROKU", "TTWO", # Social Media, Entertainment, Content - Data Generators
#     "DOCN", "TDOC", "LVGO", "AMWL", "ZM",   # Telehealth & Remote work platforms - Data from interactions
#     "IOT",  # Samsara Inc. - IoT & Industrial Data Analytics

#     # --- (Optional - Add more specific AI application areas if needed, e.g., Biotech/Pharma AI, etc.) ---

#     # --- Add some Major Consulting/IT Services firms involved in AI implementation ---
#     "ACN", "INFY", "WIT", "CTSH", "IBM", "G", "KYND", "DXC", "CAP", "EPAM" # IT Services firms helping enterprises adopt AI

#     ]


    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=30) # Roughly one year ago, can be more precise if needed

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    form_str = "10-K,13F-HR,SC 13D,SC 13G,S-1,S-4"
    ticker_str = ""


    args_loader.AddArg("start_date","edsd","start_date","Start filing date in format '%Y-%m-%d'. (default{0})",start_date_str)
    args_loader.AddArg("end_date","eded","end_date","End filing date in format '%Y-%m-%d'. (default{0})",end_date_str)
    args_loader.AddArg("form","edf","form","Form type to download can be an array in format '10-K,13F-HR,SC 13D,SC 13G,S-1,S-4'. (default{0})",form_str)
    args_loader.AddArg("ticker","tic","ticker","Tickers to download can be an array in format 'AAPL,MSFT,AMZN' leave blank for all tickers. (default{0})",ticker_str)
    


    start_date = datetime.datetime.strptime(args_loader.AdditionalArgs["start_date"]["value"], '%Y-%m-%d')
    end_date = datetime.datetime.strptime(args_loader.AdditionalArgs["end_date"]["value"], '%Y-%m-%d')
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    if args_loader.AdditionalArgs["form"]["value"]:
        form_str = args_loader.AdditionalArgs["form"]["value"]
   
    if args_loader.AdditionalArgs["ticker"]["value"]:
        ticker_str = args_loader.AdditionalArgs["form"]["value"]

    if ticker_str: 
        ticker = ticker_str.split(",")
    else:
        ticker = []
    form = form_str.split(",")
    
    args_loader.LoadArgs()
    logger.info(args_loader.string_to_print())

    # make sure to add env var to ensure SEC doesn't block you
    #export EDGAR_IDENTITY="email@domain.com"

    logger.info(f"Ensuring folder {constants.EDGAR_FOLDER}")

    if not os.path.exists(constants.EDGAR_FOLDER):
        os.makedirs(constants.EDGAR_FOLDER)


    logger.info(f"Downloading {form} filings for {start_date_str} to {end_date_str}")
    filings = edgar.get_filings(form=form,filing_date=f"{start_date_str}:{end_date_str}")
    if len(ticker)>0:
        filings = filings.filter(ticker=ticker)

    file_keys = {
        "url":"",
        "company_name":"",
        "cik":"",
        "form":"",
        "accession_no":"",
        "company.ticker_display":"",
        "company.description":"",
        "company.category":"",
        "company.industry":"",
        "company.website":"",
        "filing_date":"",
        "file_path":""}.keys()
    with open(constants.EDGAR_FOLDER_FILE_INDEX,"w", newline='') as f:
        dict_writer = csv.DictWriter(f, file_keys)
        dict_writer.writeheader()
        for filing in tqdm.tqdm(filings, desc="Processing filings"):
            process_filing(filing,dict_writer)

    logger.info("Extracted file successfully. Please check the data directory")

if __name__ == "__main__":
    download_edgar_data()
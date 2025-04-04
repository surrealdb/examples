import requests

from bs4 import BeautifulSoup
import zipfile
import io
import os
import re
from urllib.parse import urljoin
from graph_examples.helpers.constants import * 
from graph_examples.helpers import loggers     
import tqdm
import time 

MAX_REQUESTS_PER_SECOND = 4
THROTTLE_TIME_SECONDS = 1 / MAX_REQUESTS_PER_SECOND
# Define more comprehensive headers
BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br", # requests handles decompression
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


        

def download_and_extract_zip_file(logger, session: requests.Session, url:str, target_dir:str) -> None:
    time.sleep(THROTTLE_TIME_SECONDS) # Sleep to avoid overwhelming the server
    response = session.get(url, stream=True, timeout=90) # Increased timeout
    response.raise_for_status()  # Check for download errors (4xx or 5xx)

    try:
    # Check content type if possible, although zip might be application/zip or octet-stream
        content_type = response.headers.get('Content-Type', '').lower()
        logger.debug(f"    Content-Type: {content_type}")
        if 'zip' not in content_type and 'octet-stream' not in content_type:
             logger.warning(f"    Unexpected Content-Type '{content_type}' for URL {url}. Expected zip.")
             # Decide if you want to proceed anyway or return

        # Use BytesIO to handle the zip content in memory
        with io.BytesIO(response.content) as zip_buffer:
            # Check if the buffer is actually a zip file before proceeding
            if not zipfile.is_zipfile(zip_buffer):
                logger.error(f"  Error: Content downloaded from {url} is not a valid zip file.")
                # Attempt to log the first few bytes or text if possible for debugging
                try:
                    zip_buffer.seek(0)
                    preview = zip_buffer.read(500)
                    logger.error(f"    Content preview (first 500 bytes): {preview}")
                except Exception as preview_err:
                    logger.error(f"    Could not get content preview: {preview_err}")
                return # Stop processing

            # Proceed with extraction
            zip_buffer.seek(0) # Rewind buffer after is_zipfile check
            with zipfile.ZipFile(zip_buffer) as zf:
                extracted_count = 0
                # ... (extraction logic remains the same as your previous version) ...
                for filename in zf.namelist():
                    # logger.info(f"    Extracting '{filename}' to {target_dir}")
                    ensure_dir(target_dir)
                    try:
                        zf.extract(filename, path=target_dir)
                        source_path = os.path.join(target_dir, filename)
                        dest_path = os.path.join(target_dir, os.path.basename(filename))

                        if source_path != dest_path:
                            if os.path.exists(dest_path):
                                logger.warning(f"      Overwriting existing file: {dest_path}")
                                os.remove(dest_path)
                            os.rename(source_path, dest_path)
                            try:
                                os.rmdir(os.path.dirname(source_path))
                            except OSError:
                                    pass # Dir not empty or doesn't exist
                        extracted_count += 1
                    except Exception as extract_err:
                        logger.error(f"      Error extracting file {filename}: {extract_err}")

                if extracted_count == 0:
                     logger.warning(f"    No files matching specified patterns found or extracted from {url}.")


    except requests.exceptions.HTTPError as e:
        logger.error(f"  HTTP Error downloading {url}: {e.response.status_code} {e.response.reason}")
        # Log response body if it's a 403 or similar client error, might contain clues
        if 400 <= e.response.status_code < 500:
             logger.error(f"  Response body (preview): {e.response.text[:500]}...") # Log first 500 chars
    except requests.exceptions.ConnectionError as e:
        logger.error(f"  Connection Error downloading {url}: {e}")
    except requests.exceptions.Timeout as e:
        logger.error(f"  Timeout downloading {url}: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"  Error downloading {url}: {e}")
    except zipfile.BadZipFile:
        logger.error(f"  Error: Downloaded content from {url} appears corrupt or not a zip file after download.")
    except Exception as e:
        logger.error(f"  An unexpected error occurred processing {url}: {e}")

def download_and_extract_zip_files(logger, session: requests.Session, referer_url:str, links:list[str], destination_folder:str) -> None:
    
    headers = session.headers.copy() # Get base headers from session
    headers['Referer'] = referer_url
    session.headers.update(headers) # Update session headers
    for link in tqdm.tqdm(links, desc="Downloading zip files"):
        download_and_extract_zip_file(logger, session, link, destination_folder)



def process_page_links(logger,session: requests.Session, url:str, pattern:re, destination_folder:str, max_links:int=12) -> None:
    ensure_dir(destination_folder)
    time.sleep(THROTTLE_TIME_SECONDS) # Sleep to avoid overwhelming the server
    response = session.get(url, timeout=30) # No need to pass headers explicitly now
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    links = []
    num_links = 0
    all_links = soup.find_all('a', href=re.compile(pattern, re.IGNORECASE))
    for link in all_links:
        href = link.get('href')
        full_url = urljoin(url, href)
        if full_url not in links:
            links.append(full_url)
            num_links += 1
            if num_links >= max_links:
                break
    if not links:
        logger.warning(f"  Could not find any zip file links on the page: {url}")
    else:
        download_and_extract_zip_files(logger, session,url, links, destination_folder)


def download_adv_data() -> None:
    logger = loggers.setup_logger("DownloadData") # Use your logger setup

    logger.info("Starting SEC data download process...")
    ensure_dir(BASE_OUTPUT_DIR)

    # Create a session object to persist cookies and headers
    session = requests.Session()
    headers = BASE_HEADERS.copy() 
    identity = os.environ.get("EDGAR_IDENTITY")
    if identity is None:
        raise Exception("User-Agent identity is not set in environment variables. Add EDGAR_IDENTITY with your email address.")
    headers["User-Agent"] = identity
    session.headers.update(headers) # Set base headers for the session




    # 1. Process FOIA Page for Part 1 Data
    logger.info(f"\nProcessing FOIA Part 1 data from: {FOIA_DATA_PAGE}#part1")
    pattern = r"adv[-_]filing[-_]data.*\.zip"
    process_page_links(logger,session, FOIA_DATA_PAGE, pattern, PART1_DIR)


    # 2. Process Adviser Data Page for Master Feed
    logger.info(f"\nProcessing Master Adviser Feed from: {ADVISER_DATA_PAGE}")
    pattern = r"ia.*\.zip"
    process_page_links(logger,session, ADVISER_DATA_PAGE, pattern, INVESTMENT_ADVISER_FIRMS_DIR,2)



# --- Main execution block ---
if __name__ == "__main__":
    download_adv_data()
# --- End main execution block ---
import requests
import xml.etree.ElementTree as ET
import csv
import time

def download_adv_filing(cik_number, filing_year):
    """Downloads a Form ADV filing for a given CIK number and year."""
    base_url = "https://www.sec.gov/Archives/edgar/data"
    cik_padded = cik_number.zfill(10)
    url = f"{base_url}/{cik_padded}/{filing_year}/000XXXXXXX-YY-{filing_year}XXXXX.txt" # Placeholder URL - needs adjustment based on specific filing

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error downloading filing for CIK {cik_number} in {filing_year}: {e}")
        return None

def parse_adv_filing(filing_content):
    """Parses the Form ADV filing content (assuming XML format within the text)."""
    # This is a simplified example. Form ADV filings can have variations.
    try:
        # Find the XML part within the text filing
        xml_start = filing_content.find("<XML>")
        xml_end = filing_content.find("</XML>")
        if xml_start != -1 and xml_end != -1:
            xml_content = filing_content[xml_start + 5:xml_end]
            root = ET.fromstring(xml_content)
            return root
        else:
            print("XML content not found in the filing.")
            return None
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None

def extract_sma_data(root):
    """Extracts SMA related data from the parsed Form ADV XML root."""
    sma_data = {}

    # Look for Item 5.F (Regulatory Assets Under Management)
    raum_element = root.find('.//TOTAL_RAUM') # Adjust path based on actual XML structure
    if raum_element is not None and raum_element.text:
        sma_data['total_raum'] = raum_element.text

    # Look for Schedule D - Section 5.K (Separately Managed Accounts)
    sma_section = root.find('.//S5_K') # Adjust path based on actual XML structure
    if sma_section is not None:
        # Extract percentage of RAUM in SMAs
        percentage_sma_element = sma_section.find('.//PERCENTAGE_SMA') # Adjust path
        if percentage_sma_element is not None and percentage_sma_element.text:
            sma_data['percentage_of_raum_in_sma'] = percentage_sma_element.text

        # Extract asset category percentages (example for equity securities)
        equity_percentage_element = sma_section.find('.//EXCHANGE_TRADED_EQUITY_SECURITIES') # Adjust path
        if equity_percentage_element is not None and equity_percentage_element.text:
            sma_data['equity_sma_percentage'] = equity_percentage_element.text

        # You would need to add more logic to extract other asset categories
        # and information from Section 5.K.(2) and 5.K.(3) if needed.

    return sma_data

if __name__ == "__main__":
    cik = "0001049349"  # Example CIK number (replace with a real one)
    year = "2024"       # Example year

    filing_content = download_adv_filing(cik, year)

    if filing_content:
        xml_root = parse_adv_filing(filing_content)
        if xml_root is not None:
            sma_info = extract_sma_data(xml_root)
            print(f"SMA Data for CIK {cik} in {year}:")
            print(sma_info)

            # Example of writing to a CSV file
            with open('sma_data.csv', 'w', newline='') as csvfile:
                fieldnames = ['cik', 'year', 'total_raum', 'percentage_of_raum_in_sma', 'equity_sma_percentage'] # Add more fields as needed
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                sma_info['cik'] = cik
                sma_info['year'] = year
                writer.writerow(sma_info)

    # Be mindful of SEC's rate limiting policies when accessing EDGAR.
    # Add delays between requests if you are processing multiple filings.
    time.sleep(1)
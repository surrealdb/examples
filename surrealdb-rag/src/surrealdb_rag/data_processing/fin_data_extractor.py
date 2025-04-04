from bs4 import BeautifulSoup, NavigableString
import re

def extract_text_from_edgar_html(html_content, form_type):
    """
    Extracts text from Edgar HTML filings, focusing on relevant sections and improving table handling.

    This function parses HTML content from EDGAR filings, removes irrelevant tags (scripts, styles, etc.),
    and extracts text from key sections based on the filing's form type (10-K, 10-Q, SC 13D, etc.).
    It includes enhanced logic to process HTML tables into natural language sentences.

    Args:
        html_content (str): The HTML content of the EDGAR filing.
        form_type (str): The type of the filing (e.g., "10-K", "10-Q", "S-1").

    Returns:
        str: The extracted and processed text from the filing.
    """
    soup = BeautifulSoup(html_content, 'lxml')

    for tag in soup.find_all(['script', 'style', 'head', 'meta', 'img']):
        tag.decompose()

    relevant_text = []
    if form_type.upper() in ("10-K", "10-Q"):
        sections_to_find = [  # ... (Same list as before) ...
            "item 1\. business", "item 1a\. risk factors", "item 1b\. unresolved staff comments",
            "item 2\. properties", "item 3\. legal proceedings",
            "item 4\. mine safety disclosures",
            "item 5\. market for registrant’s common equity, related stockholder matters and issuer purchases of equity securities",
            "item 6\. \[reserved\]",
            "item 7\. management’s discussion and analysis of financial condition and results of operations",
            "item 7a\. quantitative and qualitative disclosures about market risk",
            "item 8\. financial statements and supplementary data",
            "item 9\. changes in and disagreements with accountants on accounting and financial disclosure",
            "item 9a\. controls and procedures",
            "item 9b\. other information",
            "item 9b\. disclosure regarding foreign jurisdictions that prevent inspections",
            "item 10\. directors, executive officers and corporate governance",
            "item 11\. executive compensation",
            "item 12\. security ownership of certain beneficial owners and management and related stockholder matters",
            "item 13\. certain relationships and related transactions, and director independence",
            "item 14\. principal accountant fees and services",
            "part i",
            "part ii",
            "part iii",
            "part iv", ]

        for i in range(len(sections_to_find)):
          start_section = sections_to_find[i]
          start_tag = find_section(soup, start_section)

          if start_tag:
            end_tag_text = sections_to_find[i + 1] if i + 1 < len(sections_to_find) else None
            section_text = extract_text_between(start_tag, end_tag_text)  # Use updated extract_text_between
            relevant_text.append(section_text)

    elif form_type.upper() in ("SC 13D", "SC 13G"):
        items_to_find = [
            "item 1\. security and issuer",
            "item 2\. identity and background",
            "item 3\. source and amount of funds or other consideration",
            "item 4\. purpose of transaction",
            "item 5\. interest in securities of the issuer",
            "item 6\. contracts, arrangements, understandings or relationships with respect to securities of the issuer",
            "item 7\. material to be filed as exhibits",
            "signature"
        ]
        for i in range(len(items_to_find)):
          start_item = items_to_find[i]
          start_tag = find_section(soup, start_item)
          if start_tag:
            end_tag_text = items_to_find[i+1] if i + 1 < len(items_to_find) else None
            item_text = extract_text_between(start_tag, end_tag_text)
            relevant_text.append(item_text)

    elif form_type.upper() in ("S-1", "S-4"):
        common_headings = [
            "summary",
            "risk factors",
            "use of proceeds",
            "dividend policy",
            "capitalization",
            "dilution",
            "selected financial data",
            "management’s discussion and analysis",
            "business",
            "management",
            "certain relationships and related transactions",
            "principal stockholders",
            "description of securities",
            "underwriting",
            "legal matters",
            "experts",
            "where you can find more information",
            "incorporation of certain information by reference",
        ]
        for heading in common_headings:
          start_tag = find_section(soup, heading)
          if start_tag:
            next_heading_index = common_headings.index(heading) + 1
            end_tag_text = common_headings[next_heading_index] if next_heading_index < len(common_headings) else None
            section_text = extract_text_between(start_tag, end_tag_text)
            relevant_text.append(section_text)

    all_paragraphs = []
    for p_tag in soup.find_all('p'):
        paragraph_text = p_tag.get_text(separator=" ", strip=True)
        if paragraph_text:
            all_paragraphs.append(paragraph_text)

    combined_text = "\n\n".join(relevant_text)
    for paragraph in all_paragraphs:
        if paragraph not in combined_text:
           combined_text += "\n" + paragraph

    combined_text = re.sub(r'\s+', ' ', combined_text)
    combined_text = combined_text.strip()
    return combined_text


def find_section(soup_obj, section_start):
    """
    Finds the starting tag of a section within the BeautifulSoup object.

    This function searches for a tag that contains the section start text, considering various tag types
    (string, <b>, <span>, <p>) and case-insensitivity.

    Args:
        soup_obj (BeautifulSoup): The BeautifulSoup object representing the HTML.
        section_start (str): The text that marks the beginning of the section.

    Returns:
        bs4.element.Tag or None: The starting tag of the section, or None if not found.
    """
    section_start_lower = section_start.lower()
    start_tag = soup_obj.find(string=re.compile(r'^\s*' + re.escape(section_start_lower), re.IGNORECASE))
    if start_tag:
        return start_tag
    start_tag = soup_obj.find('b', string=re.compile(r'^\s*' + re.escape(section_start_lower), re.IGNORECASE))
    if start_tag:
        return start_tag
    for span in soup_obj.find_all('span'):
        if span.get('style') and 'font-weight' in span.get('style').lower() and 'bold' in span.get('style').lower():
            if re.search(r'^\s*' + re.escape(section_start_lower), span.get_text(), re.IGNORECASE):
                return span
    start_tag = soup_obj.find('p', string=re.compile(r'^\s*' + re.escape(section_start_lower), re.IGNORECASE))
    if start_tag:
        return start_tag
    return None

def extract_text_between(start_tag, end_tag_text=None):
    """
    Extracts text from the HTML between a starting tag and an optional ending tag/text.

    This function iterates through the tags following the start tag, extracting text and handling tables.
    It stops when it encounters the end_tag_text (if provided) or reaches the end of the document.

    Args:
        start_tag (bs4.element.Tag): The tag where the extraction should begin.
        end_tag_text (str, optional): The text that indicates the end of the extraction. Defaults to None.

    Returns:
        str: The extracted text.
    """
    if not start_tag:
        return ""

    extracted_text = []
    current_tag = start_tag.find_next()

    while current_tag and (end_tag_text is None or not current_tag.find(string=re.compile(end_tag_text, re.IGNORECASE))):
        if isinstance(current_tag, NavigableString):
            extracted_text.append(current_tag.strip())
        elif current_tag.name == 'table':
            # Improved Table Handling
            table_sentences = process_table_to_sentences(current_tag)
            extracted_text.extend(table_sentences)
        current_tag = current_tag.find_next()

    return " ".join(extracted_text)

def process_table_to_sentences(table_tag):
    """
    Converts an HTML table to a list of natural language sentences.

    This function extracts data from the table, handling both tables with headers and those without.
    It also performs basic cleanup of number and currency formatting.

    Args:
        table_tag (bs4.element.Tag): The <table> BeautifulSoup tag.

    Returns:
        list[str]: A list of sentences representing the table's content.
    """
    sentences = []
    rows = table_tag.find_all('tr')
    if not rows:
        return sentences

    # 1. Try to Extract Headers (if they exist and are reasonably formatted)
    header_row = rows[0]
    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
    has_headers = len(headers) > 0

    # 2. Process Data Rows
    for row in rows[1 if has_headers else 0:]:  # Skip header row if we found headers
        cells = [td.get_text(strip=True) for td in row.find_all('td')]

        if not cells: # Skip if empty row
          continue

        # --- Simple Strategy (Suitable for many tables) ---
        if has_headers and len(headers) == len(cells):
            # Create sentences like "Header1: Cell1, Header2: Cell2, ..."
            sentence = ", ".join([f"{headers[i]}: {cells[i]}" for i in range(len(cells))])
            sentences.append(sentence)
        else:
            # If no headers, or header/cell count mismatch, just join cells with spaces.
            sentence = " ".join(cells)
            sentences.append(sentence)
    
    # 3. Number and Currency Handling
    #    - Replace $ signs with "USD " (or your currency of choice).
    final_sentences = []
    for sentence in sentences:
      sentence = re.sub(r'\$', 'USD ', sentence)      # Replace $ with "USD "
      sentence = re.sub(r'(\d),(\d)', r'\1\2', sentence) #9,941 --> 9941 remove commas within numbers.
      final_sentences.append(sentence)

    return final_sentences
# ADV Filing Graph Extractor and Firm Disambiguation Tool

This project provides tools for extracting, processing, and visualizing data from SEC ADV (Uniform Application for Investment Adviser Registration) filings. It specifically focuses on data points relevant to hedge funds, venture capital firms, banks, custodians, and technology providers. A core feature is the sophisticated firm name disambiguation pipeline using custom cleaning functions and a FastText embedding model to resolve inconsistencies and identify entities across different filing sections. The processed data is stored and queried using SurrealDB, leveraging its graph capabilities, and visualized through a web application.

## Key Capabilities

* **Targeted Data Extraction:** Scrapes and parses ADV filings from the SEC, focusing on:
    * **Section 7b1:** Separately Managed Account (SMA) details, highlighting assets managed by Hedge Funds and VCs (valuable for competitive analysis within the HF/VC community).
    * **Section 5k3:** SMA custodian information (primarily relevant for banks, custodians, and regulators monitoring market share and infrastructure).
    * **Schedule D (Books and Records):** Lists third-party service providers, including cloud hosting platforms like AWS and Snowflake (useful for technology firms tracking market adoption).
* **Advanced Firm Name Disambiguation:**
    * Implements a custom cleaning function (`fn::clean_company_string`) to normalize firm names by removing common jargon, geographic terms, punctuation, and standardizing initial formats (e.g., "J. P. Morgan" -> "JP MORGAN").
    * Trains a FastText (skipgram) embedding model specifically on the cleaned, distinct firm names found in the filings (`minn=2` to capture initials, `minCount=1` to ensure coverage).
    * Generates representative vectors for firms (`fn::firm_name_to_vector`) by averaging the embeddings of their constituent cleaned words.
    * Utilizes vector similarity search combined with a weighted string-similarity scoring function (`fn::firm_match_score`) considering legal name, common name, cleaned name, and geographic data (city, state, country) to accurately match firms across different sections, even with messy input data.
* **Knowledge Graph Construction:** Builds relationships within SurrealDB:
    * `is_compliance_officer`: Links firms to their compliance officers.
    * `signed`: Links filings to the signing officer.
    * `custodian_for`: Links firms (clients) to their custodians, capturing the type of relationship (Third-party, Affiliate, Other, Private Fund, RAUM).
    * `parent_firm`: Establishes hierarchical relationships between parent firms and subsidiaries based on name analysis.
* **Data Storage and Querying:** Leverages SurrealDB for efficient storage, graph traversal, and querying using semantic (vector), full-text, and filtered approaches.
* **Web-Based Visualization:**
    * Provides table views for structured data like asset holdings.
    * Enables hierarchical navigation of firm relationships.
    * Offers dynamic graph visualization (using VivaGraphJS) of the connections between entities (e.g., firms, custodians, officers).

## The Firm Name Challenge

A significant challenge with ADV data is the inconsistency in how firm names are reported, especially in free-text fields within sections like Schedule D. The master list of advisers provides relatively clean names but lacks parent-subsidiary links. Names extracted from other sections can be variations, include abbreviations, or miss legal identifiers. This project addresses this by:

1.  **Cleaning:** Applying a robust cleaning function to strip away noise and standardize name components.
2.  **Embedding:** Training a FastText model to learn semantic relationships between words and sub-words (like initials) specific to the financial domain context found in the filings.
3.  **Vectorization:** Representing each firm name as a numerical vector based on its cleaned components.
4.  **Matching:** Using efficient vector search to find likely candidates, followed by a fine-grained scoring function that blends vector similarity (implied) with weighted string comparisons across multiple fields (name, location) to confirm matches.

## Workflow & Processing Pipeline

The project follows a sequential processing pipeline executed by Python scripts:

1.  **Download Data (`process_1_download_adv_data.py`):** Scrapes the SEC website using Beautiful Soup to download ADV filing zip archives containing CSVs and XLS files.
2.  **Train Embedding Model (`process_2_train_firm_fast_text.py`):**
    * Extracts all firm names from various sections.
    * Applies the `fn::clean_company_string` function.
    * Trains a FastText model on the distinct cleaned names and saves the model.
3.  **Setup Database (`process_3_create_database.py`):** Initializes the SurrealDB schema, namespaces, and tables.
4.  **Insert Embedding Model (`process_4_insert_firm_ft_model.py`):** Loads the trained FastText word vectors into the `embeddings` table in SurrealDB for efficient lookup.
5.  **Load Master Firms (`process_5_insert_adviser_firms.py`):**
    * Inserts firms from the master adviser list.
    * Creates aliases for lookup (SEC number, legal name).
    * Populates the `is_compliance_officer` graph relationship.
6.  **Add Initial Indexes (`process_6_add_adv_firm_indexes.py`):** Creates indexes, including vector indexes, on the firm data to accelerate searching.
7.  **Load Base Filings (`process_7_insert_adv_base_a_filings.py`):**
    * Inserts core filing information, linking back to the master firms.
    * Populates the `signed` graph relationship.
8.  **Load Section D Data & Match (`process_8_a/b/c_*.py`):**
    * Processes Section 7b1 (HF/VC SMAs), 5k3 (Custodian SMAs), and Books & Records data.
    * For each firm mentioned in these sections:
        * Cleans the name.
        * Generates its vector using `fn::firm_name_to_vector`.
        * Performs a vector search in SurrealDB to find potential matches from the master list.
        * Applies the `fn::firm_match_score` function to score and confirm the best match above a threshold.
        * Inserts the data, linking to the matched firm or creating a new firm record if no suitable match is found (common for many custodians or service providers).
    * Populates the `custodian_for` graph relationship.
9.  **Consolidate Firms (`process_9_insert_firm_consolidation.py`):** Analyzes firm names (potentially using the cleaned strings) to identify and create `parent_firm` entities using reference records.
10. **Add Final Indexes (`process_10_add_adv_app_search_indexes.py`):** Creates additional indexes optimized for the application's search and exploration features.
11. **Launch Application (`app.py`):** Starts the FastAPI web server providing the UI for querying and visualizing the graph.

## Technology Stack

* **Backend:** FastAPI (Python)
* **Frontend:** Jinja2 (Templating), htmx (Dynamic HTML Interactivity)
* **Database:** SurrealDB (v2.2.x+ or Cloud) - Handles storage, graph relationships, vector search, and full-text search.
* **Data Processing:** Python, Beautiful Soup (Scraping), Pandas (Data Handling), FastText (Embeddings)

## Graph Relationships Created

* `(Firm)-[:is_compliance_officer]->(Person)`
* `(Filing)-[:signed]->(Person)`
* `(Firm)-[:custodian_for {type: string}]->(Firm)` (Where type is 'Third-party unaffiliated', 'Branch/Affiliate', 'Other', 'PF', 'RAUM')
* `(Firm)-[:parent]->(Firm)`

## Visualization

* **Tables:** Structured display of extracted data points.
* **Hierarchy Navigation:** Tree-like views to explore parent-subsidiary structures.
* **Dynamic Graph Visualization:** Interactive graph powered by VivaGraphJS showing connections between firms, custodians, and potentially officers.

## Setup

* **Hardware:** A machine with sufficient RAM and CPU for data processing (especially embedding training and vector indexing) and running SurrealDB.
* **SurrealDB:** Version 2.2.x or later or [SurrealDB Cloud](https://surrealdb.com/cloud). See [SurrealDB Installation](https://surrealdb.com/install).
* **Python:** Version 3.11 recommended.
* **Environment Variables:** Set these in your environment (e.g., `.bashrc`, `.zshrc`, `.env` file):
    ```bash
    SURREAL_ADV_USER=<SurrealDB username>
    SURREAL_ADV_PASS=<SurrealDB password>
    SURREAL_ADV_DB_URL=<SurrealDB connection URL (e.g., ws://localhost:8000 or wss://cloud_id.surreal.cloud)>
    SURREAL_ADV_DB_NS=<SurrealDB namespace (e.g., ADV_NS)>
    SURREAL_ADV_DB_DB=<SurrealDB database (e.g., ADV_DB)>
    ```

## Getting Started

1.  **Clone the repository:**
    ```bash
    git clone <your_repo_url>
    cd <your_repo_directory>
    ```

2.  **Set up Python environment and install dependencies:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt # Assuming you have a requirements.txt
    # Or if using setup.py/pyproject.toml:
    # pip install -e ./
    ```

3.  **Run the data processing pipeline scripts sequentially:**
    ```bash
    # 1. Download
    python src/graph_examples/data_processing/process_1_download_adv_data.py

    # 2. Train Embeddings
    python src/graph_examples/data_processing/process_2_train_firm_fast_text.py

    # 3. Setup DB Schema
    python src/graph_examples/data_processing/process_3_create_database.py --url_env SURREAL_ADV_DB_URL --user_env SURREAL_ADV_USER --pass_env SURREAL_ADV_PASS --namespace_env SURREAL_ADV_DB_NS --database_env SURREAL_ADV_DB_DB # Pass args or rely on defaults

    # 4. Insert Embedding Model into DB
    python src/graph_examples/data_processing/process_4_insert_firm_ft_model.py # Args as above

    # 5. Insert Master Adviser Firms & Compliance Officers
    python src/graph_examples/data_processing/process_5_insert_adviser_firms.py # Args as above

    # 6. Add Vector & Other Indexes
    python src/graph_examples/data_processing/process_6_add_adv_firm_indexes.py # Args as above

    # 7. Insert Base Filings & Signers
    python src/graph_examples/data_processing/process_7_insert_adv_base_a_filings.py # Args as above

    # 8. Insert Section D data (matching firms using embeddings)
    python src/graph_examples/data_processing/process_8_a_insert_adv_schedule_d_7b1_s.py # Args as above
    python src/graph_examples/data_processing/process_8_b_insert_adv_schedule_d_5k3_s.py # Args as above
    python src/graph_examples/data_processing/process_8_c_insert_adv_schedule_d_books_records.py # Args as above

    # 9. Create Parent-Child Firm Links
    python src/graph_examples/data_processing/process_9_insert_firm_consolidation.py # Args as above

    # 10. Add Final Application Search Indexes
    python src/graph_examples/data_processing/process_10_add_adv_app_search_indexes.py # Args as above
    ```
    *Note: Ensure the script arguments (for DB connection etc.) are passed correctly, either via command line flags or by relying on the environment variables being picked up within the scripts.*

4.  **Launch the web application:**
    ```bash
    python src/graph_examples/app.py
    ```
    Access the application in your browser (typically `http://localhost:8082` or as configured).

## Key Libraries

* **FastAPI:** Modern web framework for building APIs.
* **Jinja2:** Templating engine for generating HTML.
* **htmx:** Enables dynamic front-end interactions without complex JavaScript.
* **SurrealDB (Client):** Python library for interacting with SurrealDB.
* **Beautiful Soup:** Library for parsing HTML/XML, used for scraping.
* **Pandas:** Data manipulation and analysis library.
* **FastText:** Library for efficient text classification and representation learning (word embeddings).

## UI Libraries

* **Lightpick:** Lightweight date range picker. [https://wakirin.github.io/Lightpick/](https://wakirin.github.io/Lightpick/)
* **VivaGraphJS:** Library for graph drawing and visualization. [https://github.com/anvaka/VivaGraphJS/](https://github.com/anvaka/VivaGraphJS/)

## Acknowledgments

* (Thanks to Andrey)
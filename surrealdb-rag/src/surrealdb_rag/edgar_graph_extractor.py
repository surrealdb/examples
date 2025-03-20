import edgar.company
import spacy
from tqdm import tqdm
from surrealdb_rag import loggers  
import surrealdb_rag.constants as constants
import pandas as pd
from surrealdb_rag.constants import DatabaseParams, ModelParams, ArgsLoader, SurrealParams
from surrealdb_rag.embeddings import WordEmbeddingModel
import csv
import ast
import spacy
import tqdm
import spacy
spacy.require_gpu()
import os
import edgar
from fuzzywuzzy import fuzz, process
import unicodedata
import re
from surrealdb_rag.embeddings import WordEmbeddingModel


def fuzzy_merge_people(nlp, people_list, threshold=85):
    """
    Merges similar person entities using fuzzy matching and alias handling.
    Creates a primary key based on the longest, most descriptive name.
    """
    merged_people = {}  # Key: Primary Name, Value: {aliases: [], contexts: []}

    for person in tqdm.tqdm(people_list, desc="De-Duping People", position=1, leave=False):
    #for person in people_list:
        name = person["name"]
        contexts = person["contexts"]

        # Find best matches
        matches = process.extract(name, list(merged_people.keys()) + [p["name"] for p in people_list], scorer=fuzz.token_set_ratio, limit=None)
        best_matches = sorted([match[0] for match in matches if match[1] >= threshold], key=len, reverse=True)

        primary_name = best_matches[0]  # Longest name is the primary key

        if primary_name not in merged_people:
            merged_people[primary_name] = {"aliases": [primary_name], "contexts": contexts.copy()}
        else:
            merged_people[primary_name]["aliases"].extend([m for m in best_matches if m not in merged_people[primary_name]["aliases"]])
            for context in contexts:
                if context not in merged_people[primary_name]["contexts"]:
                    merged_people[primary_name]["contexts"].append(context)
    #add pronouns
    final_people = []
    for primary_name, data in merged_people.items():
      person_dict = {"name":primary_name, "aliases":data["aliases"], "contexts": data["contexts"]}
      #add pronoun
      for context in data["contexts"]:
        doc = nlp(context)
        for token in doc:
            if token.pos_ == "PRON" and token.text.lower() in ("he","she","him","her","his","hers"):
                if token.text.lower() not in person_dict["aliases"]:
                  person_dict["aliases"].append(token.text.lower())
      final_people.append(person_dict)

    return final_people
def fuzzy_match_company(company_name, company_index, company_metadata_lookup, threshold=80):
    """
    Finds best matching company using fuzzy matching.  Uses company_index
    for direct lookups, and company_metadata_lookup for fuzzy matching.
    Returns CIK or None.
    """
    # 1. Try a direct, case-insensitive lookup in the index FIRST
    company_name_lower = company_name.lower()
    cik = company_index.get(company_name_lower)
    if cik:
        return cik  # Fast path: exact match found

    # 2. If no direct match, do fuzzy matching against the metadata
    best_match = None
    best_score = 0
    for cik, metadata in company_metadata_lookup.items():
        #possible_names = [metadata["company_name"]] + metadata.get("company.tickers", []) + metadata.get("company.exchanges", [])
        #let's only look for full company name
        possible_names = [metadata["company_name"]]
        
        for name in possible_names:
            if isinstance(name, str):
                score = fuzz.token_set_ratio(company_name.lower(), name.lower()) #make lower case
                if score > best_score:
                    best_score = score
                    best_match = cik

    return best_match if best_score >= threshold else None


def extract_people(doc, nlp):
    """Extracts and deduplicates person entities."""
    people = []
    for ent in tqdm.tqdm(doc.ents, desc="Processing People", position=1, leave=False):
    #for ent in doc.ents:
        if ent.label_ == "PERSON":
            people.append({"name": ent.text.strip(), "contexts": [ent.sent.text.strip()]})

    merged_people = fuzzy_merge_people(nlp, people)
    return merged_people



def extract_companies(doc, company_metadata_lookup, company_index, filing_company_cik, use_fuzz_company_match = False):
    """Extracts company entities."""
    companies = []
        
    for ent in tqdm.tqdm(doc.ents, desc="Processing Companies", position=1, leave=False):
    #for ent in doc.ents:
          if ent.label_ == "ORG":
            entity_name_lower = ent.text.strip().lower()
            cik = company_index.get(entity_name_lower)  # Fast lookup first
            if cik:
                if cik != filing_company_cik:
                    companies.append({"cik": cik, "name": ent.text.strip(), "contexts": [ent.sent.text.strip()],"company_data":company_metadata_lookup[cik]})
            elif use_fuzz_company_match==True:
                # Fallback to fuzzy matching if not found directly
                #only bother to fuzzy match if string is of sizable length. most firms only discuss other companies in full language
                if len(ent.text.strip()) > 4:
                    cik = fuzzy_match_company(ent.text.strip(), company_index, company_metadata_lookup)
                    if cik and cik != filing_company_cik:
                        companies.append({"cik": cik, "name": ent.text.strip(), "contexts": [ent.sent.text.strip()],"company_data":company_metadata_lookup[cik]})

    merged_companies = {}
    for company in companies:
        cik = company["cik"]

        if cik not in merged_companies:
            merged_companies[cik] = {"cik":cik,
                                     "name":company["company_data"]["company_name"],
                                     "company_data":company["company_data"],
                                     "aliases": [company["name"]],
                                     "contexts": company["contexts"].copy()}
        else:
            if company["name"].lower() not in [alias.lower() for alias in merged_companies[cik]["aliases"]]:
                merged_companies[cik]["aliases"].append(company["name"])
            for context in company["contexts"]:
                if context not in merged_companies[cik]["contexts"]:
                    merged_companies[cik]["contexts"].append(context)

    return list(merged_companies.values())


def find_relationships(entity1_list, entity2_list, nlp):
    """
    Finds relationships between two lists of entities, focusing only on shared contexts.
    """
    relationships = []


    for entity1 in tqdm.tqdm(entity1_list, desc="Processing relationships", position=1, leave=False):
    #for entity1 in entity1_list:
        
        for entity2 in tqdm.tqdm(entity2_list, desc="...", position=2, leave=False):
        #for entity2 in entity2_list:
            if entity1 == entity2:  # Avoid self-relations
                continue
                         
            # Find shared contexts
            shared_contexts = set(entity1.get("contexts", [])) & set(entity2.get("contexts", []))

            if not shared_contexts:
                continue  # Skip if no shared contexts



            for context in shared_contexts:

                # if "cik" in entity1 and entity1["cik"] == 354950:
                #     if "name" in entity2 and entity2["name"] == 'Monica Schwartz':
                #         a = ""
                        
                context_doc = nlp(context) #added spacy_nlp

               # Find entity1 spans
                sentence_entity1_spans = find_entity_spans(context_doc, entity1)

                # Find entity2 spans
                sentence_entity2_spans = find_entity_spans(context_doc, entity2)

                for span1, entity1_found in sentence_entity1_spans:
                    for span2, entity2_found in sentence_entity2_spans:
                        if entity1_found != entity2_found:  # Avoid self-relations within sentence
                            # --- Simplified Relationship Extraction ---
                            relationship = find_relationship_verb(span1.root, span2.root) #passing the span root.
                            if relationship:
                                add_directional_relationship(relationships, entity1_found, entity2_found, relationship, shared_contexts=list(shared_contexts))               
    
    relationships = normalize_confidence(relationships)
    
    return relationships

def normalize_confidence(relationships):
    """
    Normalizes confidence scores in a list of relationships to a 1-10 range.
    """
    if not relationships:
        return relationships

    confidences = [rel["confidence"] for rel in relationships if rel.get("confidence") is not None]
    if not confidences:
        return relationships

    min_confidence = min(confidences)
    max_confidence = max(confidences)

    if min_confidence == max_confidence:
        # All scores are the same, set them to 5
        for rel in relationships:
            if rel.get("confidence") is not None:
                rel["confidence"] = 5
        return relationships

    for rel in relationships:
        if rel.get("confidence") is not None:
            normalized_confidence = int(1 + 9 * (rel["confidence"] - min_confidence) / (max_confidence - min_confidence))
            rel["confidence"] = normalized_confidence

    return relationships


def find_entity_spans(doc, entity):
    """
    Finds entity spans within a spaCy Doc based on aliases.
    """
    entity_spans = []
    for alias in entity.get("aliases", [entity.get("name")]):
        start_char = 0
        while True:
            start_char = doc.text.lower().find(alias.lower(), start_char)
            if start_char == -1:
                break
            end_char = start_char + len(alias)
            span = doc.char_span(start_char, end_char)
            if span:
                entity_spans.append((span, entity))
            start_char = end_char
    return entity_spans

def find_relationship_verb(source_token, target_token):
    """
    Finds a relationship verb between two tokens, indicating the source of the action.
    """

    verb_token = None
    source_is_actor = True
    confidence = 0
    # --- Dependency Checks (As Before) ---
    if (source_token.dep_ in ("nsubj", "nsubjpass") and target_token.dep_ in ("dobj", "pobj", "iobj") and
            source_token.head.pos_ == "VERB" and source_token.head == target_token.head):
        source_is_actor = True
        verb_token = source_token.head
        # return {"verb": source_token.head.lemma_, "source_is_actor": True}

    elif (target_token.dep_ in ("nsubj", "nsubjpass") and source_token.dep_ in ("dobj", "pobj", "iobj") and
          target_token.head.pos_ == "VERB" and target_token.head == source_token.head):
        source_is_actor = False
        verb_token = target_token.head
        # return {"verb": target_token.head.lemma_, "source_is_actor": False}

    elif (source_token.dep_ == "pobj" and source_token.head.pos_ == "ADP" and target_token in source_token.head.head.subtree):
        source_is_actor = True
        verb_token = source_token.head.head
        # return {"verb": source_token.head.head.lemma_, "source_is_actor": True}

    elif (target_token.dep_ == "pobj" and target_token.head.pos_ == "ADP" and source_token in target_token.head.head.subtree):
        source_is_actor = False
        verb_token = target_token.head.head
        # return {"verb": target_token.head.head.lemma_, "source_is_actor": False}

    elif source_token.dep_ == "appos" and target_token == source_token.head:
        source_is_actor = True
        verb_token = source_token.head
        # return {"verb": source_token.head.lemma_, "source_is_actor": True}

    elif target_token.dep_ == "appos" and source_token == target_token.head:
        source_is_actor = False
        verb_token = target_token.head
        # return  {"verb": target_token.head.lemma_, "source_is_actor": False}

    elif source_token.dep_ == "conj" and target_token.head == source_token.head and source_token.head.pos_ == "NOUN":
        source_is_actor = True
        verb_token = source_token.head
        # return  {"verb": source_token.head.lemma_, "source_is_actor": True}

    elif target_token.dep_ == "conj" and source_token.head == target_token.head and target_token.head.pos_ == "NOUN":
        source_is_actor = False
        verb_token = target_token.head
        # return   {"verb": target_token.head.lemma_, "source_is_actor": False}

    if not verb_token:
        # --- Verb Search ---
        sentence = source_token.sent  # Get the sentence containing the tokens
        # Find verbs between token1 and token2
        start = min(source_token.i, target_token.i)
        end = max(source_token.i, target_token.i)

        for token in sentence[start:end]:
            if token.pos_ == "VERB":
                # Heuristic filtering (adjust as needed)
                if token.dep_ not in ("aux", "auxpass"):  # Exclude auxiliary verbs
                    # Determine source_is_actor based on token order
                    source_is_actor = source_token.i < target_token.i #if the source token is before the target token, it is the actor.
                    verb_token = token
                    break
    else:
        confidence += 1  # Confidence boost for dependency match

    if verb_token:
        confidence += calculate_token_distance_relationship_confidence(source_token,target_token,verb_token)   
        return {"verb": verb_token.lemma_, "source_is_actor": source_is_actor, "confidence":confidence}
    else:
        return None #returning None instead of "" to be more clear that no verb was found.


def calculate_token_distance_relationship_confidence(source_token,target_token,verb_token):
    confidence = 0

    start = min(source_token.i, target_token.i)
    end = max(source_token.i, target_token.i)


    middle = (start + end) / 2
    distance = abs(verb_token.i - middle)
    max_distance = (end - start) / 2
    if max_distance > 0:
        verb_position_score = 3 - min(2, distance / max_distance * 2)
        confidence += verb_position_score


    distance = abs(source_token.i - target_token.i)
    max_distance = len(source_token.sent) // 2  # Adjust as needed
    proximity_score = 2 - min(1, distance / max_distance)
    confidence += proximity_score

    return confidence



def add_directional_relationship(relationships, entity1, entity2, relationship_data, shared_contexts=None):
    
     
    if relationship_data["source_is_actor"] == False:
        ent1 = entity2
        ent2 = entity1
    else:
        ent1 = entity1
        ent2 = entity2
        



    """
    Adds a directional relationship to the relationships list, de-duplicating, merging shared_contexts, and adding confidence.
    """
    if shared_contexts is None:
        shared_contexts = []

    for existing_relationship in relationships:
        if (existing_relationship["entity1"] == ent1 and
            existing_relationship["entity2"] == ent2 and
            existing_relationship["relationship"] == relationship_data["verb"]):

            # Merge shared_contexts
            existing_relationship["shared_contexts"] = list(set(existing_relationship["shared_contexts"] + shared_contexts))
            # multiply the confidence score by the number of matched context to better wieght for normalization
            existing_relationship["confidence"] += relationship_data["confidence"] * len(shared_contexts)
            # max(existing_relationship.get("confidence",0), relationship_data["confidence"])
            return  # Exit after merging

    # If no existing relationship found, append a new one
    relationships.append({
        "entity1": ent1,
        "entity2": ent2,
        "relationship": relationship_data["verb"],
        "shared_contexts": shared_contexts,
        "confidence": relationship_data["confidence"] * len(shared_contexts)
    })

def write_file_data_to_csv(
            dict_writer:csv.DictWriter,gloveEmbeddingModel,fastTextEmbeddingModel,
            url,
            filer_cik,
            form,
            people,
                 companies,
                relationships):
    





    row_master = {
        "url":url,
        "filer_cik":filer_cik,
        "form":form
    }
    for person in people:
        row = row_master.copy()
        row["entity_type"] = "person"
        row["entity_name"] = person["name"]
        row["contexts"] = person["contexts"]
        all_contexts = "\n".join(row["contexts"])
        context_glove_vector = gloveEmbeddingModel.sentence_to_vec(all_contexts)
        context_fasttext_vector = fastTextEmbeddingModel.sentence_to_vec(all_contexts)
        row["glove_vector"] = context_glove_vector
        row["fasttext_vector"] = context_fasttext_vector
        dict_writer.writerow(row)

    for company in companies:
        row = row_master.copy()
        row["entity_type"] = "company"
        row["entity_name"] = company["name"]
        row["entity_cik"] = company["cik"]
        row["contexts"] = company["contexts"]
        all_contexts = "\n".join(row["contexts"])
        context_glove_vector = gloveEmbeddingModel.sentence_to_vec(all_contexts)
        context_fasttext_vector = fastTextEmbeddingModel.sentence_to_vec(all_contexts)
        row["glove_vector"] = context_glove_vector
        row["fasttext_vector"] = context_fasttext_vector
        dict_writer.writerow(row)
    

    for relation in relationships:
        row = row_master.copy()
        
        row["entity_type"] = "realtion"

        #entity 1
        row["entity_name"] = relation["entity1"]["name"]
        if 'company_data' in relation["entity1"]:
            row["entity_cik"] = relation["entity1"]["cik"]

        #entity 2
        row["entity2_name"] = relation["entity2"]["name"]
        if 'company_data' in relation["entity2"]:
            row["entity2_cik"] = relation["entity2"]["cik"]
        row["relationship"] = relation["relationship"]
        row["confidence"] = relation["confidence"]
        row["contexts"] = relation["shared_contexts"]

        all_contexts = "\n".join(row["contexts"])
        context_glove_vector = gloveEmbeddingModel.sentence_to_vec(all_contexts)
        context_fasttext_vector = fastTextEmbeddingModel.sentence_to_vec(all_contexts)
        row["glove_vector"] = context_glove_vector
        row["fasttext_vector"] = context_fasttext_vector
        dict_writer.writerow(row)
    
def clean_text(text):
    """
    Cleans and normalizes text for spaCy processing.

    This function performs the following operations:
    - Removes leading/trailing whitespace.
    - Replaces multiple spaces with single spaces.
    - Removes control characters.
    - Removes or replaces non-ASCII characters.
    - Normalizes unicode characters.

    Args:
        text (str): The text to clean.

    Returns:
        str: The cleaned text.
    """
    # 1. Remove leading/trailing whitespace
    text = text.strip()

    # 2. Replace multiple spaces with single spaces
    text = re.sub(r'\s+', ' ', text)

    # 3. Remove control characters
    text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C')

    # 4. Handle non-ASCII characters
    # Option A: Remove non-ASCII characters (fastest for pure ASCII use cases)
    # text = ''.join(ch for ch in text if ord(ch) < 128)

    # Option B: Replace non-ASCII characters with ASCII equivalents (more robust)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')

    # 5. Normalize unicode characters
    text = unicodedata.normalize('NFKC', text)

    return text

def extract_entities_and_relationships(logger, output_file_path ,files, company_metadata_lookup, company_index, nlp, use_fuzz_company_match = False, return_results = False):
    """Main function to extract entities and relationships."""


    logger.info(f"Loading Glove embedding model {constants.DEFAULT_GLOVE_PATH}")
    try:
        gloveEmbeddingModel = WordEmbeddingModel(constants.DEFAULT_GLOVE_PATH,False)
    except Exception as e:
        logger.error(f"Error opening embedding model. please check the model file was downloaded using download_glove_model {e}")

    logger.info(f"Loading custom FastText embedding model {constants.FS_EDGAR_PATH}")
    try:
        fastTextEmbeddingModel = WordEmbeddingModel(constants.FS_EDGAR_PATH,True)
    except Exception as e:
        logger.error(f"Error opening embedding model. train the model using train_fastText {e}")


    add_to_existing_data = False
    open_text_mode = "w"

    if os.path.exists(output_file_path):
        logger.info(f"File already exists... skipping (delete it if you want to regenerate): '{output_file_path}'.")
        logger.info(f"Loading data that was already processed to data frame '{output_file_path}'")
       
        already_processed_file_data = pd.read_csv(output_file_path)
        add_to_existing_data = True
        open_text_mode = "a"
    

    
    
    file_keys = {
        "url":"",
        "filer_cik":"",
        "form":"",
        "entity_type":"",
        "entity_name":"",
        "entity_cik":"",
        "entity2_name":"",
        "entity2_cik":"",
        "relationship":"",
        "confidence":0,
        "contexts":[],
        "glove_vector":[],
        "fasttext_vector":[]
        }.keys()
    

    with open(output_file_path,open_text_mode, newline='') as f:
        dict_writer = csv.DictWriter(f, file_keys)
        if not add_to_existing_data:
            dict_writer.writeheader()



        results = {}

        file_tqdm = tqdm.tqdm(files, desc="Processing Files")
        for file_data in file_tqdm:
            if add_to_existing_data:
                url = file_data["url"]
                # check to see if file already processed
                if url in already_processed_file_data['url'].values:
                    continue


            file_path = file_data["file_path"]
            filing_company_cik = file_data["cik"]

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            except FileNotFoundError:
                logger.info(f"Error: File not found: {file_path}")
                continue
            except Exception as e:
                logger.info(f"Error reading file {file_path}: {e}")
                continue

            text = clean_text(text)
            text_length = len(text)
            if text_length > nlp.max_length:
                nlp.max_length =  len(text)  # Increase to 5,000,000 characters (5GB memory)
                logger.info(f"Increased nlp.max_length to {nlp.max_length} for file: {file_path}")

            # Update tqdm with a message before nlp processing
            file_tqdm.set_description(f"Processing file: {file_path}") #use tqdm.write to avoid overwriting the progress bar.
            file_tqdm.set_description("Loading spaCy...")

            doc = nlp(text)  # This might take a while

            # Update tqdm with a message after nlp processing
            file_tqdm.set_description("spaCy loaded, extracting data...")



            # --- Step 1 & 2: Extract and Deduplicate Entities ---
            people = extract_people(doc, nlp)
            companies = extract_companies(doc, company_metadata_lookup,company_index, filing_company_cik, use_fuzz_company_match = use_fuzz_company_match)
            # --- Step 3: Find Relationships ---
            company_company_relationships = find_relationships(companies, companies, nlp)
            company_person_relationships = find_relationships(companies, people, nlp)

            # This is slow... lets skip for now
            # person_person_relationships = find_relationships(people, people, nlp)

            # Combine relationships
            # all_relationships = company_company_relationships + company_person_relationships + person_person_relationships
            all_relationships = company_company_relationships + company_person_relationships


      
            if return_results == True:
                results[file_data["url"]] = {
                    "people": people,
                    "companies": companies,
                    "relationships": all_relationships,
                }
            write_file_data_to_csv (dict_writer,gloveEmbeddingModel,fastTextEmbeddingModel,file_data["url"],filing_company_cik,file_data["form"],people,companies,all_relationships)

            file_tqdm.set_description("Processing Complete")
        return results


def get_name_of_entity_dict(entity):
    if 'name' in entity:
        e1 = entity['name']
    elif 'company_data' in entity:
        e1 = entity['company_data']['company_name']
    else:
        e1 = "??"
    return e1
def get_public_companies(logger):
    """Gets/creates public company metadata and returns BOTH index and lookup."""
    if not os.path.exists(constants.EDGAR_PUBLIC_COMPANIES_LIST):
        logger.info(f"Creating {constants.EDGAR_PUBLIC_COMPANIES_LIST}...")
        sample_company = {
            "company_name": "Sample Co", "cik": 12345, "company.ticker_display": "SAMPLE",
            "company.tickers": ["SAMPLE"], "company.exchanges": ["NYSE"], "company.description": "",
            "company.category": "", "company.industry": "", "company.sic": 0, "company.website": ""
        }
        with open(constants.EDGAR_PUBLIC_COMPANIES_LIST, "w", newline='') as f:
            dict_writer = csv.DictWriter(f, sample_company.keys())
            dict_writer.writeheader()
            cik_df = edgar.company.get_cik_tickers()
            for _, cik_row in tqdm(cik_df.iterrows(), total=len(cik_df), desc="Fetching company data"):
                try:
                    company = edgar.company.Company(cik_row["cik"])
                    row = {
                        "company_name": company.name, "cik": int(company.cik),
                        "company.ticker_display": company.ticker_display,
                        "company.tickers": company.tickers, "company.exchanges": company.exchanges,
                        "company.description": company.description, "company.category": company.category,
                        "company.industry": company.industry, "company.sic": company.sic,
                        "company.website": company.website
                    }
                    for key, value in row.items():
                        if isinstance(value, list):
                            row[key] = ", ".join(value)
                    dict_writer.writerow(row)
                except Exception as e:
                    logger.info(f"Error fetching data for CIK {cik_row['cik']}: {e}")
        logger.info("Company metadata file created.")

    # Load metadata and build BOTH the index and the lookup
    company_metadata_lookup = {}
    company_index = {}
    companies_df = pd.read_csv(constants.EDGAR_PUBLIC_COMPANIES_LIST)
    companies_df = companies_df.dropna(subset=['company_name']).copy()
    companies_df.loc[:, "company.tickers"] = companies_df["company.tickers"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else [])
    companies_df.loc[:, "company.exchanges"] = companies_df["company.exchanges"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else [])
    
    companies_df["company.description"] = companies_df["company.description"].astype(str).fillna("")
    companies_df.loc[:, "cik"] = companies_df["cik"].fillna(0).astype(int)
    companies_df.loc[:, "company.sic"] = companies_df["company.sic"].fillna(0).astype(int)

    company_metadata_list = companies_df.to_dict(orient='records')
    for company_data in company_metadata_list:
        cik = int(company_data['cik'])
        company_metadata_lookup[cik] = company_data  # Full metadata lookup by CIK
        company_index[company_data["company_name"].lower()] = cik # Index by names/tickers/exchanges
        for ticker in company_data.get("company.tickers", []):
            if isinstance(ticker, str):
                company_index[ticker.lower()] = cik

    return company_index, company_metadata_lookup  # Return BOTH


def print_entities_and_relationships(logger, results):
    """Prints entities and relationships."""
    for file, data in results.items():
        print(f"\n----- {file} -----")

        print("\nPeople:")
        if data['people']:
            for person in data['people']:
                #print(f"  - {person['name']} (Aliases: {', '.join(person['aliases'])}), Contexts: {len(person['contexts'])}")
                print(f"  - {person['name']}, Contexts: {len(person['contexts'])}")
        else:
            print("  No people found.")

        print("\nCompanies:")
        if data['companies']:
            for company in data['companies']:
                company_data = company["company_data"]
                print(f"  - {company_data['company_name']} (CIK: {company['cik']}) {company_data['company.ticker_display']}, Contexts: {len(company['contexts'])}")
        else:
            print("  No companies found.")

        print("\nRelationships:")
        if data['relationships']:
            for rel in data['relationships']:
                #print(f"  - {rel['entity1']} -> {rel['relationship']} -> {rel['entity2']} ({rel['context']})")
                print(f"  - {get_name_of_entity_dict(rel['entity1'])} -> {rel['relationship']} -> {get_name_of_entity_dict(rel['entity2'])} conf: {rel['confidence']} ")
        else:
            print("  No relationships found.")
        print(f"\nPeople: {len(data['people'])}")
        print(f"\nCompanies: {len(data['companies'])}")
        print(f"\nRelationships: {len(data['relationships'])}")


def run_edgar_graph_extraction() -> None:
   

    index_file = constants.DEFAULT_EDGAR_FOLDER_FILE_INDEX
    output_file = constants.DEFAULT_EDGAR_GRAPH_PATH

    logger = loggers.setup_logger("SurreaEdgarGraphExtractor")
    logger.info(f"Loading EDGAR file index data to data frame '{index_file}'")


    try:
      file_index_df = pd.read_csv(index_file)
    except FileNotFoundError:
      logger.info(f"Error file not found {index_file}")
      return
    


    company_index, company_metadata_lookup = get_public_companies(logger)
    nlp = spacy.load("en_core_web_lg")  # Load spaCy model *once*

    files = file_index_df.to_dict(orient='records')

    extract_entities_and_relationships(logger,output_file,files, company_metadata_lookup,company_index,nlp, use_fuzz_company_match = False, return_results = False)
    # results = extract_entities_and_relationships(logger,output_file,files, company_metadata_lookup,company_index,nlp, use_fuzz_company_match = False, return_results = True)
    
    # if results:
    #     print_entities_and_relationships(logger,results)

if __name__ == "__main__":
    run_edgar_graph_extraction()


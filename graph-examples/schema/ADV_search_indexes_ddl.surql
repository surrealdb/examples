

DEFINE INDEX IF NOT EXISTS name_text_index ON TABLE parent_firm FIELDS name SEARCH ANALYZER large_name_analyzer BM25 CONCURRENTLY;

DEFINE INDEX IF NOT EXISTS firm_type_index ON firm FIELDS firm_type.firm_type CONCURRENTLY;
DEFINE INDEX IF NOT EXISTS parent_firm_index ON TABLE firm FIELDS parent_firm CONCURRENTLY;
DEFINE INDEX IF NOT EXISTS name_clean_text_index ON TABLE firm FIELDS name_clean SEARCH ANALYZER large_name_analyzer BM25 CONCURRENTLY;

DEFINE INDEX IF NOT EXISTS name_text_index ON TABLE firm_alias FIELDS name SEARCH ANALYZER large_name_analyzer BM25 CONCURRENTLY;
DEFINE INDEX IF NOT EXISTS cik_index ON TABLE firm_alias FIELDS cik CONCURRENTLY;
DEFINE INDEX IF NOT EXISTS legal_entity_identifier_index ON TABLE firm_alias FIELDS legal_entity_identifier CONCURRENTLY;
DEFINE INDEX IF NOT EXISTS pfid_index ON TABLE firm_alias FIELDS pfid CONCURRENTLY;

DEFINE INDEX IF NOT EXISTS email ON TABLE person_alias FIELDS email CONCURRENTLY;
DEFINE INDEX IF NOT EXISTS full_name ON TABLE person_alias FIELDS full_name CONCURRENTLY;
DEFINE INDEX IF NOT EXISTS title_text_index ON TABLE person_alias FIELDS title SEARCH ANALYZER name_analyzer BM25 CONCURRENTLY;
DEFINE INDEX IF NOT EXISTS full_name_text_index ON TABLE person_alias FIELDS full_name SEARCH ANALYZER large_name_analyzer BM25 CONCURRENTLY;

DEFINE INDEX IF NOT EXISTS description_text_index ON TABLE custodian_for FIELDS description SEARCH ANALYZER large_name_analyzer BM25 CONCURRENTLY;


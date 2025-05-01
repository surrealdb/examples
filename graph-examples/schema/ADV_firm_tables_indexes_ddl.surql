
DEFINE INDEX IF NOT EXISTS name_text_index ON TABLE parent_firm
    FIELDS name SEARCH ANALYZER name_analyzer BM25;

DEFINE INDEX IF NOT EXISTS simple_name_text_index ON TABLE parent_firm
    FIELDS simple_name SEARCH ANALYZER name_analyzer BM25;


DEFINE INDEX IF NOT EXISTS name_embedding_vector_index ON firm
    FIELDS name_embedding
    HNSW DIMENSION 100 M 32 EFC 300;


// Defines an index named 'name_text_index' on the 'firm' table for the 'name' field.
// It uses the 'name_analyzer' for text searching and the BM25 ranking algorithm.
DEFINE INDEX IF NOT EXISTS name_text_index ON TABLE firm
    FIELDS name SEARCH ANALYZER name_analyzer BM25;
DEFINE INDEX IF NOT EXISTS name_clean_index ON TABLE firm
    FIELDS name_clean ;
DEFINE INDEX IF NOT EXISTS name_clean_text_index ON TABLE firm
    FIELDS name_clean SEARCH ANALYZER name_analyzer BM25;

// Defines an index for the 'legal_name' field on the 'firm' table, using 'name_analyzer'.
-- DEFINE INDEX IF NOT EXISTS legal_name_text_index ON TABLE firm
--     FIELDS legal_name SEARCH ANALYZER name_analyzer BM25;

// Defines a regular index on the 'identifier' field of the 'firm' table for exact lookups.
DEFINE INDEX IF NOT EXISTS identifier_index ON TABLE firm
    FIELDS identifier;

// Defines a regular index on the 'cik' field within the 'section1' object of the 'firm' table.
DEFINE INDEX IF NOT EXISTS cik_index ON firm
    FIELDS section1.cik;

// Defines a regular index on the 'firm_type.firm_type' field of the 'firm' table.
DEFINE INDEX IF NOT EXISTS firm_type_index ON firm
    FIELDS firm_type.firm_type;


DEFINE INDEX IF NOT EXISTS parent_firm_index ON TABLE firm
    FIELDS parent_firm;

// Defines text search indexes for 'name' and 'legal_name' on the 'firm_alias' table.
-- DEFINE INDEX IF NOT EXISTS name_text_index ON TABLE firm_alias
--     FIELDS name SEARCH ANALYZER name_analyzer BM25;

-- DEFINE INDEX IF NOT EXISTS legal_name_text_index ON TABLE firm_alias
--     FIELDS legal_name SEARCH ANALYZER name_analyzer BM25;

// Defines a text search index on the 'description' field of the 'custodian_for' table.
-- DEFINE INDEX IF NOT EXISTS description_index ON TABLE custodian_for
--    
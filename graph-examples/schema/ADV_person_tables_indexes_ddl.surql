


// Defines text search indexes on various fields of the 'person' table.
DEFINE INDEX IF NOT EXISTS full_name_text_index ON TABLE person
    FIELDS full_name SEARCH ANALYZER name_analyzer BM25;
-- DEFINE INDEX IF NOT EXISTS first_name_text_index ON TABLE person
--     FIELDS first_name SEARCH ANALYZER name_analyzer BM25;
-- DEFINE INDEX IF NOT EXISTS last_name_text_index ON TABLE person
--     FIELDS last_name SEARCH ANALYZER name_analyzer BM25;
DEFINE INDEX IF NOT EXISTS title_text_index ON TABLE person
    FIELDS title SEARCH ANALYZER name_analyzer BM25;




// Defines text search indexes on various fields of the 'person_alias' table.
DEFINE INDEX IF NOT EXISTS full_name_text_index ON TABLE person_alias
    FIELDS full_name SEARCH ANALYZER name_analyzer BM25;
-- DEFINE INDEX IF NOT EXISTS first_name_text_index ON TABLE person_alias
--     FIELDS first_name SEARCH ANALYZER name_analyzer BM25;
-- DEFINE INDEX IF NOT EXISTS last_name_text_index ON TABLE person_alias
--     FIELDS last_name SEARCH ANALYZER name_analyzer BM25;
DEFINE INDEX IF NOT EXISTS title_text_index ON TABLE person_alias
    FIELDS title SEARCH ANALYZER name_analyzer BM25;

// Defines a regular index on the 'email' field of the 'firm_alias' table.
DEFINE INDEX IF NOT EXISTS email ON TABLE person_alias
    FIELDS email;



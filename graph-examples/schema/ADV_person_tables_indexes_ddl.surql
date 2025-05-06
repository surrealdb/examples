


// Defines text search indexes on various fields of the 'person' table.
DEFINE INDEX IF NOT EXISTS full_name_text_index ON TABLE person FIELDS full_name SEARCH ANALYZER large_name_analyzer BM25 CONCURRENTLY;



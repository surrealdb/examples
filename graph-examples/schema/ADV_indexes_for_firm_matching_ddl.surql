
DEFINE INDEX IF NOT EXISTS name_text_index ON TABLE firm FIELDS name SEARCH ANALYZER name_analyzer BM25 CONCURRENTLY;
DEFINE INDEX IF NOT EXISTS name_clean_index ON TABLE firm FIELDS name_clean;
DEFINE INDEX IF NOT EXISTS identifier_index ON TABLE firm FIELDS identifier;
DEFINE INDEX IF NOT EXISTS cik_index ON firm FIELDS section1.cik;
DEFINE INDEX IF NOT EXISTS name_embedding_vector_index ON firm FIELDS name_embedding HNSW DIMENSION 100 M 32 EFC 300 CONCURRENTLY;
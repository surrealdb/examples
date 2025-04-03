

# Define the `{corpus_table}` related graph tables.

REMOVE TABLE IF EXISTS {corpus_table}_entity;
DEFINE FIELD IF NOT EXISTS source_document ON TABLE {corpus_table}_entity TYPE Record<{corpus_table}_source_document>;
DEFINE FIELD IF NOT EXISTS identifier ON TABLE {corpus_table}_entity TYPE string
    # Field must be non-empty
    ASSERT string::len($value) > 0;
DEFINE FIELD IF NOT EXISTS name ON TABLE {corpus_table}_entity TYPE string
    # Field must be non-empty
    ASSERT string::len($value) > 0;
DEFINE FIELD IF NOT EXISTS entity_type ON TABLE {corpus_table}_entity TYPE string
    # Field must be non-empty
    ASSERT string::len($value) > 0;
DEFINE FIELD IF NOT EXISTS additional_data ON TABLE {corpus_table}_entity 
    FLEXIBLE TYPE option<object>;
DEFINE FIELD IF NOT EXISTS contexts ON TABLE {corpus_table}_entity 
    TYPE option<array<string>>;
DEFINE FIELD IF NOT EXISTS context_glove_vector ON TABLE {corpus_table}_entity 
    TYPE option<array<float>>
    # Field must have length 300 to use embedding model: glove 300d
    ASSERT array::len($value) = 300;
DEFINE FIELD IF NOT EXISTS context_fasttext_vector ON TABLE {corpus_table}_entity 
    TYPE option<array<float>>
    # Field must have length 100 to use embedding model: fast text
    ASSERT array::len($value) = 100;

DEFINE FIELD IF NOT EXISTS context_openai_vector ON TABLE {corpus_table}_entity 
    TYPE option<array<float>>
    # Field must have length 1536 to use embedding model: text-embedding-ada-002
    ASSERT array::len($value) = 1536;

DEFINE INDEX IF NOT EXISTS {corpus_table}_entity_context_glove_vector_index ON {corpus_table}_entity
    FIELDS context_glove_vector
    HNSW DIMENSION 300 M 32 EFC 300;

DEFINE INDEX IF NOT EXISTS {corpus_table}_entity_context_fasttext_vector_index ON {corpus_table}_entity
    FIELDS context_fasttext_vector
    HNSW DIMENSION 100 M 32 EFC 300;

DEFINE INDEX IF NOT EXISTS {corpus_table}_entity_context_openai_vector_index ON {corpus_table}_entity
    FIELDS context_openai_vector
    HNSW DIMENSION 1536 M 32 EFC 300;

DEFINE INDEX IF NOT EXISTS {corpus_table}_entity_identifier_index ON {corpus_table}_entity
    FIELDS identifier;


DEFINE INDEX IF NOT EXISTS {corpus_table}_entity_source_document_index ON {corpus_table}_entity FIELDS source_document,source_document.url;


REMOVE TABLE IF EXISTS {corpus_table}_relation;
DEFINE TABLE IF NOT EXISTS {corpus_table}_relation TYPE RELATION
IN {corpus_table}_entity OUT {corpus_table}_entity SCHEMAFULL;

DEFINE FIELD IF NOT EXISTS source_document ON TABLE {corpus_table}_relation TYPE Record<{corpus_table}_source_document>;
DEFINE FIELD IF NOT EXISTS contexts ON TABLE {corpus_table}_relation 
    TYPE option<array<string>>;
DEFINE FIELD IF NOT EXISTS confidence ON TABLE {corpus_table}_relation TYPE int;
DEFINE FIELD IF NOT EXISTS relationship ON TABLE {corpus_table}_relation TYPE string;
DEFINE FIELD IF NOT EXISTS context_glove_vector ON TABLE {corpus_table}_relation 
    TYPE option<array<float>>
    # Field must have length 300 to use embedding model: glove 300d
    ASSERT array::len($value) = 300;
DEFINE FIELD IF NOT EXISTS context_fasttext_vector ON TABLE {corpus_table}_relation 
    TYPE option<array<float>>
    # Field must have length 1536 to use embedding model: text-embedding-ada-002
    ASSERT array::len($value) = 100;

DEFINE FIELD IF NOT EXISTS context_openai_vector ON TABLE {corpus_table}_relation 
    TYPE option<array<float>>
    # Field must have length 1536 to use embedding model: text-embedding-ada-002
    ASSERT array::len($value) = 1536;

DEFINE INDEX IF NOT EXISTS {corpus_table}_relation_context_glove_vector_index ON {corpus_table}_relation
    FIELDS context_glove_vector
    HNSW DIMENSION 300 M 32 EFC 300;

DEFINE INDEX IF NOT EXISTS {corpus_table}_relation_context_fasttext_vector_index ON {corpus_table}_relation
    FIELDS context_fasttext_vector
    HNSW DIMENSION 100 M 32 EFC 300;


DEFINE INDEX IF NOT EXISTS {corpus_table}_relation_context_openai_vector_index ON {corpus_table}_relation
    FIELDS context_openai_vector
    HNSW DIMENSION 1536 M 32 EFC 300;



DEFINE INDEX IF NOT EXISTS {corpus_table}_relation_out_identifier_index ON {corpus_table}_relation
    FIELDS out.identifier;
DEFINE INDEX IF NOT EXISTS {corpus_table}_relation_in_identifier_index ON {corpus_table}_relation
    FIELDS in.identifier;
DEFINE INDEX IF NOT EXISTS {corpus_table}_relation_source_document_index ON {corpus_table}_relation FIELDS source_document,source_document.url;


DEFINE INDEX IF NOT EXISTS {corpus_table}_entity_name_text_index ON TABLE {corpus_table}_entity
    FIELDS name SEARCH ANALYZER snowball_analyzer BM25;

DEFINE INDEX IF NOT EXISTS {corpus_table}_relation_in_name_text_index ON TABLE {corpus_table}_relation
    FIELDS in.name SEARCH ANALYZER snowball_analyzer BM25;

DEFINE INDEX IF NOT EXISTS {corpus_table}_relation_out_name_text_index ON TABLE {corpus_table}_relation
    FIELDS out.name SEARCH ANALYZER snowball_analyzer BM25;
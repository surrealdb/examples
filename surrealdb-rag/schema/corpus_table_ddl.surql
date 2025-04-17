

# Define the `{corpus_table}` table.

REMOVE TABLE IF EXISTS {corpus_table};

DEFINE TABLE IF NOT EXISTS {corpus_table} SCHEMAFULL;

DEFINE FIELD IF NOT EXISTS url ON TABLE {corpus_table} TYPE string
    # Field must be a URL.
    ASSERT string::is::url($value);

DEFINE FIELD IF NOT EXISTS title ON TABLE {corpus_table} TYPE string
    # Field must be non-empty
    ASSERT string::len($value) > 0;

DEFINE FIELD IF NOT EXISTS text ON TABLE {corpus_table} TYPE string
    # Field must be non-empty
    ASSERT string::len($value) > 0;

DEFINE FIELD IF NOT EXISTS additional_data ON TABLE {corpus_table} FLEXIBLE TYPE option<object>;

DEFINE FIELD IF NOT EXISTS content_glove_vector ON TABLE {corpus_table} TYPE option<array<float>>
    # Field must have length 300 to use embedding model: glove 300d
    ASSERT array::len($value) = 300;

DEFINE INDEX IF NOT EXISTS {corpus_table}_content_glove_vector_index ON {corpus_table}
    FIELDS content_glove_vector
    HNSW DIMENSION 300 M 32 EFC 300;

DEFINE FIELD IF NOT EXISTS content_openai_vector ON TABLE {corpus_table} TYPE option<array<float>>
    # Field must have length 1536 to use embedding model: text-embedding-ada-002
    ASSERT array::len($value) = 1536;

DEFINE INDEX IF NOT EXISTS {corpus_table}_content_openai_vector_index ON {corpus_table}
    FIELDS content_openai_vector
    HNSW DIMENSION 1536 M 32 EFC 300;

DEFINE FIELD IF NOT EXISTS content_fasttext_vector ON TABLE {corpus_table} TYPE option<array<float>>
    # Field must have length 1536 to use embedding model: text-embedding-ada-002
    ASSERT array::len($value) = 100;

DEFINE INDEX IF NOT EXISTS {corpus_table}_content_fasttext_vector_index ON {corpus_table}
    FIELDS content_fasttext_vector
    HNSW DIMENSION 100 M 32 EFC 300;


DEFINE TABLE IF NOT EXISTS {corpus_table}_source_document SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS url ON TABLE {corpus_table}_source_document TYPE string
    # Field must be a URL.
    ASSERT string::is::url($value);
DEFINE FIELD IF NOT EXISTS title ON TABLE {corpus_table}_source_document TYPE string;
DEFINE FIELD IF NOT EXISTS additional_data ON TABLE {corpus_table}_source_document 
    FLEXIBLE TYPE option<object>;

/*
This file defines the SurrealQL for the chat functionality of this project. and functions that span either embedding model
*/


# Define the `chat` table.
DEFINE TABLE IF NOT EXISTS chat SCHEMAFULL;

DEFINE FIELD IF NOT EXISTS title ON TABLE chat TYPE string
    DEFAULT "Untitled chat";

# Field is populated on creation and is readonly.
DEFINE FIELD IF NOT EXISTS created_at ON TABLE chat TYPE datetime
    VALUE time::now() READONLY;

# Field automatically updates when a field is edited.
DEFINE FIELD IF NOT EXISTS updated_at ON TABLE chat TYPE datetime
    VALUE time::now();

# Define the message table.
DEFINE TABLE IF NOT EXISTS message SCHEMAFULL;

/* Field can only be populated with `user` or `system`.
*/
DEFINE FIELD IF NOT EXISTS role ON message TYPE string
    ASSERT $input IN ["user", "system"];

DEFINE FIELD IF NOT EXISTS content ON message TYPE string;

# Field is populated on creation and is readonly.
DEFINE FIELD IF NOT EXISTS created_at ON TABLE message TYPE datetime
    VALUE time::now() READONLY;

# Field automatically updates when a field is edited.
DEFINE FIELD IF NOT EXISTS updated_at ON TABLE message TYPE datetime
    VALUE time::now();

# Define the `sent` edge table.
DEFINE TABLE sent TYPE RELATION IN chat OUT message ENFORCED;
DEFINE FIELD IF NOT EXISTS timestamp ON TABLE sent TYPE datetime
    VALUE time::now();
DEFINE FIELD IF NOT EXISTS referenced_documents ON TABLE sent TYPE option<array<{score:float ,doc:any }>>;
DEFINE FIELD IF NOT EXISTS llm_model ON TABLE sent TYPE option<string>;
DEFINE FIELD IF NOT EXISTS embedding_model ON TABLE sent TYPE option<Record<embedding_model_definition>>;
DEFINE FIELD IF NOT EXISTS prompt_text ON TABLE sent TYPE option<string>;



# A message can only be sent in one chat
DEFINE INDEX IF NOT EXISTS unique_sent_message_in_chat
    ON TABLE sent
    COLUMNS in, out UNIQUE;


/*
This file defines the SurrealQL DDL for the glove model embedding functionality of this project.
*/

DEFINE TABLE IF NOT EXISTS corpus_table SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS table_name ON TABLE corpus_table TYPE string;
DEFINE FIELD IF NOT EXISTS display_name ON TABLE corpus_table TYPE string;
DEFINE FIELD IF NOT EXISTS embed_models ON TABLE corpus_table TYPE Array<Record<corpus_table_model>;


DEFINE TABLE IF NOT EXISTS embedding_model_definition SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS model_trainer ON TABLE embedding_model_definition TYPE string;
DEFINE FIELD IF NOT EXISTS host ON TABLE embedding_model_definition TYPE string;
DEFINE FIELD IF NOT EXISTS dimensions ON TABLE embedding_model_definition TYPE int;
DEFINE FIELD IF NOT EXISTS corpus ON TABLE embedding_model_definition TYPE string;
DEFINE FIELD IF NOT EXISTS description ON TABLE embedding_model_definition TYPE string;

# UPSERT embed_model:['FASTTEXT','fasttext wiki'] CONTENT {model_trainer:'FASTTEXT',host:'SQL',dimensions:100,version:'fasttext wiki', corpus:"trained on openai wiki sample data"};
# UPSERT embedding_model_definition:['GLOVE','glove 300d'] CONTENT {model_trainer:'GLOVE',host:'SQL',dimensions:300,version:'glove 300d', corpus:"generic pretrained"};
UPSERT embedding_model_definition:['OPENAI','text-embedding-ada-002'] CONTENT {
    model_trainer:'OPENAI',host:'API',dimensions:1536, version:"text-embedding-ada-002", corpus:"generic pretrained" , description:'The standard OPENAI embedding model'
    };

DEFINE TABLE IF NOT EXISTS corpus_table_model SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS corpus_table ON TABLE corpus_table_model TYPE Record<corpus_table>;
DEFINE FIELD IF NOT EXISTS model ON TABLE corpus_table_model TYPE Record<embedding_model_definition>;
DEFINE FIELD IF NOT EXISTS field_name ON TABLE corpus_table_model TYPE string;


# Define the `{corpus_table}` table.

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

DEFINE FIELD IF NOT EXISTS content_glove_vector ON TABLE {corpus_table} TYPE option<array<float>>
    # Field must have length 300 to use embedding model: glove 300d
    ASSERT array::len($value) = 300;

DEFINE INDEX IF NOT EXISTS {corpus_table} ON {corpus_table}
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


# this is a table to store a glove word model in database
DEFINE TABLE IF NOT EXISTS embedding_model TYPE NORMAL SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS word ON embedding_model TYPE string;
DEFINE FIELD IF NOT EXISTS model ON embedding_model TYPE Record<embedding_model_definition>;
DEFINE FIELD IF NOT EXISTS embedding ON embedding_model TYPE array<float>;

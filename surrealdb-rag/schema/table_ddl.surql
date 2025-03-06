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

There are CSS and HTML that relies on these values.
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
DEFINE FIELD IF NOT EXISTS referenced_documents ON TABLE sent TYPE option<array<{score:float ,doc:record<embedded_wiki> }>>;
DEFINE FIELD IF NOT EXISTS llm_model ON TABLE sent TYPE option<string>;
DEFINE FIELD IF NOT EXISTS embedding_model ON TABLE sent TYPE option<string>;

# A message can only be sent in one chat
DEFINE INDEX IF NOT EXISTS unique_sent_message_in_chat
    ON TABLE sent
    COLUMNS in, out UNIQUE;


/*
This file defines the SurrealQL DDL for the glove model embedding functionality of this project.
*/


# Define the `embedded_wiki` table.

DEFINE TABLE IF NOT EXISTS embedded_wiki SCHEMAFULL;

DEFINE FIELD IF NOT EXISTS url ON TABLE embedded_wiki TYPE string
    # Field must be a URL.
    ASSERT string::is::url($value);

DEFINE FIELD IF NOT EXISTS title ON TABLE embedded_wiki TYPE string
    # Field must be non-empty
    ASSERT string::len($value) > 0;

DEFINE FIELD IF NOT EXISTS text ON TABLE embedded_wiki TYPE string
    # Field must be non-empty
    ASSERT string::len($value) > 0;

DEFINE FIELD IF NOT EXISTS content_glove_vector ON TABLE embedded_wiki TYPE option<array<float>>
    # Field must have length 300 to use embedding model: glove 300d
    ASSERT array::len($value) = 300;

DEFINE INDEX IF NOT EXISTS embedded_wiki_content_glove_vector_index ON embedded_wiki
    FIELDS content_glove_vector
    HNSW DIMENSION 300 M 32 EFC 300;

DEFINE FIELD IF NOT EXISTS content_openai_vector ON TABLE embedded_wiki TYPE option<array<float>>
    # Field must have length 1536 to use embedding model: text-embedding-ada-002
    ASSERT array::len($value) = 1536;

DEFINE INDEX IF NOT EXISTS embedded_wiki_content_openai_vector_index ON embedded_wiki
    FIELDS content_openai_vector
    HNSW DIMENSION 1536 M 32 EFC 300;

DEFINE FIELD IF NOT EXISTS content_fasttext_vector ON TABLE embedded_wiki TYPE option<array<float>>
    # Field must have length 1536 to use embedding model: text-embedding-ada-002
    ASSERT array::len($value) = 100;

DEFINE INDEX IF NOT EXISTS embedded_wiki_content_fasttext_vector_index ON embedded_wiki
    FIELDS content_fasttext_vector
    HNSW DIMENSION 100 M 32 EFC 300;


# this is a table to store a glove word model in database
DEFINE TABLE IF NOT EXISTS embedding_model TYPE NORMAL SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS word ON embedding_model TYPE string;
DEFINE FIELD IF NOT EXISTS model ON embedding_model TYPE string;
DEFINE FIELD IF NOT EXISTS embedding ON embedding_model TYPE array<float>;

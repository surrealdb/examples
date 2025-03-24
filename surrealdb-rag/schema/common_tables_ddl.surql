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
DEFINE TABLE IF NOT EXISTS sent TYPE RELATION IN chat OUT message ENFORCED;
DEFINE FIELD IF NOT EXISTS timestamp ON TABLE sent TYPE datetime
    VALUE time::now();
DEFINE FIELD IF NOT EXISTS referenced_documents ON TABLE sent TYPE option<array<{score:float ,doc:any}>>;
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
DEFINE FIELD IF NOT EXISTS embed_models ON TABLE corpus_table TYPE Array<Record<corpus_table_model>>;
DEFINE FIELD IF NOT EXISTS chunk_size ON TABLE corpus_table TYPE option<int>;


DEFINE TABLE IF NOT EXISTS embedding_model_definition SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS model_trainer ON TABLE embedding_model_definition TYPE string;
DEFINE FIELD IF NOT EXISTS host ON TABLE embedding_model_definition TYPE string;
DEFINE FIELD IF NOT EXISTS dimensions ON TABLE embedding_model_definition TYPE int;
DEFINE FIELD IF NOT EXISTS corpus ON TABLE embedding_model_definition TYPE string;
DEFINE FIELD IF NOT EXISTS description ON TABLE embedding_model_definition TYPE string;
DEFINE FIELD IF NOT EXISTS version ON TABLE embedding_model_definition TYPE string;

UPSERT embedding_model_definition:['OPENAI','text-embedding-ada-002'] CONTENT {
    model_trainer:'OPENAI',host:'API',dimensions:1536, version:"text-embedding-ada-002", corpus:"generic pretrained" , description:'The standard OPENAI embedding model'
    };

DEFINE TABLE IF NOT EXISTS corpus_table_model SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS corpus_table ON TABLE corpus_table_model TYPE Record<corpus_table>;
DEFINE FIELD IF NOT EXISTS model ON TABLE corpus_table_model TYPE Record<embedding_model_definition>;
DEFINE FIELD IF NOT EXISTS field_name ON TABLE corpus_table_model TYPE string;

# this is a table to store a glove word model in database
DEFINE TABLE IF NOT EXISTS embedding_model TYPE NORMAL SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS word ON embedding_model TYPE string;
DEFINE FIELD IF NOT EXISTS model ON embedding_model TYPE Record<embedding_model_definition>;
DEFINE FIELD IF NOT EXISTS embedding ON embedding_model TYPE array<float>;


DEFINE TABLE IF NOT EXISTS corpus_graph_tables SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS corpus_table ON TABLE corpus_graph_tables TYPE Record<corpus_table>;
DEFINE FIELD IF NOT EXISTS entity_table_name ON TABLE corpus_graph_tables TYPE string;
DEFINE FIELD IF NOT EXISTS entity_display_name ON TABLE corpus_graph_tables TYPE string;
DEFINE FIELD IF NOT EXISTS relation_table_name ON TABLE corpus_graph_tables TYPE string;
DEFINE FIELD IF NOT EXISTS relation_display_name ON TABLE corpus_graph_tables TYPE string;
DEFINE FIELD IF NOT EXISTS entity_date_field ON TABLE corpus_graph_tables TYPE option<string>;
DEFINE FIELD IF NOT EXISTS relation_date_field ON TABLE corpus_graph_tables TYPE option<string>;
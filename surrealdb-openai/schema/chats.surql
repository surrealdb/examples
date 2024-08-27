/*
This file defines the SurrealQL for the chat functionality of this project.
*/

# We are required to specify the namespace and database we want our resources to reside in.
USE NS test; USE DB test;

# Define the `wiki_embedding` table.
DEFINE TABLE IF NOT EXISTS wiki_embedding SCHEMAFULL;

DEFINE FIELD IF NOT EXISTS url ON TABLE wiki_embedding TYPE string
    # Field must be a URL.
    ASSERT string::is::url($value);

DEFINE FIELD IF NOT EXISTS title ON TABLE wiki_embedding TYPE string
    # Field must be non-empty
    ASSERT string::len($value) > 0;

DEFINE FIELD IF NOT EXISTS text ON TABLE wiki_embedding TYPE string
    # Field must be non-empty
    ASSERT string::len($value) > 0;

DEFINE FIELD IF NOT EXISTS  title_vector ON TABLE wiki_embedding TYPE array<float>
    # Field must have length 1536 to use embedding model: text-embedding-ada-002
    ASSERT array::len($value) = 1536;

DEFINE FIELD IF NOT EXISTS content_vector ON TABLE wiki_embedding TYPE array<float>
    # Field must have length 1536 to use embedding model: text-embedding-ada-002
    ASSERT array::len($value) = 1536;

DEFINE INDEX IF NOT EXISTS wiki_embedding_content_vector_index ON wiki_embedding
    FIELDS content_vector
    MTREE DIMENSION 1536
    DIST COSINE;

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
DEFINE TABLE IF NOT EXISTS sent SCHEMAFULL;

DEFINE FIELD IF NOT EXISTS in ON TABLE sent TYPE record<chat>;
DEFINE FIELD IF NOT EXISTS out ON TABLE sent TYPE record<message>;
DEFINE FIELD IF NOT EXISTS timestamp ON TABLE sent TYPE datetime
    VALUE time::now();

# A message can only be sent in one chat
DEFINE INDEX IF NOT EXISTS unique_sent_message_in_chat
    ON TABLE sent
    COLUMNS in, out UNIQUE;

/* Get OpenAI token.

Insert your token into this function before importing into SurrealDB.

Returns:
    string: Bearer token.
*/
DEFINE FUNCTION IF NOT EXISTS fn::get_openai_token() {
    RETURN "Bearer " + $openai_token;
};

/* OpenAI embeddings complete.

Args:
    embeddings_model: Embedding model from OpenAI.
    input: User input.

Returns:
    array<float>: Array of embeddings.
*/
DEFINE FUNCTION IF NOT EXISTS fn::embeddings_complete($embedding_model: string, $input: string) {
    RETURN http::post(
        "https://api.openai.com/v1/embeddings",
        {
            "model": $embedding_model,
            "input": $input
        },
        {
            "Authorization": fn::get_openai_token()
        }
    )["data"][0]["embedding"]
};

/* Search for documents using embeddings.

Args:
    embeddings_model: Embedding model from OpenAI.
    input: User input.

Returns:
    array<float>: Array of embeddings.
*/
DEFINE FUNCTION IF NOT EXISTS fn::search_for_documents($input_vector: array<float>, $threshold: float) {
   LET $results = (
     SELECT
        url,
        title,
        text,
        vector::similarity::cosine(content_vector, $input_vector) AS similarity
    FROM wiki_embedding
    WHERE content_vector <|1|> $input_vector
    ORDER BY similarity DESC
    LIMIT 5
   );

   RETURN {
     results: $results,
     count: array::len($results),
     threshold: $threshold
   };
};


/* Get prompt for RAG.

Args:
    context: Context to add to the prompt.

Returns:
    string: Prompt with context.
*/
DEFINE FUNCTION IF NOT EXISTS fn::get_prompt_with_context($context: string) {
    LET $prompt = "You are an AI assistant answering questions about anything from Simple English Wikipedia the context will provide you with the most relevant data from Simple English Wikipedia including the page title, url, and page content.

    If referencing the text/context refer to it as Simple English Wikipedia.

    Please provide your response in Markdown converted to HTML format. Include appropriate headings and lists where relevant.

    At the end of the response, add link a HTML link and replace the title and url with the associated title and url of the more relevant page from the context.

    The maximum number of links you can include is 1, do not provide any other references or annotations.

    Only reply with the context provided. If the context is an empty string, reply with 'I am sorry, I do not know the answer.'.

    Do not use any prior knowledge that you have been trained on.

    <context>
        $context
    </context>";
    RETURN string::replace($prompt, '$context', $context);
};

/* OpenAI chat complete.

Args:
    llm: Large Language Model to use for generation.
    input: Initial user input.
    prompt_with_context: Prompt with context for the system.

Returns:
    string: Response from LLM.
*/
DEFINE FUNCTION IF NOT EXISTS fn::chat_complete($llm: string, $input: string, $prompt_with_context: string, $temperature: float) {
    LET $response = http::post(
        "https://api.openai.com/v1/chat/completions",
        {
            "model": $llm,
            "messages": [
                {
                 "role": "system",
                 "content": $prompt_with_context
                },
                {
                    "role": "user", "content": $input
                },
            ],
        "temperature": $temperature
    },
    {
        "Authorization": fn::get_openai_token()
    }
    )["choices"][0]["message"]["content"];

    # Sometimes there are double quotes
    RETURN string::replace($response, '"', '');
};

/* Perfrom RAG using the `text-embedding-ada-002` model for embeddings.

Args:
    llm: Large Language Model to use for generation.
    input: Initial user input.
    threshold: Similarity threshold to retreve documents.

Returns:
    string: Response from LLM.
*/
DEFINE FUNCTION IF NOT EXISTS fn::surreal_rag($llm: string, $input: string, $threshold: float, $temperature: float) {
    LET $input_vector = fn::embeddings_complete("text-embedding-ada-002", $input);
    LET $search_results = fn::search_for_documents($input_vector, $threshold);
    
    LET $context = array::join($search_results.results[*].text, "\n\n");
    
    LET $prompt = "Use the following information to answer the question. If the answer cannot be found in the given information, say 'I don't have enough information to answer that question.'\n\nInformation:\n" + $context + "\n\nQuestion: " + $input + "\n\nAnswer:";
    
    LET $answer = fn::chat_complete($llm, $prompt, "", $temperature);
    
    RETURN {
        answer: $answer,
        search_results: $search_results,
        input: $input
    };
};

/* Create a message.

Args:
    chat_id: Record ID from the `chat` table that the message was sent in.
    role: Role that sent the message. Allowed values are `user` or `system`.
    content: Sent message content.

Returns:
    oject: Content and timestamp.
*/
DEFINE FUNCTION IF NOT EXISTS fn::create_message(
    $chat_id: record<chat>, 
    $role: string,
    $content: string
) {
    # Create a message record and get the resulting ID.
    LET $message_id = 
        SELECT VALUE
            id
        FROM ONLY
            CREATE ONLY message 
            SET role = $role, 
            content = $content;

    # Create a relation between the chat record and the message record and get the resulting timestamp.
    LET $timestamp =
        SELECT VALUE
            timestamp 
        FROM ONLY 
            RELATE ONLY $chat_id->sent->$message_id;

    RETURN {
        content: $content,
        timestamp: $timestamp
    };
};

/* Create a user message.

Args:
    chat_id: Record ID from the `chat` table that the message was sent in.
    content: Sent message content.

Returns:
    object: Content and timestamp.
*/
DEFINE FUNCTION IF NOT EXISTS fn::create_user_message($chat_id: record<chat>, $content: string) {
    RETURN fn::create_message($chat_id, "user", $content);
};

/* Create system message using OpenAI.

Args:
    chat_id: Record ID of the chat the user sent a message in.

Returns:
    object: Content and timestamp.
*/
DEFINE FUNCTION IF NOT EXISTS fn::create_system_message($chat_id: record<chat>) {
    LET $last_user_message_content = (
        SELECT
            out.content AS content,
            timestamp AS timestamp 
        FROM ONLY $chat_id->sent
        ORDER BY timestamp DESC
        LIMIT 1
        FETCH out
    ).content;

    LET $rag_response = fn::surreal_rag("gpt-3.5-turbo", $last_user_message_content, 0.5, 0.5);
    
    RETURN fn::create_message($chat_id, "system", $rag_response.answer);
};

/* Generate a chat title based on the user's message in a chat.

Args:
    chat_id: Record ID from the `chat` table to generate a title for.

Returns:
    string: Generated chat title.
*/
DEFINE FUNCTION IF NOT EXISTS fn::generate_chat_title($chat_id: record<chat>) {
    # Get the `content` of the user's initial message.
    LET $first_message = (
        SELECT
            out.content AS content,
            timestamp
        FROM ONLY $chat_id->sent
        ORDER BY timestamp 
        LIMIT 1
        FETCH out
    ).content;

    # Define a system prompt to generate a title with.
    LET $system_prompt = "You are a conversation title generator for a ChatGPT type app. Respond only with a simple title using the user input.";

    # Use the Chat Complete API from OpenAI to generate the chat title.
    LET $generated_title = fn::chat_complete("gpt-3.5-turbo", $first_message, $system_prompt, 0.0);

    # Update the title of the chat and return the title.
    RETURN 
        SELECT VALUE
            title
        FROM ONLY UPDATE ONLY $chat_id
            SET title = $generated_title
            RETURN title;
};

/* Create a new chat.

Returns:
    object: Object containing `id` and `title`.
*/
DEFINE FUNCTION IF NOT EXISTS fn::create_chat() {
    RETURN CREATE ONLY chat 
        RETURN id, title;
};

/* Load a chat.

Args:
    chat_id: Record ID from the `chat` table to load.

Returns:
    array[objects]: Array of messages containing `role` and `content`.
*/
DEFINE FUNCTION IF NOT EXISTS fn::load_chat($chat_id: record<chat>) {
    RETURN 
        SELECT
            out.role AS role,
            out.content AS content,
            timestamp
        FROM $chat_id->sent
        ORDER BY timestamp
        FETCH out;
};

/* Load all chats

Returns:
    array[objects]: array of chats records containing `id`, `title`, and `created_at`.
*/
DEFINE FUNCTION IF NOT EXISTS fn::load_all_chats() {
    RETURN 
        SELECT 
            id, title, created_at 
        FROM chat 
        ORDER BY created_at DESC;
};

/* Get chat title

Args: Record ID of the chat to get the title for.

Returns:
    string: Chat title.
*/
DEFINE FUNCTION IF NOT EXISTS fn::get_chat_title($chat_id: record<chat>) {
    RETURN SELECT VALUE title FROM ONLY $chat_id;
};
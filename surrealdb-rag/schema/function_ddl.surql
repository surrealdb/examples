/*
This file defines the SurrealQL for the chat functionality of this project. and functions that span either embedding model
*/



DEFINE FUNCTION OVERWRITE fn::retrieve_vector_size_for_model($model:string) 
{
    RETURN (SELECT VALUE array::len(embedding) FROM embedding_model:[
    	$model,
    	NONE
    ]..[
    	$model,
    	..
    ] LIMIT 1)[0]
};

DEFINE FUNCTION OVERWRITE fn::sentence_to_vector($sentence: string,$model: string) {
    
    #Pull the first row to determine the size of the vector (they should all be the same)
    LET $vector_size = fn::retrieve_vector_size_for_model($model);
    
    #select the vectors from the embedding table that match the words
    LET $vectors = fn::retrieve_vectors_for_sentence($sentence,$model);

    #remove any non-matches
    LET $vectors = array::filter($vectors, |$v| { RETURN $v != NONE; });
    
    #transpose the vectors to be able to average them
    LET $transposed = array::transpose($vectors);

    #sum up the individual floats in the arrays
    LET $sum_vector = $transposed.map(|$sub_array| math::sum($sub_array));

    # calculate the mean of each vector by dividing by the total number of 
    # vectors in each of the floats
    LET $mean_vector = vector::scale($sum_vector, 1.0 / array::len($vectors));

    #if the array size is correct return it, otherwise return array of zeros
    RETURN 
        IF array::len($mean_vector) == $vector_size {$mean_vector}
        ELSE {None}
        ;
};



/* Search for documents using embeddings.

Args:
    input_vector: embedding to search for within the embedding field
    threshold: min threshold above and beyond the N returned
    model: the name of the embedding model to use... "GLOVE", "CUST_FASTTEXT" or "OPENAI"
Returns:
    array<float>: Array of embeddings.
*/

DEFINE FUNCTION OVERWRITE fn::search_for_documents($input_vector: array<float>, $threshold: float, $model: string) {
   
    LET $first_pass = 
        (IF $model = "GLOVE" THEN
            (
             SELECT
                id,
                vector::similarity::cosine(content_glove_vector, $input_vector) AS similarity_score
            FROM embedded_wiki
            WHERE content_glove_vector <|5,40|> $input_vector
            );
        ELSE IF $model = "CUST_FASTTEXT" THEN
            (
             SELECT
                id,
                vector::similarity::cosine(content_fasttext_vector, $input_vector) AS similarity_score
            FROM embedded_wiki
            WHERE content_fasttext_vector <|5,40|> $input_vector
            );
        ELSE IF $model = "OPENAI" THEN
            SELECT id FROM (
             SELECT
                id,
                vector::similarity::cosine(content_openai_vector, $input_vector) AS similarity_score
            FROM embedded_wiki
            WHERE content_openai_vector <|5,40|> $input_vector
            ) ;
        END);
    
    
    RETURN SELECT similarity_score as score,id as doc FROM $first_pass WHERE similarity_score > $threshold;
}

/* Get prompt for RAG.

Args:
    context: Context to add to the prompt.

Returns:
    string: Prompt with context.
*/
DEFINE FUNCTION OVERWRITE fn::get_prompt_with_context($documents: array<record<embedded_wiki>>) {
    
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
    LET $context = (SELECT VALUE "\n ------------- \n URL: " + url + "\nTitle: " + title + "\n Content:\n" + text as content
        FROM $documents).join("\n");
    RETURN string::replace($prompt, '$context', $context);
};


/* Create a message.

Args:
    chat_id: Record ID from the `chat` table that the message was sent in.
    role: Role that sent the message. Allowed values are `user` or `system`.
    content: Sent message content.

Returns:
    oject: Content and timestamp.
*/

DEFINE FUNCTION OVERWRITE fn::create_message(
    $chat_id: string, 
    $role: string,
    $content: string,
    $documents: option<array<{ score:float ,doc:record<embedded_wiki> }>>,
    $embedding_model: option<string>,
    $llm_model: option<string>,
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
    LET $chat = type::record($chat_id);
    LET $timestamp =
        SELECT VALUE
            timestamp 
        FROM ONLY 
            RELATE ONLY $chat->sent->$message_id CONTENT { 
                referenced_documents: $documents,
                embedding_model: $embedding_model,
                llm_model: $llm_model
                 };

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
DEFINE FUNCTION OVERWRITE fn::create_user_message($chat_id: string, $content: string, $embedding_model: string,$openai_token: option<string>) {

    LET $threshold = 0.7;
    
    LET $vector = IF $embedded_model == "OPENAI" THEN 
        fn::openai_embeddings_complete("text-embedding-ada-002", $content, $openai_token)
    ELSE
        fn::sentence_to_vector($content,$embedding_model)
    END;
    LET $documents = fn::search_for_documents($vector, $threshold ,$embedding_model);
    RETURN fn::create_message($chat_id, "user", $content, $documents,$embedding_model,None);
};

/* Create get the last user message and the reference docs for generating a prompt.

Args:
    chat_id: Record ID from the `chat` table that the message was sent in\

Returns:
    object: Content, referenced documents [{score,embedded_wiki}], timestamp.
*/

DEFINE FUNCTION OVERWRITE fn::get_last_user_message_input_and_prompt($chat_id: string) {
        LET $message = 
            SELECT content,fn::get_prompt_with_context(docs) as prompt_text FROM (
                SELECT
                    out.content AS content,
                    referenced_documents.doc as docs,
                    timestamp
                FROM ONLY type::record($chat_id)->sent
                WHERE out.role = "user"
                ORDER BY timestamp DESC
                LIMIT 1
                FETCH out);

        RETURN $message[0];
};
/* Generate get the user's message in a chat for generating a tile.

Args:
    chat_id: Record ID from the `chat` table to generate a title for.

Returns:
    string: first chat content.
*/

DEFINE FUNCTION OVERWRITE fn::get_first_message($chat_id: string) {
    # Get the `content` of the user's initial message.
    RETURN (
        SELECT
            out.content AS content,
            timestamp
        FROM ONLY type::record($chat_id)->sent
        ORDER BY timestamp 
        LIMIT 1
        FETCH out
    ).content;
    
};


/* Create a new chat.

Returns:
    object: Object containing `id` and `title`.
*/
DEFINE FUNCTION OVERWRITE fn::create_chat() {
    RETURN CREATE ONLY chat 
        RETURN id, title;
};

/* Load a chat.

Args:
    chat_id: Record ID from the `chat` table to load.

Returns:
    array[objects]: Array of messages containing `role` and `content`.
*/
DEFINE FUNCTION OVERWRITE fn::load_chat($chat_id: string) {
    RETURN 
        SELECT
            out.role AS role,
            out.content AS content,
            timestamp
        FROM type::record($chat_id)->sent
        ORDER BY timestamp
        FETCH out;
};

/* Load all chats

Returns:
    array[objects]: array of chats records containing `id`, `title`, and `created_at`.
*/
DEFINE FUNCTION OVERWRITE fn::load_all_chats() {
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
DEFINE FUNCTION OVERWRITE fn::get_chat_title($chat_id: string) {
    RETURN SELECT VALUE title FROM ONLY type::record($chat_id);
};

/* delete a chat and sent messages.

Args: Record ID of the chat to get the title for.

Returns:
    string: chat id that was delete.
*/

DEFINE FUNCTION OVERWRITE fn::delete_chat($chat_id:string){
    $chat = type::record($chat_id);
    DELETE message WHERE id IN (SELECT ->sent->message FROM $chat);
    DELETE sent WHERE in = $chat;
    DELETE $chat;
    RETURN $chat;
};


/* OpenAI embeddings complete.
Args:
    embeddings_model: Embedding model from OpenAI.
    input: User input.
    openai_token: the token used to authorize calling the API

Returns:
    array<float>: Array of embeddings.
*/
DEFINE FUNCTION OVERWRITE fn::openai_embeddings_complete($embedding_model: string, $input: string, $openai_token:string) {
    RETURN http::post(
        "https://api.openai.com/v1/embeddings",
        {
            "model": $embedding_model,
            "input": $input
        },
        {
            "Authorization": "Bearer " + $openai_token
        }
    )["data"][0]["embedding"]
};


/* OpenAI chat complete.

Args:
    llm: Large Language Model to use for generation.
    input: Initial user input.
    prompt_with_context: Prompt with context for the system.

Returns:
    string: Response from LLM.
*/
DEFINE FUNCTION OVERWRITE fn::openai_chat_complete($llm: string, $input: string, $prompt_with_context: string, $temperature: float, $openai_token:string) {
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
        "Authorization": $openai_token
    }
    )["choices"][0]["message"]["content"];

    # Sometimes there are double quotes
    RETURN string::replace($response, '"', '');
};


/* Gemini format for their endpoint has the model name and key in the query 

Args:
    llm: Large Language Model to use for generation.
    google_token: the API token for gemini
Returns:
    string: path to query for LLM.
*/
DEFINE FUNCTION OVERWRITE fn::get_gemini_api_url($llm: string,$google_token:string){
 return string::concat("https://generativelanguage.googleapis.com/v1beta/models/",$llm,":generateContent?key=",$google_token);

};


/* Gemini chat complete.

Args:
    llm: Large Language Model to use for generation.
    input: Initial user input.
    prompt_with_context: Prompt with context for the system.
    google_token: the API token for gemini

Returns:
    string: Response from LLM.
*/
DEFINE FUNCTION OVERWRITE fn::gemini_chat_complete($llm: string, $prompt_with_context: string, $input: string,$google_token:string) {

    LET $body = {
          "contents": [{
            "parts":[{"text": $prompt_with_context},{"text": $input}]
            }],
          "safetySettings": []
        };
    RETURN http::post(
        fn::get_gemini_api_url($llm,$google_token),
        $body    
    );
};


#these funtions calulates the mean vector for the tokens in a sentence using the glove Model
DEFINE FUNCTION OVERWRITE fn::retrieve_vectors_for_sentence($sentence:string,$model:string) 
{
    LET $sentence = $sentence.lowercase().
        replace('.',' .').
        replace(',',' ,').
        replace('?',' ?').
        replace('!',' !').
        replace(';',' ;').
        replace(':',' :').
        replace('(',' (').
        replace(')',' )').
        replace('[',' [').
        replace(']',' ]').
        replace('{',' {').
        replace('}',' }').
        replace('"',' "').
        replace("'"," '").
        replace('`',' `').
        replace('/',' /').
        replace('\\',' \\').
        replace('<',' <').
        replace('>',' >').
        replace('—',' —').
        replace('–',' –');
    LET $words = $sentence.words();
    LET $words = array::filter($words, |$word: any| $word != '');   

    #select the vectors from the embedding table that match the words
    
    RETURN (SELECT VALUE embedding_model:[
        $model,$this].embedding FROM $words);


};
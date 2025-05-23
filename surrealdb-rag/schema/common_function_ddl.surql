/*
This file defines the SurrealQL for the chat functionality of this project. and functions that span either embedding model
*/



/*
Calculates the mean vector for a sentence using a specified embedding model.

Args:
    sentence (string): The input sentence.
    model (Record<embedding_model_definition>): The embedding model definition.

Returns:
    array<float>|None: The mean vector of the sentence, or None if an error occurs.
*/
DEFINE FUNCTION OVERWRITE fn::sentence_to_vector($sentence: string,$model: Record<embedding_model_definition>) {
    
    #Pull the first row to determine the size of the vector (they should all be the same)
    LET $vector_size = $model.dimensions;
    
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
        IF array::len($mean_vector) == $vector_size THEN 
            $mean_vector
        ELSE 
            None
        END;
};

DEFINE FUNCTION OVERWRITE fn::additional_data_keys($corpus_table: string){
    -- This function retrieves the keys of the 'additional_data' field from the first record of a specified table.
    -- If 'additional_data' is null or missing, it returns an empty array.
    --
    -- Parameters:
    --   $corpus_table: The name of the table to query (as a string).
    --
    -- Returns:
    --   An array containing the keys of the 'additional_data' field, or an empty array if 'additional_data' is null or missing.
    --
    -- Example:
    --   SELECT fn::additional_data_keys("my_corpus_table");
   
    RETURN (SELECT VALUE IF additional_data = NONE THEN [] ELSE additional_data.keys() END FROM type::table($corpus_table) LIMIT 1)[0];
    
};


DEFINE FUNCTION OVERWRITE fn::get_datetime_range_for_corpus_table($table_name:option<string>,$date_field_name:option<string>){
   IF $table_name IS NONE OR $date_field_name IS NONE {
       RETURN NONE;
   } ELSE{
       
        RETURN
        (SELECT time::min(<datetime> type::field($date_field_name)) AS min,
        time::max(<datetime> type::field($date_field_name)) as max
        FROM type::table($table_name) GROUP ALL)[0];

   }
};

DEFINE FUNCTION OVERWRITE fn::select_additional_data($corpus_table: string,$key:string){
    -- This function selects the values associated with a specified key within the 'additional_data' field of a table,
    -- and counts the occurrences of each unique value.
    --
    -- Parameters:
    --   $corpus_table: The name of the table to query (as a string).
    --   $key: The key within the 'additional_data' field to retrieve values from (as a string).
    --
    -- Returns:
    --   A result set containing the unique values and their counts, grouped by value.
    --
    -- Example:
    --   SELECT fn::select_additional_data("my_corpus_table", "category");
    --
    RETURN SELECT val,count() FROM (
        SELECT additional_data[$key] AS val,title FROM type::table($corpus_table) GROUP BY val,title ) GROUP BY val;
};


/*
Searches for documents using embeddings.

Args:
    corpus_table (string): The name of the corpus table to search.
    input_vector (array<float>): The embedding vector to search for.
    threshold (float): The minimum similarity threshold.
    model (Record<embedding_model_definition>): The embedding model definition.

Returns:
    array<{score: float, doc: any}>: An array of documents with their similarity scores.
*/
DEFINE FUNCTION OVERWRITE fn::search_for_documents($corpus_table: string, $input_vector: array<float>, $threshold: float, $model: Record<embedding_model_definition>, $record_count: option<int>) {
    LET $first_pass = 
        (IF $model.model_trainer = "GLOVE" THEN
            (
             SELECT
                id,
                vector::similarity::cosine(content_glove_vector, $input_vector) AS similarity_score
            FROM type::table($corpus_table)
            WHERE content_glove_vector <|100,100|> $input_vector
            );
        ELSE IF $model.model_trainer = "FASTTEXT" THEN
            (
             SELECT
                id,
                vector::similarity::cosine(content_fasttext_vector, $input_vector) AS similarity_score
            FROM type::table($corpus_table)
            WHERE content_fasttext_vector <|100,100|> $input_vector
            );
        ELSE IF $model.model_trainer = "OPENAI" THEN
            (
             SELECT
                id,
                vector::similarity::cosine(content_openai_vector, $input_vector) AS similarity_score
            FROM type::table($corpus_table)
            WHERE content_openai_vector <|100,100|> $input_vector
            ) ;
        END);
    
    LET $record_count = IF $record_count = None THEN 5 ELSE $record_count END;
    
    RETURN  SELECT * FROM (  SELECT similarity_score as score,id as doc FROM $first_pass WHERE similarity_score > $threshold ) ORDER BY similarity_score DESC LIMIT $record_count;
};

/*
Generates a prompt with context and chat history.

Args:
    prompt (string): The prompt template.
    documents (array<any>): The documents to include in the context.
    chat_history (Record<message>): The chat history to include.
    include_graph (Option<bool>): Whether to include the knowledge graph.

Returns:
    string: The generated prompt.
*/

DEFINE FUNCTION OVERWRITE fn::get_prompt_with_context($prompt:string, $documents: array<any>, $chat_history: array<Record<message>>, $knowledge_graph:Option<object>) {

    
    LET $context = (SELECT VALUE "\n ------------- \n URL: " + url + "\nTitle: " + title + "\n Content:\n" + text as content
        FROM $documents).join("\n");
    LET $chat_history = (SELECT VALUE "\n ------------- \n Role: " + role + "\n Content:\n" + content as content
        FROM $chat_history).join("\n"); 

    IF $knowledge_graph IS NOT NONE{
        

        LET $entities = array::group(SELECT VALUE entities FROM $knowledge_graph);
        LET $relations = array::group(SELECT VALUE relations FROM $knowledge_graph);
        LET $knowledge_graph_string = 
            "{\nentities:[" + $entities.join(",\n") + "],\nrelations:[" + $relations.join(",\n") + "]\n}";
        RETURN string::replace(
                string::replace(
                    string::replace($prompt, '$context', $context),'$chat_history', $chat_history),'$knowledge_graph', $knowledge_graph_string);
     } ELSE {

        RETURN string::replace(
            string::replace($prompt, '$context', $context),'$chat_history', $chat_history);
        
    }
    
};




/*
Retrieves the message history for a chat.

Args:
    chat_id (string): The ID of the chat.
    message_memory_length (int): The number of messages to retrieve.

Returns:
    array<Record<message>>: An array of message records.
*/

DEFINE FUNCTION OVERWRITE fn::get_message_history($chat_id: string,$message_memory_length: int) {

   LET $full_history = (SELECT VALUE out FROM (SELECT out,timestamp FROM type::record($chat_id)->sent ORDER BY timestamp DESC));
   RETURN array::slice($full_history, 1, $message_memory_length - 1);
    
};

/*
Retrieves the last user message, its input, and the generated prompt.

Args:
    chat_id (string): The ID of the chat.
    prompt (string): The prompt template.
    message_memory_length (int): The number of messages to include in the history.
    option<bool>: Whether to include the knowledge graph.

Returns:
    object: An object containing the content, prompt, and timestamp of the last user message.
*/

DEFINE FUNCTION OVERWRITE fn::get_last_user_message_input_and_prompt($chat_id: string,$prompt:string,$message_memory_length: int) {

        LET $chat_history = fn::get_message_history($chat_id,$message_memory_length);

        LET $message =  
            SELECT content,fn::get_prompt_with_context($prompt,docs,$chat_history,knowledge_graph) as prompt_text
            FROM
                (
                SELECT
                    out.id,
                    out.content AS content,
                    referenced_documents.doc as docs,
                    knowledge_graph,
                    timestamp
                FROM ONLY type::record($chat_id)->sent
                WHERE out.role = "user"
                ORDER BY timestamp DESC
                LIMIT 1
                FETCH out 
            );
        
        RETURN $message[0];
};



/*
Creates a new message in a chat.

Args:
    chat_id (string): The ID of the chat.
    role (string): The role of the message sender (e.g., "user", "system").
    content (string): The message content.
    documents (option<array<{score: float, doc: any}>>): Referenced documents.
    embedding_model (option<Record<embedding_model_definition>>): The embedding model used.
    llm_model (option<string>): The LLM model used.
    prompt_text (option<string>): The prompt text used.

Returns:
    object: The created message details.
*/
DEFINE FUNCTION OVERWRITE fn::create_message(
    $chat_id: string, 
    $role: string,
    $content: string,
    $documents: option<array<{ score:float ,doc:any }>>,
    $knowledge_graph: option<object>,
    $embedding_model: option<Record<embedding_model_definition>>,
    $llm_model: option<string>,
    $prompt_text: option<string>

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
                llm_model: $llm_model,
                prompt_text: $prompt_text,
                knowledge_graph: $knowledge_graph
                 };


    RETURN fn::load_message_detail(<string>$message_id);

};



/*
Creates a new user message in a chat.

Args:
    chat_id (string): The ID of the chat.
    corpus_table (string): The corpus table the document resides in.
    content (string): The message content.
    embedding_model (option<Record<embedding_model_definition>>): The embedding model used.
    openai_token (option<string>): OpenAI API token (if applicable).

Returns:
    object: The created user message details.
*/
DEFINE FUNCTION OVERWRITE fn::create_user_message(
$chat_id: string, 
$corpus_table: string, 
$content: string, 
$embedding_model: Record<embedding_model_definition>,
$record_count: option<int>,
$graph_mode: option<string>,
$openai_token: option<string>) {

    LET $threshold = 0.7;
    LET $confidence_threshold = 5;
    LET $max_graph_size_per_doc = 100;
    LET $max_graph_size = 1000;
    
    LET $vector = IF $embedding_model.model_trainer == "OPENAI" THEN 
        fn::openai_embeddings_complete($embedding_model.version, $content, $openai_token)
    ELSE
        fn::sentence_to_vector($content,$embedding_model)
    END;

    LET $documents = fn::search_for_documents($corpus_table,$vector, $threshold ,$embedding_model,$record_count);

    
    

    LET $knowledge_graph = 
        IF ($graph_mode = "document" AND array::len($documents) > 0) THEN
            (SELECT VALUE fn::get_graph_detail_for_corpus_doc(
                     $corpus_table,doc.url,$confidence_threshold,$max_graph_size_per_doc) FROM $documents)[0];
        ELSE IF $graph_mode = "context" THEN
            fn::search_for_relevant_graph(
                 $corpus_table,$vector,$threshold,$confidence_threshold,$embedding_model,$max_graph_size); 
        END;
    RETURN fn::create_message($chat_id, "user", $content, $documents,$knowledge_graph,$embedding_model,None,None);
};




DEFINE FUNCTION OVERWRITE fn::search_for_relevant_graph($corpus_table: string, $input_vector: array<float>, $cosine_threshold: float, $confidence_threshold: float, $model: Record<embedding_model_definition>, $record_count: option<int>) {

    LET $corpus_graph_table_info = SELECT * FROM corpus_graph_tables WHERE corpus_table = type::thing('corpus_table',$corpus_table);
    LET $relate_table = type::table($corpus_graph_table_info.relation_table_name[0]);
    LET $entity_table = type::table($corpus_graph_table_info.entity_table_name[0]);

    LET $vector_field = IF $model.model_trainer = "GLOVE" THEN 'context_glove_vector'
        ELSE IF $model.model_trainer = "FASTTEXT" THEN 'context_fasttext_vector'
        ELSE IF $model.model_trainer = "OPENAI" THEN 'context_openai_vector'
        ELSE NONE END;
    
    LET $relate_data =
        (IF $model.model_trainer = "GLOVE" THEN
            (
                SELECT 
                    in.{additional_data,entity_type,identifier,name},
                    out.{additional_data,entity_type,identifier,name},
                    confidence,relationship,contexts,
                    vector::similarity::cosine(context_glove_vector, $input_vector) AS similarity_score
                FROM $relate_table WHERE 
                    context_glove_vector <|100,100|> $input_vector AND 
                    confidence>$confidence_threshold 
                ORDER BY similarity_score DESC
            );
        ELSE IF $model.model_trainer = "FASTTEXT" THEN
            (
                 SELECT 
                    in.{additional_data,entity_type,identifier,name},
                    out.{additional_data,entity_type,identifier,name},
                    confidence,relationship,contexts,
                    vector::similarity::cosine(context_fasttext_vector, $input_vector) AS similarity_score 
                FROM $relate_table WHERE 
                    context_fasttext_vector <|100,100|> $input_vector AND 
                    confidence>$confidence_threshold 
                ORDER BY similarity_score DESC
            );
        ELSE IF $model.model_trainer = "OPENAI" THEN
            (
                SELECT 
                    in.{additional_data,entity_type,identifier,name},
                    out.{additional_data,entity_type,identifier,name},
                    confidence,relationship,contexts,
                    vector::similarity::cosine(context_openai_vector, $input_vector) AS similarity_score 
                FROM $relate_table WHERE 
                    context_openai_vector <|100,100|> $input_vector AND 
                    confidence>$confidence_threshold 
                ORDER BY similarity_score DESC
            
            ) ;
        END);
    
    LET $record_count = IF $record_count = None THEN 100 ELSE $record_count END;
    
    LET $additional_data = None;
    LET $entities = 
        SELECT in.additional_data AS addtional_data,in.name AS name,in.identifier AS identifier,in.entity_type AS entity_type 
            FROM $relate_data 
            WHERE similarity_score > $cosine_threshold;

    
    LET $relations = SELECT
            in.identifier AS in_identifier,
            out.identifier AS out_identifier,
            confidence,relationship,contexts,
            similarity_score FROM $relate_data WHERE similarity_score > $cosine_threshold
    ORDER BY similarity_score DESC LIMIT $record_count;
    
    
    
    RETURN  {
        additional_data:$additional_data,
        relations:(SELECT * FROM $relations LIMIT $record_count),
        entities:(SELECT * FROM $entities WHERE 
            identifier IN (SELECT VALUE in_identifier FROM $relations)
            OR identifier IN (SELECT VALUE out_identifier FROM $relations)
        ),
    }
    
    
};


DEFINE FUNCTION OVERWRITE fn::get_corpus_doc_from_extended_url($corpus_table: string, $url: string) {
    LET $corpus_graph_table_info = SELECT * FROM corpus_graph_tables WHERE 
        corpus_table = type::thing('corpus_table',$corpus_table);
    LET $source_document_table = type::table($corpus_graph_table_info.source_document_table_name[0]);
    RETURN (SELECT value id FROM $source_document_table WHERE string::starts_with($url,url))[0];
};

DEFINE FUNCTION OVERWRITE fn::get_graph_detail_for_corpus_doc($corpus_table: string, $source_document: any, $confidence_threshold: float, $record_count: option<int>) {

        
    LET $corpus_graph_table_info = SELECT * FROM corpus_graph_tables WHERE 
        corpus_table = type::thing('corpus_table',$corpus_table);
    LET $relate_table = type::table($corpus_graph_table_info.relation_table_name[0]);
    LET $entity_table = type::table($corpus_graph_table_info.entity_table_name[0]);

    LET $source_document_record = 
        IF type::is::record($source_document) THEN 
            $source_document
        ELSE
            fn::get_corpus_doc_from_extended_url($corpus_table,$source_document)
        END;



    LET $additional_data = (SELECT VALUE additional_data FROM $source_document_record)[0];
    LET $entities = 
        SELECT additional_data,name,identifier,entity_type FROM $entity_table 
            WHERE source_document = $source_document_record;
    LET $relations = 
        SELECT 
            in.identifier AS in_identifier,
            out.identifier AS out_identifier,
            confidence,relationship,contexts FROM $relate_table 
            WHERE source_document = $source_document_record AND confidence >= $confidence_threshold
        ORDER BY confidence DESC;
    
    LET $record_count = IF $record_count = None THEN 100 ELSE $record_count END;
    
    RETURN  {
        additional_data:$additional_data,
        relations:(SELECT * FROM $relations LIMIT $record_count),
        entities:(SELECT * FROM $entities WHERE 
            identifier IN (SELECT VALUE in_identifier FROM $relations)
            OR identifier IN (SELECT VALUE out_identifier FROM $relations)
        ),
    }
};





/*
Creates a new system message in a chat.

Args:
    chat_id (string): The ID of the chat.
    content (string): The message content.
    llm_model (string): The LLM model used.
    prompt_text (string): The prompt used to generate the system message.

Returns:
    object: The created system message details.
*/
DEFINE FUNCTION OVERWRITE fn::create_system_message($chat_id: string, $content: string, $llm_model: string,$prompt_text:string) {
    RETURN fn::create_message($chat_id, "system", $content, None,None,None,$llm_model,$prompt_text);
};





/*
Retrieves the first message in a chat.

Args:
    chat_id (string): The ID of the chat.

Returns:
    string|null: The content of the first message, or null if the chat is empty.
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


/*
Creates a new chat.

Returns:
    object: The created chat object with `id` and `title`.
*/
DEFINE FUNCTION OVERWRITE fn::create_chat() {
    RETURN CREATE ONLY chat 
        RETURN id, title;
};


/*
Loads the messages in a chat.

Args:
    chat_id (string): The ID of the chat.

Returns:
    array<object>: An array of message objects.
*/
DEFINE FUNCTION OVERWRITE fn::load_chat($chat_id: string) {
    RETURN 
        SELECT
            out.id AS id,
            out.role AS role,
            out.content AS content,
            timestamp
        FROM type::record($chat_id)->sent
        ORDER BY timestamp
        FETCH out;
};

/*
Loads all chats.

Returns:
    array<object>: An array of chat objects.
*/
DEFINE FUNCTION OVERWRITE fn::load_all_chats() {
    RETURN 
        SELECT 
            id, title, created_at 
        FROM chat 
        ORDER BY created_at DESC;
};

/*
Retrieves the title of a chat.

Args:
    chat_id (string): The ID of the chat.

Returns:
    string: The chat title.
*/
DEFINE FUNCTION OVERWRITE fn::get_chat_title($chat_id: string) {
    RETURN SELECT VALUE title FROM ONLY type::record($chat_id);
};

/*
Deletes a chat and its messages.

Args:
    chat_id (string): The ID of the chat to delete.

Returns:
    string: The ID of the deleted chat.
*/
DEFINE FUNCTION OVERWRITE fn::delete_chat($chat_id:string){
    $chat = type::record($chat_id);
    DELETE message WHERE id IN (SELECT ->sent->message FROM $chat);
    DELETE sent WHERE in = $chat;
    DELETE $chat;
    RETURN $chat;
};

/*
Generates embeddings using the OpenAI API.

Args:
    embedding_model (string): The OpenAI embedding model to use.
    input (string): The input text.
    openai_token (string): The OpenAI API token.

Returns:
    array<float>: The generated embeddings.
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

/*
Generates a chat completion using the OpenAI API.

Args:
    llm (string): The OpenAI LLM to use.
    prompt_with_context (string): The prompt with context.
    input (string): The user input.
    temperature (float): The temperature for generation.
    openai_token (string): The OpenAI API token.

Returns:
    string: The generated chat response.
*/
DEFINE FUNCTION OVERWRITE fn::openai_chat_complete($llm: string, $prompt_with_context: string, $input: string, $temperature: float, $openai_token:string) {
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
        "Authorization": "Bearer " + $openai_token
    }
    )["choices"][0]["message"]["content"];

    # Sometimes there are double quotes
    RETURN string::replace($response, '"', '');
};

/*
Generates the Gemini API URL.

Args:
    llm (string): The Gemini LLM to use.
    google_token (string): The Google API token.

Returns:
    string: The Gemini API URL.
*/
DEFINE FUNCTION OVERWRITE fn::get_gemini_api_url($llm: string,$google_token:string){
 return string::concat("https://generativelanguage.googleapis.com/v1beta/models/",$llm,":generateContent?key=",$google_token);

};

/* Gemini chat complete.

Args:
    llm (string): Large Language Model to use for generation.
    input (string): Initial user input.
    prompt_with_context (string): Prompt with context for the system.
    google_token (string): The API token for Gemini.

Returns:
    object: Response from LLM.
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




/*
Loads the details of a document.

Args:
    corpus_table (string): The name of the corpus table.
    document_id (string): The ID of the document.

Returns:
    object: The document details.
*/
DEFINE FUNCTION OVERWRITE fn::load_document_detail($corpus_table:string,$document_id: string) {
    RETURN SELECT * FROM type::thing($corpus_table,$document_id);
};
    
/*
Loads the details of a documents with the same root url.

Args:
    corpus_table (string): The name of the corpus table.
    url (string): root url to match.

Returns:
    array<object>: The documents detail.
*/
DEFINE FUNCTION OVERWRITE fn::load_documents_from_url_root($corpus_table:string,$url_root: string) {
    RETURN SELECT * FROM type::table($corpus_table) WHERE string::starts_with(url,$url_root) = True
};
    

/*
Loads the details of a message, including related sent data.

Args:
    message_id (string): The ID of the message.

Returns:
    object: The message details, including related sent data.
*/
DEFINE FUNCTION OVERWRITE fn::load_message_detail($message_id: string) {
    RETURN (SELECT *,<-sent.{referenced_documents,embedding_model,llm_model,timestamp,prompt_text,knowledge_graph} AS sent FROM  type::record($message_id))[0];
};
/*
Retrieves the vectors for each word in a sentence using the specified embedding model.

Args:
    sentence (string): The input sentence.
    model (Record<embedding_model_definition>): The embedding model definition.

Returns:
    array<array<float>>: An array of embedding vectors, one for each word.
*/
DEFINE FUNCTION OVERWRITE fn::retrieve_vectors_for_sentence($sentence:string,$model:Record<embedding_model_definition>) 
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
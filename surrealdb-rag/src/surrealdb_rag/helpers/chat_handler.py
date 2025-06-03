
"""Handles chat-related operations in the application."""


from surrealdb_rag.helpers.params import DatabaseParams, ModelParams, SurrealParams

from surrealdb_rag.helpers.ux_helpers import *
from surrealdb_rag.helpers.llm_handler import RAGChatHandler
from surrealdb import AsyncSurreal



class ChatHandler():
    """
    Provides methods for managing chat sessions and messages within the application.

    This class interacts with the SurrealDB database to create, delete, load, and retrieve details
    about chat conversations and individual messages. It also integrates with the LLM handler
    to generate system messages based on user input and chat history.
    """
    def __init__(self, connection: AsyncSurreal):
        """
        Initializes the ChatHandler with a database connection.

        Args:
            connection: The SurrealDB connection object.
        """

        self.connection = connection
    

    async def create_chat(self):
        """
        Creates a new chat session in the database.

        Returns:
            dict: A dictionary containing the 'id' and 'title' of the newly created chat.
        """
        chat_record = await self.connection.query(
            """RETURN fn::create_chat();"""
        )
        return {
                "id": chat_record["id"],
                "title": chat_record["title"],
            }
        
    async def delete_chat(self,chat_id:str ):
        """
        Deletes a chat session and its associated messages from the database.

        Args:
            chat_id (str): The ID of the chat to delete.
        """
        SurrealParams.ParseResponseForErrors( await self.connection.query_raw(
            """RETURN fn::delete_chat($chat_id)""",params = {"chat_id":chat_id}    
        ))
        

    async def chat_detail(self,chat_id: str):
        """
        Loads the details of a specific chat, including its messages.

        This function retrieves the messages associated with a given chat ID and parses the content
        of each message to extract the actual message and any "thinking" process the LLM used.

        Args:
            chat_id (str): The ID of the chat to load.

        Returns:
            dict: A dictionary containing the list of 'messages' and chat 'detail'.
                  Each message has 'content' and optionally 'think'.
        """
        
        message_records = await self.connection.query(
            """RETURN fn::load_chat($chat_id)""",vars = {"chat_id":chat_id}    
        )

        title = await self.connection.query(
            """RETURN fn::get_chat_title($chat_id);""",vars = {"chat_id":chat_id}
        )

        for i, message in enumerate(message_records):
            message_think = RAGChatHandler.parse_llm_response_content(message["content"])
            message_records[i]["content"] = message_think["content"]
            if message_think["think"]:
                message_records[i]["think"] = message_think["think"]

        return {
                "messages": message_records,
                "chat": {"id":chat_id,"title": title } }
    

    async def message_detail(self,message_id: str):
        """
        Loads the details of a specific message.

        This function retrieves a message by its ID, parses its content to separate the actual
        message from any LLM "thinking", and extracts information about the associated knowledge
        graph and corpus table.

        Args:
            message_id (str): The ID of the message to load.

        Returns:
            dict: A dictionary containing the 'message' details, the 'corpus_table' name,
                  'graph_data' (converted for UI), 'graph_size', and a formatted 'graph_id'.
        """
        message = await self.connection.query(
            """RETURN fn::load_message_detail($message_id)""",vars = {"message_id":message_id}    
        )
        message_think = RAGChatHandler.parse_llm_response_content(message["content"])
        message["content"] = message_think["content"]
        if message_think["think"]:
            message["think"] = message_think["think"]
        
        
        corpus_table = ""   
        graph_data = message["sent"][0]["knowledge_graph"]
        if graph_data:
            graph_size = len(graph_data["relations"])
            graph_title = f"Message Graph For Message ID: {message_id}"
            if message['sent'][0]['referenced_documents']:
                doc_id:RecordID = message['sent'][0]['referenced_documents'][0]['doc']
                corpus_table = doc_id.table_name
        else:
            graph_size = 0
            graph_title = ""

        return {
                "message": message,
                "corpus_table": corpus_table,
                "graph_data": convert_prompt_graph_to_ux_data(graph_data),
                "graph_size": graph_size,
                "graph_id": format_url_id(graph_title.replace(" ","_"))
            }
            
    
    async def all_chats(self):
        """
        Loads all chat sessions from the database.

        Returns:
            list: A list of dictionaries, where each dictionary represents a chat session.
        """
        chat_records = await self.connection.query(
            """RETURN fn::load_all_chats();"""
        )
        return chat_records
    

    async def create_user_message(self,chat_id: str, corpus_table: str, content:str ,embed_model: any,number_of_chunks: int,graph_mode: str,openai_token: str):
        """
        Creates a new user message in a chat session.

        This function saves a user's message to the database, along with information about the
        corpus table, embedding model, and other relevant parameters.

        Args:
            chat_id (str): The ID of the chat the message belongs to.
            corpus_table (str): The name of the corpus table used for context retrieval.
            content (str): The text content of the user's message.
            embed_model (any): The embedding model used for the message.
            number_of_chunks (int): The number of chunks to retrieve from the corpus.
            graph_mode (str): The graph mode for relationship extraction.
            openai_token (str): The OpenAI token used for authentication.

        Returns:
            dict: A dictionary containing the created 'message' details.
        """
        outcome = SurrealParams.ParseResponseForErrors( await self.connection.query_raw(
                """RETURN fn::create_user_message($chat_id,$corpus_table, $content,
                type::thing('embedding_model_definition',$embedding_model),$number_of_chunks,$graph_mode,$openaitoken);""",
                params = {
                    "chat_id":chat_id,
                    "corpus_table":corpus_table,
                    "content":content,
                    "embedding_model":embed_model,
                    "openaitoken":openai_token,
                    "number_of_chunks":number_of_chunks,
                    "graph_mode":graph_mode
                    }    
            ))
        
        message = outcome["result"][0]["result"]
        return {
                "message" : message
            }
        

    async def create_system_message(
            self,     
    chat_id: str,
    llm_model: str,
    prompt_template: str,
    number_of_chats: int,
    llm_handler: RAGChatHandler):
        """
        Creates a system message in a chat session, generated by the LLM.

        This function retrieves the last user message and prompt, calls the LLM to generate a response,
        saves the LLM's response as a system message in the database, and optionally updates the chat's title
        if it's the first message.

        Args:
            chat_id (str): The ID of the chat the message belongs to.
            llm_model (str): The LLM model used to generate the response.
            prompt_template (str): The template used to generate the prompt for the LLM.
            number_of_chats (int): The number of previous messages to include in the prompt.
            llm_handler (RAGChatHandler): The LLM handler object.

        Returns:
            dict: A dictionary containing the newly generated 'message' and optionally the 'new_title' of the chat.
        """
        outcome = SurrealParams.ParseResponseForErrors( await self.connection.query_raw(
            """RETURN fn::get_last_user_message_input_and_prompt($chat_id,$prompt,$message_memory_length);""",params = {"chat_id":chat_id,"prompt":prompt_template,"message_memory_length":number_of_chats}
        ))
        result =  outcome["result"][0]["result"]
        prompt_text = result["prompt_text"]
        content = result["content"]
        #call the LLM
       
        llm_response = await llm_handler.get_chat_response(prompt_text,content)
        
        #save the response in the DB
        outcome = SurrealParams.ParseResponseForErrors(await self.connection.query_raw(
            """RETURN fn::create_system_message($chat_id,$llm_response,$llm_model,$prompt_text);""",params = {"chat_id":chat_id,"llm_response":llm_response,"llm_model":llm_model,"prompt_text":prompt_text}
            ))
        
        title = await self.connection.query(
            """RETURN fn::get_chat_title($chat_id);""",vars = {"chat_id":chat_id}
        )
        new_title = ""
        if title == "Untitled chat":
            first_message_text = await self.connection.query(
                "RETURN fn::get_first_message($chat_id);",vars={"chat_id":chat_id}
            )
            system_prompt = "You are a conversation title generator for a ChatGPT type app. Respond only with a simple title using the user input."
            new_title = await llm_handler.get_short_plain_text_response(system_prompt,first_message_text)
            #update chat title in database
            SurrealParams.ParseResponseForErrors(await self.connection.query_raw(
                """UPDATE type::record($chat_id) SET title=$title;""",params = {"chat_id":chat_id,"title":new_title}    
            ))

        message = outcome["result"][0]["result"]
        
        message_think = RAGChatHandler.parse_llm_response_content(message["content"])
        message["content"] = message_think["content"]
        if message_think["think"]:
            message["think"] = message_think["think"]
        return {
                "new_title": new_title.strip(),
                "message": message
            }
        


from surrealdb_rag.constants import DatabaseParams, ModelParams, ArgsLoader,SurrealParams
from surrealdb import AsyncSurreal
import datetime
from surrealdb_rag.ux_helpers import *
from surrealdb_rag.llm_handler import RAGChatHandler



class ChatHandler():
    
    def __init__(self, connection):
        self.connection = connection
    

    async def create_chat(self):
        chat_record = await self.connection.query(
            """RETURN fn::create_chat();"""
        )
        return {
                "chat_id": chat_record["id"],
                "chat_title": chat_record["title"],
            }
        
    async def delete_chat(self,chat_id:str ):
        """Delete a chat and its messages."""
        SurrealParams.ParseResponseForErrors( await self.connection.query_raw(
            """RETURN fn::delete_chat($chat_id)""",params = {"chat_id":chat_id}    
        ))
        

    async def chat_detail(self,chat_id: str):
      
        """Load a chat."""
        message_records = await self.connection.query(
            """RETURN fn::load_chat($chat_id)""",params = {"chat_id":chat_id}    
        )

        title = await self.connection.query(
            """RETURN fn::get_chat_title($chat_id);""",params = {"chat_id":chat_id}
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
       

        """Load a message."""
        message = await self.connection.query(
            """RETURN fn::load_message_detail($message_id)""",params = {"message_id":message_id}    
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
        """Load all chats."""
        chat_records = await self.connection.query(
            """RETURN fn::load_all_chats();"""
        )
        return chat_records
    

    async def create_user_message(self,chat_id: str, corpus_table: str, content:str ,embed_model: any,number_of_chunks: int,graph_mode: str,openai_token: str):
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
            """RETURN fn::get_chat_title($chat_id);""",params = {"chat_id":chat_id}
        )
        new_title = ""
        if title == "Untitled chat":
            first_message_text = await self.connection.query(
                "RETURN fn::get_first_message($chat_id);",params={"chat_id":chat_id}
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
        

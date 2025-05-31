from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, function_tool
from dotenv import load_dotenv
import os
import asyncio
from pymongo import MongoClient
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv()
app = FastAPI()





class Prompt(BaseModel):
    user_input: str


MONGO_URI = os.getenv("MONGO_URI")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
set_tracing_disabled = True

external_client = AsyncOpenAI(
    api_key=GEMINI_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)





db_client = MongoClient(MONGO_URI)

db = db_client["test_bro"]

collection = db["crud_collection"]

# tools 

@function_tool
def create(documents: list):
    """
    Create a new document in the MongoDB collection.
    Args:
        documents (list): a list containing document dictionaries, i.e.  [
            {"name": "john doe"},
            {"age": 80}
        ] 
        
    
    """
    result = collection.insert_many(documents)
    return f"Documents with id: '{result.inserted_ids}' created successfully."

@function_tool
def find(query, limit: int ):
    """
    Read/find desired documents in a collection.
        Args:
            query (dict): The filter query to match documents (default: {} for all documents), example: {"age": {"$gt": 18}}. 
            limit (int): The maximum number of documents to return (default: 10).
        
    """
    

    cursor =  collection.find(query).limit(limit)
    cursor_list = list(cursor)
    
    for doc in cursor_list:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
            
    return  {"documents": cursor_list}             
    

@function_tool
def find_one_doc(key, value):
    """
    Read/find one document in the collection.
        Args:
            key (str): The key to look for in the documents.
            value (str): Value of that particular key.
    
    """
    
    
    cursor  = collection.find({key : value})
    str_cursor_obj = list(cursor)
    
    for doc in str_cursor_obj:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
    
    return str_cursor_obj
    


@function_tool
def delete(filter):
    """
    Delete/remove multiple documents from the MongoDB collection.
    Args:
        filter (dict): the mongoose filter query to delete documents based on.
    """
    result = collection.delete_many(filter)
    if result.deleted_count > 0:
        return "Documents deleted successfully."
    else:
        return "No documents found."

@function_tool
def delete_one_doc(key, value):
    """
    Delete/remove a single document from the MongoDB collection.
    Args:
        key (str): Any key in that present in the document.
        value (any): value of the key. 
    """
    
    result = collection.delete_one({key, value})
    if result.deleted_count >0:
        return "Document Deleted"
    else:
        return "No document found"


@function_tool
def update(filter, update):
    """
    Update multiple documents in the MongoDB collection.
    Args:
        filter (dict): mongoose filter query to find documents based on.
        update (dict): the new value to update to the document.
    
    """
    result = collection.update_many(filter, update)
    if result.modified_count > 0:
        return f"Document updated successfully."
    else:
        return f"No document found with key."

@function_tool
def update_one_doc(key, value, update):
    """
    Update a single document in the MongoDB collection.
    Args: 
         key (str): The key to look for in the documents.
         value (str): Value of that particular key. 
         update (dict): The update operation (either $set, or $inc as per mongoose syntax) and value, e.g., {"$set": {"field": "new_value"}} or {"$inc": {"count": 1}}.
    """
    
    filter_query = {key: value}
    
    
    result = collection.update_one(filter_query, update)
    if result.deleted_count > 0:
        return "Document updated"
    else:
        return "No document found"


@app.post("/agent/")
async def main(prompt: Prompt):
    try:
        agent = Agent(
            name= "crudMaster",
            instructions="""
            You are a helpful assistant, who will use given tools for crud operations. And perform crud operations on mongodb.
            
                 
            Create: 
                use create tool for document creations.
            
            FOR SINGLE DOCUMENTS:
                  'delete_one_doc' for deleting a single file.
                  'update_one_doc' for updating a single document. when updated always respond with "updated document, read the document to see changes"
                  'find_one_doc' for reading one document.
            
            
            FOR MULTIPLE DOCUMENTS:
                  use tool 'delete' when deleting multiple files.
                  Use 'update' when the user asks to update multiple documents.when updated always respond with "updated document, read the document to see changes"
                  Use 'find' tool when you see the user is saying to read the whole collection.
            
            
                
            After each opeartion reply with specific details of that operation.    
            """,
            model= OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=external_client),
            tools=[create, find, update, delete, find_one_doc, update_one_doc, delete_one_doc]
            
        )
        
        #prompt.user_input 
        response =  await Runner.run(agent, prompt.user_input)
        
        return response.final_output
    
    except Exception as e:
        return {"error": str(e)}
    
if __name__ == "__main__":
    asyncio.run(main())   
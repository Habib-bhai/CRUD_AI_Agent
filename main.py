from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, function_tool
from dotenv import load_dotenv
import os
import asyncio
from pymongo import MongoClient


load_dotenv()





MONGO_URI = os.getenv("MONGO_URI")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
set_tracing_disabled = True

external_client = AsyncOpenAI(
    api_key=GEMINI_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)


# tools


db_client = MongoClient(MONGO_URI)

db = db_client["test_bro"]

collection = db["crud_collection"]



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
    Read documents to find the desired value in a collection.
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
def delete(filter):
    """
    Delete a document from the MongoDB collection.
    Args:
        key (str): The key for the document.
        value (str): The value for the document.
    
    """
    result = collection.delete_many(filter)
    if result.deleted_count > 0:
        return f"Document with key deleted successfully."
    else:
        return f"No document found."



@function_tool
def update(filter, update):
    """
    Update a document in the MongoDB collection.
    Args:
        key (str): The key for the document.
        value (str): The current value for the document.
        new_value (str): The new value to update the document with.
    
    """
    result = collection.update_many(filter, update)
    if result.modified_count > 0:
        return f"Document updated successfully."
    else:
        return f"No document found with key."





async def main():
    agent = Agent(
        name= "crudMaster",
        instructions="""
        You are a helpful assistant, who will use given tools for crud operations. And perform crud operations on mongodb. 
        When you create a document,reply properly with created this xyz with this id.
        When you read a document, reply properly with found "key": "value".
        when you delete, give the delete tool a proper mongoose filter query and reply properly with deleted this id (grab the objectId before deleting to represent in final_output).
        when you update, you will give the update function a mongoose filter query and update operation $set or $inc, reply updated doc with this id.
        when you see the user is saying to read the whole collection, give the find tool proper mongoose query for that and list all values in "key":"value" pairs.
        
        """,
        model= OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=external_client),
        tools=[create, find, update, delete]
        
    )
    
    
    response =  await Runner.run(agent, "create a user doc, with name habib, profession ai engineer, love agentic ai")
    
    print(response.final_output)
    
    
if __name__ == "__main__":
    asyncio.run(main())   
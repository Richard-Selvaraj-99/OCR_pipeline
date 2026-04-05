import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_DETAILS")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
database = client.doc_ai_db  # This creates a database named doc_ai_db
document_collection = database.get_collection("documents_queue")
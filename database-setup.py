import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING, TEXT
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection string from environment variable
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "chat_db")

# Initialize MongoDB client as None, to be initialized during startup
client = None
db = None

async def connect_to_mongo():
    """Connect to MongoDB and create necessary indexes for optimized queries."""
    global client, db
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    # Create collections if they don't exist
    await db.command({"create": "chats", "validator": {}})
    await db.command({"create": "users", "validator": {}})
    
    # Create indexes for better query performance
    # For chats collection
    chat_indexes = [
        IndexModel([("conversation_id", ASCENDING)], unique=True),
        IndexModel([("user_id", ASCENDING)]),
        IndexModel([("timestamp", ASCENDING)]),
        IndexModel([("content", TEXT)], name="content_text_search")
    ]
    await db.chats.create_indexes(chat_indexes)
    
    # For users collection
    user_indexes = [
        IndexModel([("user_id", ASCENDING)], unique=True)
    ]
    await db.users.create_indexes(user_indexes)
    
    print("Connected to MongoDB")

async def close_mongo_connection():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        print("Closed MongoDB connection")

def get_db():
    """Get database instance."""
    return db

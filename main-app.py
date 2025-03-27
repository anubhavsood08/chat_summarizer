from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import chat_routes
from app.database import connect_to_mongo, close_mongo_connection

app = FastAPI(
    title="Chat Summarization and Insights API",
    description="An API that processes user chat data, stores conversations in a database, and generates summaries & insights using an LLM-powered summarization model.",
    version="1.0.0"
)

# CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers for database connection
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# Include routers
app.include_router(chat_routes.router, tags=["chats"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to the Chat Summarization and Insights API",
        "docs": "/docs",
        "endpoints": {
            "Store Chat Messages": "POST /chats",
            "Retrieve Chats": "GET /chats/{conversation_id}",
            "Summarize Chat": "POST /chats/summarize",
            "Get User's Chat History": "GET /users/{user_id}/chats",
            "Delete Chat": "DELETE /chats/{conversation_id}"
        }
    }

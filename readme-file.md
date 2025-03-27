# Chat Summarization and Insights API

A FastAPI-based REST API that processes user chat data, stores conversations in a database, and generates summaries & insights using an LLM-powered summarization model.

## Features

- **Real-time chat ingestion** - Store raw chat messages in MongoDB
- **Conversation retrieval & filtering** - Find chats by user, date, or keywords
- **Chat summarization** - Generate conversation summaries using LLM
- **User chat history** - Retrieve chat history with pagination
- **Conversation insights** - Extract sentiment analysis and keywords
- **Real-time chat** - WebSocket support for real-time chat with immediate summarization
- **Streamlit UI** - Interactive user interface for chat interaction

## API Endpoints

- **Store Chat Messages**: `POST /chats`
- **Retrieve Chats**: `GET /chats/{conversation_id}`
- **Summarize Chat**: `POST /chats/summarize`
- **Get User's Chat History**: `GET /users/{user_id}/chats?page=1&limit=10`
- **Delete Chat**: `DELETE /chats/{conversation_id}`
- **Add Message to Chat**: `POST /chats/message`
- **Generate Insights**: `POST /chats/insights`
- **WebSocket Chat**: `WebSocket /ws/chat/{conversation_id}`

## Tech Stack

- **FastAPI** - High-performance web framework
- **MongoDB** - NoSQL database for chat storage
- **OpenAI API** - LLM integration for summarization and insights
- **WebSockets** - Real-time communication
- **Streamlit** - Interactive UI for chat interaction
- **Docker** - Containerization for easy deployment

## Project Structure

```
chat_summarization_api/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI app entry point
│   ├── config.py             # Configuration settings
│   ├── database.py           # Database connection setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── chat.py           # Pydantic models for chat data
│   │   └── responses.py      # Pydantic models for API responses
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat_routes.py    # API route definitions
│   │   └── websocket_routes.py # WebSocket endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat_service.py   # Chat CRUD operations
│   │   └── llm_service.py    # LLM integration for summarization
│   └── utils/
│       ├── __init__.py
│       └── helpers.py        # Utility functions
├── tests/
│   ├── __init__.py
│   ├── test_routes.py
│   └── test_services.py
├── streamlit_app.py          # Streamlit UI
├── .env                      # Environment variables
├── .gitignore
├── requirements.txt
├── streamlit_requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- MongoDB
- OpenAI API key

### Local Development Setup

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/chat-summarization-api.git
cd chat-summarization-api
```

2. **Create and activate a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create a `.env` file in the root directory:

```
MONGODB_URI=mongodb://localhost:27017
DB_NAME=chat_db
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-3.5-turbo
API_HOST=0.0.0.0
API_PORT=8000
```

5. **Run the API**

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

6. **Run Streamlit UI (optional)**

Install Streamlit UI dependencies:

```bash
pip install -r streamlit_requirements.txt
```

Run the Streamlit app:

```bash
streamlit run streamlit_app.py
```

The UI will be available at http://localhost:8501

### Docker Setup

1. **Build and run with Docker Compose**

```bash
docker-compose up -d
```

This will start:
- The API at http://localhost:8000
- MongoDB at mongodb://localhost:27017

## Usage Examples

### Store a Chat Conversation

```bash
curl -X POST http://localhost:8000/chats \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "title": "Sample Conversation",
    "messages": [
      {
        "sender_id": "user123",
        "sender_name": "John",
        "content": "Hello, how are you?"
      },
      {
        "sender_id": "user456",
        "sender_name": "Jane",
        "content": "I'm doing well, thank you!"
      }
    ]
  }'
```

### Retrieve a Chat

```bash
curl -X GET http://localhost:8000/chats/{conversation_id}
```

### Summarize a Chat

```bash
curl -X POST http://localhost:8000/chats/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "{conversation_id}",
    "additional_instructions": "Focus on key points and action items."
  }'
```

### Get User Chat History

```bash
curl -X GET "http://localhost:8000/users/user123/chats?page=1&limit=10"
```

## API Documentation

Once the API is running, you can access the auto-generated documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Optimizations

- **Indexing**: MongoDB collections are indexed for efficient queries
- **Async Database**: Using async MongoDB client for non-blocking I/O
- **Pagination**: All list endpoints support pagination for heavy load handling
- **Text Search**: MongoDB text search for filtering chats by content
- **Real-time Summarization**: Background tasks for non-blocking summarization

## Running Tests

```bash
pytest
```

## Production Deployment

For production deployment, consider:

1. Setting up authentication
2. Using a managed MongoDB instance
3. Deploying to a cloud platform (AWS, GCP, Azure)
4. Setting up proper logging and monitoring
5. Implementing rate limiting

## License

MIT

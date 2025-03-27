import os
from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # MongoDB settings
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "chat_db")
    
    # LLM settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    
    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0") 
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100

settings = Settings()

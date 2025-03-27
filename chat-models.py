from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId

class PyObjectId(str):
    """Custom ObjectId field for Pydantic models."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

class Message(BaseModel):
    """Chat message model."""
    sender_id: str = Field(..., description="ID of the message sender")
    sender_name: Optional[str] = Field(None, description="Name of the message sender")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class ConversationBase(BaseModel):
    """Base conversation model."""
    conversation_id: Optional[str] = Field(None, description="Unique conversation ID")
    user_id: str = Field(..., description="ID of the user who owns the conversation")
    title: Optional[str] = Field(None, description="Conversation title")

class ConversationCreate(ConversationBase):
    """Model for creating a new conversation."""
    messages: List[Message] = Field(..., description="List of messages in the conversation")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the conversation")

class ConversationDB(ConversationBase):
    """Database model for a conversation."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    messages: List[Message] = Field(default=[], description="List of messages in the conversation")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    summary: Optional[str] = Field(None, description="LLM-generated summary of the conversation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the conversation")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

class ConversationResponse(ConversationBase):
    """Model for conversation response."""
    id: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class SummarizeRequest(BaseModel):
    """Model for chat summarization request."""
    conversation_id: str = Field(..., description="ID of the conversation to summarize")
    additional_instructions: Optional[str] = Field(None, description="Additional instructions for summarization")

class SummarizeResponse(BaseModel):
    """Model for chat summarization response."""
    conversation_id: str
    summary: str
    keywords: Optional[List[str]] = None
    sentiment: Optional[str] = None

class MessageCreate(BaseModel):
    """Model for adding a message to an existing conversation."""
    conversation_id: str = Field(..., description="ID of the conversation")
    message: Message = Field(..., description="Message to add")

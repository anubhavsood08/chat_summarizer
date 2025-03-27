from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
from pymongo import DESCENDING, TEXT
from bson import ObjectId
from fastapi import HTTPException, status

from app.database import get_db
from app.models.chat import ConversationCreate, ConversationDB, ConversationResponse, Message
from app.models.responses import PaginatedResponse, PageInfo

class ChatService:
    """Service for chat-related operations."""
    
    def __init__(self):
        self.db = get_db()
        self.chats_collection = self.db.chats if self.db else None
    
    async def create_conversation(self, conversation: ConversationCreate) -> ConversationResponse:
        """Create a new conversation."""
        if not self.chats_collection:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection not available"
            )
        
        # Generate a unique conversation_id if not provided
        if not conversation.conversation_id:
            conversation.conversation_id = str(uuid.uuid4())
        
        # Create conversation object for database
        conversation_dict = conversation.dict(exclude={"id"})
        conversation_dict["created_at"] = datetime.utcnow()
        conversation_dict["updated_at"] = conversation_dict["created_at"]
        
        # Insert into database
        result = await self.chats_collection.insert_one(conversation_dict)
        
        # Get the created conversation
        created_conversation = await self.chats_collection.find_one({"_id": result.inserted_id})
        
        # Convert to response model
        return self._convert_to_response(created_conversation)
    
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationResponse]:
        """Get a conversation by ID."""
        if not self.chats_collection:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection not available"
            )
        
        conversation = await self.chats_collection.find_one({"conversation_id": conversation_id})
        if not conversation:
            return None
        
        return self._convert_to_response(conversation)
    
    async def update_conversation_summary(
        self, 
        conversation_id: str, 
        summary: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update conversation summary."""
        if not self.chats_collection:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection not available"
            )
        
        update_data = {
            "summary": summary,
            "updated_at": datetime.utcnow()
        }
        
        # Update metadata if provided
        if metadata:
            for key, value in metadata.items():
                update_data[f"metadata.{key}"] = value
        
        result = await self.chats_collection.update_one(
            {"conversation_id": conversation_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    
    async def get_user_conversations(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search_query: Optional[str] = None
    ) -> PaginatedResponse:
        """Get conversations for a user with pagination and filtering."""
        if not self.chats_collection:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection not available"
            )
        
        # Build query
        query = {"user_id": user_id}
        
        # Add date filtering if provided
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            
            if date_query:
                query["created_at"] = date_query
        
        # Add text search if provided
        if search_query:
            # Create text index if it doesn't exist
            try:
                await self.chats_collection.create_index([("messages.content", TEXT)])
            except Exception:
                # Index may already exist
                pass
                
            query["$text"] = {"$search": search_query}
        
        # Calculate skip value for pagination
        skip = (page - 1) * limit
        
        # Get total count for pagination info
        total = await self.chats_collection.count_documents(query)
        
        # Get conversations with pagination
        cursor = self.chats_collection.find(query)
        cursor = cursor.sort("created_at", DESCENDING)
        cursor = cursor.skip(skip).limit(limit)
        
        # Get conversations
        conversations = []
        async for conversation in cursor:
            conversations.append(self._convert_to_response(conversation))
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        page_info = PageInfo(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
        return PaginatedResponse(data=conversations, page_info=page_info)
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        if not self.chats_collection:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection not available"
            )
        
        result = await self.chats_collection.delete_one({"conversation_id": conversation_id})
        return result.deleted_count > 0
    
    async def add_message(self, conversation_id: str, message: Message) -> Optional[ConversationResponse]:
        """Add a message to an existing conversation."""
        if not self.chats_collection:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection not available"
            )
        
        # First check if the conversation exists
        conversation = await self.chats_collection.find_one({"conversation_id": conversation_id})
        if not conversation:
            return None
        
        # Prepare message data
        message_dict = message.dict()
        
        # Update the conversation with the new message
        result = await self.chats_collection.update_one(
            {"conversation_id": conversation_id},
            {
                "$push": {"messages": message_dict},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if result.modified_count == 0:
            return None
        
        # Get the updated conversation
        updated_conversation = await self.chats_collection.find_one({"conversation_id": conversation_id})
        return self._convert_to_response(updated_conversation)
    
    def _convert_to_response(self, db_conversation: Dict[str, Any]) -> ConversationResponse:
        """Convert a database conversation to a response model."""
        return ConversationResponse(
            id=str(db_conversation["_id"]),
            conversation_id=db_conversation["conversation_id"],
            user_id=db_conversation["user_id"],
            title=db_conversation.get("title"),
            messages=[Message(**msg) for msg in db_conversation.get("messages", [])],
            created_at=db_conversation["created_at"],
            updated_at=db_conversation["updated_at"],
            summary=db_conversation.get("summary"),
            metadata=db_conversation.get("metadata", {})
        )

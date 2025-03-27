# Add this to a new file app/routes/websocket_routes.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict, List, Optional
import json
import asyncio
from uuid import uuid4

from app.services.chat_service import ChatService
from app.services.llm_service import LLMService
from app.models.chat import Message
from app.utils.helpers import JSONEncoder

router = APIRouter()

# Store active connections
class ConnectionManager:
    def __init__(self):
        # Map of conversation_id -> list of websocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)

    def disconnect(self, websocket: WebSocket, conversation_id: str):
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

    async def broadcast_to_conversation(self, conversation_id: str, message: dict):
        if conversation_id in self.active_connections:
            message_json = json.dumps(message, cls=JSONEncoder)
            for connection in self.active_connections[conversation_id]:
                await connection.send_text(message_json)

manager = ConnectionManager()

# Dependency to get chat service
async def get_chat_service():
    return ChatService()

# Dependency to get LLM service
async def get_llm_service():
    return LLMService()

@router.websocket("/ws/chat/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    user_id: Optional[str] = Query(None),
    chat_service: ChatService = Depends(get_chat_service),
    llm_service: LLMService = Depends(get_llm_service)
):
    await manager.connect(websocket, conversation_id)
    
    try:
        # Check if conversation exists and create it if not
        conversation = await chat_service.get_conversation(conversation_id)
        if not conversation and user_id:
            # Create new conversation
            from app.models.chat import ConversationCreate
            new_conversation = ConversationCreate(
                conversation_id=conversation_id,
                user_id=user_id,
                title=f"Conversation {conversation_id}",
                messages=[]
            )
            conversation = await chat_service.create_conversation(new_conversation)
        
        # Real-time chat loop
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                
                # Create message
                sender_id = message_data.get("sender_id", str(uuid4()))
                sender_name = message_data.get("sender_name", f"User {sender_id}")
                content = message_data.get("content", "")
                
                # Skip empty messages
                if not content.strip():
                    continue
                
                # Create message object
                message = Message(
                    sender_id=sender_id,
                    sender_name=sender_name,
                    content=content
                )
                
                # Add message to conversation
                updated_conversation = await chat_service.add_message(conversation_id, message)
                
                if updated_conversation:
                    # Broadcast message to all connected clients
                    await manager.broadcast_to_conversation(
                        conversation_id,
                        {
                            "type": "message",
                            "message": {
                                "sender_id": message.sender_id,
                                "sender_name": message.sender_name,
                                "content": message.content,
                                "timestamp": message.timestamp.isoformat()
                            }
                        }
                    )
                    
                    # Real-time summarization if requested
                    if message_data.get("auto_summarize", False):
                        # Run summarization in background
                        asyncio.create_task(
                            generate_and_broadcast_summary(
                                conversation_id, 
                                updated_conversation, 
                                llm_service, 
                                chat_service
                            )
                        )
                
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Invalid JSON data"})
                )
            except Exception as e:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": str(e)})
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, conversation_id)

async def generate_and_broadcast_summary(
    conversation_id: str, 
    conversation, 
    llm_service: LLMService,
    chat_service: ChatService
):
    """Generate real-time summary and broadcast to all connected clients."""
    try:
        # Generate summary
        summary_result = await llm_service.summarize_conversation(conversation)
        
        # Update conversation with summary
        await chat_service.update_conversation_summary(
            conversation_id,
            summary_result["summary"],
            {
                "keywords": summary_result.get("keywords", []),
                "sentiment": summary_result.get("sentiment")
            }
        )
        
        # Broadcast summary to all connected clients
        await manager.broadcast_to_conversation(
            conversation_id,
            {
                "type": "summary",
                "summary": summary_result["summary"],
                "keywords": summary_result.get("keywords", []),
                "sentiment": summary_result.get("sentiment")
            }
        )
    except Exception as e:
        print(f"Error in real-time summarization: {str(e)}")
        await manager.broadcast_to_conversation(
            conversation_id,
            {
                "type": "error",
                "message": f"Failed to generate summary: {str(e)}"
            }
        )

# Add this to app/main.py to include the WebSocket router:
# from app.routes import websocket_routes
# app.include_router(websocket_routes.router, tags=["websocket"])

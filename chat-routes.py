from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, status
from typing import Optional, List
from datetime import datetime, timedelta

from app.models.chat import (
    ConversationCreate, 
    ConversationResponse,
    SummarizeRequest,
    SummarizeResponse,
    MessageCreate
)
from app.models.responses import (
    PaginatedResponse, 
    SuccessResponse,
    ErrorResponse
)
from app.services.chat_service import ChatService
from app.services.llm_service import LLMService

router = APIRouter()

# Dependency to get chat service
async def get_chat_service():
    return ChatService()

# Dependency to get LLM service
async def get_llm_service():
    return LLMService()

@router.post("/chats", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat: ConversationCreate,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Store a new chat conversation.
    
    - **conversation_id**: Optional unique identifier for the conversation
    - **user_id**: ID of the user who owns the conversation
    - **title**: Optional title for the conversation
    - **messages**: List of messages in the conversation
    - **metadata**: Optional additional metadata for the conversation
    """
    try:
        created_chat = await chat_service.create_conversation(chat)
        return created_chat
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chat: {str(e)}"
        )

@router.get("/chats/{conversation_id}", response_model=ConversationResponse)
async def get_chat(
    conversation_id: str = Path(..., description="ID of the conversation to retrieve"),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Retrieve a specific chat conversation by ID.
    
    - **conversation_id**: ID of the conversation to retrieve
    """
    chat = await chat_service.get_conversation(conversation_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat with ID {conversation_id} not found"
        )
    return chat

@router.post("/chats/summarize", response_model=SummarizeResponse)
async def summarize_chat(
    request: SummarizeRequest,
    chat_service: ChatService = Depends(get_chat_service),
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Generate a summary for a chat conversation using LLM.
    
    - **conversation_id**: ID of the conversation to summarize
    - **additional_instructions**: Optional instructions for the summarization
    """
    # Get the conversation
    chat = await chat_service.get_conversation(request.conversation_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat with ID {request.conversation_id} not found"
        )
    
    # Generate summary
    try:
        summary_result = await llm_service.summarize_conversation(
            chat, 
            additional_instructions=request.additional_instructions
        )
        
        # Update the chat with the summary
        await chat_service.update_conversation_summary(
            request.conversation_id, 
            summary_result["summary"],
            {
                "keywords": summary_result.get("keywords", []),
                "sentiment": summary_result.get("sentiment")
            }
        )
        
        return SummarizeResponse(
            conversation_id=request.conversation_id,
            summary=summary_result["summary"],
            keywords=summary_result.get("keywords", []),
            sentiment=summary_result.get("sentiment")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to summarize chat: {str(e)}"
        )

@router.get("/users/{user_id}/chats", response_model=PaginatedResponse[ConversationResponse])
async def get_user_chats(
    user_id: str = Path(..., description="ID of the user"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    search_query: Optional[str] = Query(None, description="Search in chat content"),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get chat history for a specific user with pagination.
    
    - **user_id**: ID of the user
    - **page**: Page number (default: 1)
    - **limit**: Number of items per page (default: 10, max: 100)
    - **start_date**: Optional filter by start date
    - **end_date**: Optional filter by end date
    - **search_query**: Optional search in chat content
    """
    # Set default end date to now if not provided
    if end_date is None:
        end_date = datetime.utcnow()
    
    # Set default start date to 30 days ago if not provided
    if start_date is None:
        start_date = end_date - timedelta(days=30)
    
    result = await chat_service.get_user_conversations(
        user_id=user_id,
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        search_query=search_query
    )
    
    return result

@router.delete("/chats/{conversation_id}", response_model=SuccessResponse)
async def delete_chat(
    conversation_id: str = Path(..., description="ID of the conversation to delete"),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Delete a specific chat conversation.
    
    - **conversation_id**: ID of the conversation to delete
    """
    deleted = await chat_service.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat with ID {conversation_id} not found"
        )
    
    return SuccessResponse(
        message=f"Chat with ID {conversation_id} successfully deleted"
    )

@router.post("/chats/message", response_model=ConversationResponse)
async def add_message(
    message_data: MessageCreate,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Add a new message to an existing conversation.
    
    - **conversation_id**: ID of the conversation
    - **message**: Message to add to the conversation
    """
    try:
        updated_chat = await chat_service.add_message(
            message_data.conversation_id,
            message_data.message
        )
        if not updated_chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat with ID {message_data.conversation_id} not found"
            )
        return updated_chat
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add message: {str(e)}"
        )

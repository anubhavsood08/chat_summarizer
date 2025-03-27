# Add this to app/routes/chat_routes.py

from typing import List

@router.post("/chats/insights", response_model=Dict[str, Any])
async def generate_insights(
    user_id: str = Body(..., embed=True, description="ID of the user"),
    limit: int = Body(5, embed=True, description="Number of recent conversations to analyze"),
    chat_service: ChatService = Depends(get_chat_service),
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Generate insights from a user's recent conversations.
    
    - **user_id**: ID of the user
    - **limit**: Number of recent conversations to analyze (default: 5)
    """
    # Get user's recent conversations
    result = await chat_service.get_user_conversations(
        user_id=user_id,
        page=1,
        limit=limit,
        start_date=None,
        end_date=None
    )
    
    if not result.data:
        return {
            "insights": "No conversations found for analysis.",
            "common_topics": [],
            "patterns": []
        }
    
    # Generate insights using LLM
    insights = await llm_service.generate_insights(result.data)
    return insights

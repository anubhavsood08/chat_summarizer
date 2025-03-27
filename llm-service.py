import os
from typing import Dict, List, Optional, Any
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

from app.config import settings
from app.models.chat import ConversationResponse, Message

load_dotenv()

class LLMService:
    """Service for LLM integration."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL
    
    async def summarize_conversation(
        self,
        conversation: ConversationResponse,
        additional_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a summary of the conversation using LLM."""
        
        if not conversation.messages:
            return {
                "summary": "No messages to summarize.",
                "keywords": [],
                "sentiment": "neutral"
            }
        
        # Format messages for the LLM
        formatted_messages = []
        for msg in conversation.messages:
            formatted_messages.append(f"{msg.sender_name or msg.sender_id}: {msg.content}")
        
        messages_text = "\n".join(formatted_messages)
        
        # Create prompt
        system_prompt = """
        You are an advanced AI assistant tasked with summarizing chat conversations. 
        For the given conversation, please provide:
        
        1. A concise summary of the key points discussed (2-3 paragraphs)
        2. A list of important keywords (5-10 words or phrases)
        3. An overall sentiment analysis (positive, negative, neutral, or mixed)
        
        Format your response as a JSON object with 'summary', 'keywords', and 'sentiment' keys.
        """
        
        if additional_instructions:
            system_prompt += f"\n\nAdditional instructions: {additional_instructions}"
        
        user_prompt = f"Please summarize the following conversation:\n\n{messages_text}"
        
        # Call LLM API
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            # Parse JSON response
            result = json.loads(response.choices[0].message.content)
            
            # Ensure all required fields are present
            if 'summary' not in result:
                result['summary'] = "Summary not available."
            if 'keywords' not in result:
                result['keywords'] = []
            if 'sentiment' not in result:
                result['sentiment'] = "neutral"
                
            return result
            
        except Exception as e:
            print(f"Error in summarizing conversation: {str(e)}")
            # Provide a fallback response in case of errors
            return {
                "summary": f"Error generating summary: {str(e)}",
                "keywords": [],
                "sentiment": "unknown"
            }
    
    async def generate_insights(self, conversations: List[ConversationResponse]) -> Dict[str, Any]:
        """Generate insights from a list of conversations."""
        
        if not conversations:
            return {
                "insights": "No conversations to analyze.",
                "common_topics": [],
                "patterns": []
            }
        
        # Format conversations for the LLM
        formatted_convos = []
        for i, convo in enumerate(conversations[:5]):  # Limit to 5 conversations for token limits
            messages_text = []
            for msg in convo.messages:
                messages_text.append(f"{msg.sender_name or msg.sender_id}: {msg.content}")
            
            formatted_convos.append(f"Conversation {i+1}:\n" + "\n".join(messages_text))
        
        all_convos_text = "\n\n".join(formatted_convos)
        
        # Create prompt
        system_prompt = """
        You are an advanced AI assistant tasked with analyzing chat conversations and providing insights.
        For the given set of conversations, please provide:
        
        1. Overall insights about patterns, trends, or notable observations
        2. Common topics or themes across conversations
        3. Any patterns in communication style or effectiveness
        
        Format your response as a JSON object with 'insights', 'common_topics', and 'patterns' keys.
        """
        
        user_prompt = f"Please analyze the following conversations and provide insights:\n\n{all_convos_text}"
        
        # Call LLM API
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            # Parse JSON response
            result = json.loads(response.choices[0].message.content)
            
            # Ensure all required fields are present
            if 'insights' not in result:
                result['insights'] = "Insights not available."
            if 'common_topics' not in result:
                result['common_topics'] = []
            if 'patterns' not in result:
                result['patterns'] = []
                
            return result
            
        except Exception as e:
            print(f"Error in generating insights: {str(e)}")
            # Provide a fallback response in case of errors
            return {
                "insights": f"Error generating insights: {str(e)}",
                "common_topics": [],
                "patterns": []
            }

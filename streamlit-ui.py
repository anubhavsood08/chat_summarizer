import streamlit as st
import requests
import json
import uuid
import datetime
from typing import List, Dict, Any, Optional
import time

# API Configuration
API_URL = "http://localhost:8000"  # Update this to your deployed API URL

# Session state initialization
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "summary" not in st.session_state:
    st.session_state.summary = None

if "conversations" not in st.session_state:
    st.session_state.conversations = []

# Set page title and layout
st.set_page_config(
    page_title="Chat Summarization App",
    layout="wide",
    initial_sidebar_state="expanded"
)

# UI Header
st.title("Chat Summarization and Insights")
st.sidebar.title("Options")

# Functions for API interaction
def fetch_user_conversations():
    """Fetch conversations for the current user."""
    try:
        response = requests.get(
            f"{API_URL}/users/{st.session_state.user_id}/chats",
            params={"page": 1, "limit": 20}
        )
        if response.status_code == 200:
            return response.json()["data"]
        else:
            st.error(f"Failed to fetch conversations: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []

def create_new_conversation(title: str = None):
    """Create a new conversation."""
    try:
        if not title:
            title = f"Chat {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
        response = requests.post(
            f"{API_URL}/chats",
            json={
                "conversation_id": str(uuid.uuid4()),
                "user_id": st.session_state.user_id,
                "title": title,
                "messages": []
            }
        )
        if response.status_code == 201:
            conversation = response.json()
            st.session_state.conversation_id = conversation["conversation_id"]
            st.session_state.messages = []
            return conversation
        else:
            st.error(f"Failed to create conversation: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def load_conversation(conversation_id: str):
    """Load a specific conversation."""
    try:
        response = requests.get(f"{API_URL}/chats/{conversation_id}")
        if response.status_code == 200:
            conversation = response.json()
            st.session_state.conversation_id = conversation["conversation_id"]
            st.session_state.messages = conversation["messages"]
            st.session_state.summary = conversation.get("summary")
            return conversation
        else:
            st.error(f"Failed to load conversation: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def send_message(content: str, sender_name: str = "User"):
    """Send a message to the current conversation."""
    if not st.session_state.conversation_id:
        conversation = create_new_conversation()
        if not conversation:
            return False
    
    try:
        message = {
            "conversation_id": st.session_state.conversation_id,
            "message": {
                "sender_id": st.session_state.user_id,
                "sender_name": sender_name,
                "content": content
            }
        }
        
        response = requests.post(f"{API_URL}/chats/message", json=message)
        if response.status_code == 200:
            conversation = response.json()
            st.session_state.messages = conversation["messages"]
            return True
        else:
            st.error(f"Failed to send message: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False

def generate_summary():
    """Generate a summary for the current conversation."""
    if not st.session_state.conversation_id:
        st.error("No active conversation to summarize.")
        return None
    
    try:
        with st.spinner("Generating summary..."):
            response = requests.post(
                f"{API_URL}/chats/summarize",
                json={
                    "conversation_id": st.session_state.conversation_id,
                    "additional_instructions": "Focus on key points and action items."
                }
            )
            if response.status_code == 200:
                summary_data = response.json()
                st.session_state.summary = summary_data["summary"]
                return summary_data
            else:
                st.error(f"Failed to generate summary: {response.text}")
                return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def get_insights():
    """Get insights from recent conversations."""
    try:
        with st.spinner("Generating insights..."):
            response = requests.post(
                f"{API_URL}/chats/insights",
                json={"user_id": st.session_state.user_id, "limit": 5}
            )
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to get insights: {response.text}")
                return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Sidebar for conversation management
with st.sidebar:
    # Refresh conversations list
    if st.button("Refresh Conversations"):
        st.session_state.conversations = fetch_user_conversations()
    
    # Create new conversation
    new_chat_title = st.text_input("New Chat Title (optional)")
    if st.button("New Conversation"):
        new_conversation = create_new_conversation(new_chat_title)
        if new_conversation:
            st.success("New conversation created!")
            st.session_state.conversations = fetch_user_conversations()
    
    # List existing conversations
    st.subheader("Your Conversations")
    if not st.session_state.conversations:
        st.session_state.conversations = fetch_user_conversations()
    
    for convo in st.session_state.conversations:
        chat_title = convo.get("title", f"Chat {convo['conversation_id'][:8]}")
        if st.button(chat_title, key=convo["conversation_id"]):
            load_conversation(convo["conversation_id"])
            st.experimental_rerun()
    
    # Generate insights from conversations
    st.subheader("Conversation Insights")
    if st.button("Generate Insights"):
        insights = get_insights()
        if insights:
            st.subheader("Insights")
            st.write(insights.get("insights", "No insights available"))
            
            st.subheader("Common Topics")
            for topic in insights.get("common_topics", []):
                st.write(f"- {topic}")
            
            st.subheader("Communication Patterns")
            for pattern in insights.get("patterns", []):
                st.write(f"- {pattern}")

# Main chat interface
col1, col2 = st.columns([2, 1])

with col1:
    # Display conversation title if available
    if st.session_state.conversation_id:
        current_convo = next(
            (c for c in st.session_state.conversations 
             if c["conversation_id"] == st.session_state.conversation_id),
            None
        )
        if current_convo:
            st.header(current_convo.get("title", f"Chat {st.session_state.conversation_id[:8]}"))
        else:
            st.header("Current Chat")
    else:
        st.header("Start a new conversation")
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            sender = msg.get("sender_name", msg.get("sender_id", "Unknown"))
            content = msg.get("content", "")
            
            # Different styling for user vs others
            if msg.get("sender_id") == st.session_state.user_id:
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
                    <div style="background-color: #1E88E5; color: white; padding: 10px; border-radius: 10px; max-width: 75%;">
                        <b>{sender}</b><br>{content}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">
                    <div style="background-color: #383838; color: white; padding: 10px; border-radius: 10px; max-width: 75%;">
                        <b>{sender}</b><br>{content}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Message input
    user_name = st.text_input("Your Name", "User")
    message_text = st.text_area("Message", height=100)
    
    col1a, col1b, col1c = st.columns([1, 1, 1])
    with col1a:
        if st.button("Send Message"):
            if message_text:
                if send_message(message_text, user_name):
                    st.experimental_rerun()
            else:
                st.warning("Please enter a message")
    
    with col1b:
        if st.button("Bot Response (Mock)"):
            if st.session_state.conversation_id:
                bot_response = "This is a simulated response from the bot. In a real application, you would integrate with your bot service or LLM here."
                send_message(bot_response, "Bot")
                st.experimental_rerun()

    with col1c:
        if st.button("Generate Summary"):
            summary = generate_summary()
            st.experimental_rerun()

with col2:
    # Display conversation summary
    st.subheader("Conversation Summary")
    if st.session_state.summary:
        st.markdown(st.session_state.summary)
    else:
        st.write("No summary available. Generate a summary to see it here.")

# Footer
st.markdown("---")
st.markdown("Chat Summarization API Demo | Powered by FastAPI and LLM")

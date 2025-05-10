import streamlit as st
from datetime import datetime
from openai import OpenAI
import os
from typing import List, Dict, Any

# Load API key from environment variable
API_KEY = os.getenv('OPENAI_API_KEY')
if not API_KEY:
    raise ValueError("OpenAI API key not found in environment variables")

# Initialize OpenAI client
client = OpenAI(api_key=API_KEY)

# Backend Prompt Engineering Configuration
SYSTEM_PROMPTS = {
    "default": """You are a helpful AI assistant. Please:
1. Provide clear and concise answers
2. Be friendly and professional
3. If you're unsure, admit it
4. Keep responses focused and relevant
5. Provide short answers in 1 paragraph, only provide bullet point when users ask for instruction""",
   
    "retirement_assistant": """You are a caring and patient retirement community assistant. Please:
1. Provide clear and simple explanations, avoiding jargon unless necessary, and always explain any technical terms.
2. Speak in a warm, conversational tone, as though you are talking to a beloved elder.
3. Be patient and polite, ensuring your responses are easy to follow and reassuring.
4. Use examples and analogies from daily life to clarify concepts.
5. Offer step-by-step instructions for tasks involving technology or health management.
6. Make your responses as human-like and understanding as possible, acknowledging concerns or confusion gently.

### Three Key Scenarios You Handle:
1. **Technology-related queries:** For straightforward questions like "How do I install an app on my phone?", use the user's provided information (such as iPhone or Android) to give tailored responses. 

2. **Wellness and nutrition inquiries:** For questions such as "How do I increase Vitamin C intake?", use user information (e.g. their dietary preference) and your expertise in nutrition and wellness to give tailored responses. 

### Important: Avoid giving answers when users ask about complex medication, treatment, diagnosis, symptoms, or medical conditions."""
}

def select_prompt_by_context(user_input: str) -> str:
    """Select appropriate system prompt based on user input."""
    try:
        # Check for health or technology related keywords
        health_tech_keywords = ['health', 'app', 'phone', 'vitamin', 'diet', 'exercise', 'install', 'setup', 'computer']
        if any(keyword in user_input.lower() for keyword in health_tech_keywords):
            return SYSTEM_PROMPTS["retirement_assistant"]
            
        if any(tech_word in user_input.lower() for tech_word in ['code', 'programming', 'error', 'bug', 'function']):
            return SYSTEM_PROMPTS["technical"]
        elif any(creative_word in user_input.lower() for creative_word in ['story', 'write', 'creative', 'imagine']):
            return SYSTEM_PROMPTS["creative"]
        return SYSTEM_PROMPTS["default"]
    except Exception as e:
        st.error(f"Error in prompt selection: {str(e)}")
        return SYSTEM_PROMPTS["default"]

def get_context_data() -> str:
    """Generate context information for the current session."""
    try:
        message_count = len(st.session_state.all_sessions[st.session_state.current_session_id])
        return f"""
        Current time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        Session length: {message_count} messages
        """
    except Exception as e:
        return f"""
        Current time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        Session length: 0 messages
        """

# Initialize session state variables
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = {}
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "refresh" not in st.session_state:
    st.session_state.refresh = False

def start_new_session() -> None:
    """Initialize a new chat session with timestamp as ID."""
    session_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.all_sessions[session_id] = []
    st.session_state.current_session_id = session_id
    st.session_state.refresh = not st.session_state.refresh

def generate_gpt_response(prompt: List[Dict[str, str]], user_input: str) -> str:
    """Generate a response using OpenAI GPT API with backend prompt engineering."""
    try:
        # Select appropriate system prompt based on context
        system_prompt = select_prompt_by_context(user_input)
        context_data = get_context_data()
        
        # Initialize the engineered prompt with stronger enforcement and formatting instructions
        engineered_prompt = [
            {"role": "system", "content": system_prompt + """
IMPORTANT: Always follow these guidelines strictly:
1. Keep responses concise and in a single paragraph unless specifically asked for bullet points
2. When providing bullet points or numbered lists:
   - Place each point on a new line
   - Add a blank line between points
   - Use clear numbering or bullet points

Example format for lists:
1. First point

2. Second point

3. Third point"""
            },
            {"role": "system", "content": context_data}
        ]
        
        # Add conversation history or current input
        if prompt:
            engineered_prompt.extend(prompt)
        else:
            engineered_prompt.append({"role": "user", "content": user_input})
        
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=engineered_prompt,
            max_tokens=150,
            temperature=0.7
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        error_msg = f"Error calling OpenAI API: {str(e)}"
        st.error(error_msg)
        return f"Sorry, I encountered an error. Please try again. Error: {str(e)}"

# Initialize first session if none exists
if not st.session_state.all_sessions:
    start_new_session()

# Sidebar configuration
with st.sidebar:
    st.header("Chat Settings")
    
    # Session management
    if st.button("Start New Session"):
        start_new_session()

    session_ids = list(st.session_state.all_sessions.keys())
    selected_session_id = st.selectbox(
        "Select Session", 
        session_ids, 
        index=session_ids.index(st.session_state.current_session_id)
    )

    if selected_session_id != st.session_state.current_session_id:
        st.session_state.current_session_id = selected_session_id
        st.session_state.refresh = not st.session_state.refresh

    # Appearance settings
    font_size = st.selectbox("Select Font Size", ["Small", "Medium", "Large"])
    background_color = st.text_input(
        "Background Color (e.g., 'lightblue', '#f0f0f0')", 
        value="white"
    )
    text_color = st.text_input(
        "Text Color (e.g., 'black', '#333333')", 
        value="black"
    )

# Define font size styles
font_styles = {
    "Small": "font-size: 14px;",
    "Medium": "font-size: 16px;",
    "Large": "font-size: 20px;"
}

# Apply selected styles
selected_font_style = font_styles[font_size]
selected_bg_style = f"background-color: {background_color};"
selected_text_style = f"color: {text_color};"

# Main chat interface
st.title("Customizable Chatbot Interface")

# Display chat history
current_session_history = st.session_state.all_sessions[st.session_state.current_session_id]
for message in current_session_history:
    style = f"{selected_font_style} {selected_bg_style} {selected_text_style} padding: 8px; border-radius: 5px; margin-bottom: 5px; max-width: 80%;"
    role = "User" if message["role"] == "user" else "Assistant"
    st.markdown(
        f"<div class='{message['role']}-message' style='{style}'><strong>{role}:</strong> {message['text']}</div>",
        unsafe_allow_html=True
    )

# Initialize the previous input state if it doesn't exist
if "previous_input" not in st.session_state:
    st.session_state.previous_input = ""

# Chat input and processing
user_input = st.text_input("Type here...", key="user_input")
send_button = st.button("Send")

# Handle both Enter key and Send button
if (user_input and send_button) or (user_input and user_input != st.session_state.previous_input):
    # Add user message to history
    current_session_history.append({
        "role": "user", 
        "text": user_input,
        "content": user_input
    })

    # Prepare conversation history
    conversation_history = [
        {"role": msg["role"], "content": msg["text"]}
        for msg in current_session_history
    ]

    # Generate response with backend prompt engineering
    bot_response = generate_gpt_response(conversation_history, user_input)
    current_session_history.append({
        "role": "assistant", 
        "text": bot_response,
        "content": bot_response
    })
    
    # Update session state
    st.session_state.all_sessions[st.session_state.current_session_id] = current_session_history
    st.session_state.previous_input = user_input
    st.session_state.refresh = not st.session_state.refresh
    
    # Rerun to update the interface
    st.rerun()


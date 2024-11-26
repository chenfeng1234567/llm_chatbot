import streamlit as st
from datetime import datetime
from openai import OpenAI


client = OpenAI(api_key=api_key)
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = {}  # Dictionary to store multiple sessions
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "refresh" not in st.session_state:
    st.session_state.refresh = False  # A flag to trigger UI refresh

# Function to start a new session
def start_new_session():
    session_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.all_sessions[session_id] = []  # Initialize empty chat history
    st.session_state.current_session_id = session_id
    st.session_state.refresh = not st.session_state.refresh  # Toggle refresh flag

# Check if there are no sessions yet, start one
if not st.session_state.all_sessions:
    start_new_session()

# Sidebar for settings, session control, and session navigation
with st.sidebar:
    st.header("Chat Settings")
    
    # Button to start a new session
    if st.button("Start New Session"):
        start_new_session()

    # Dropdown to select a session to view
    session_ids = list(st.session_state.all_sessions.keys())
    selected_session_id = st.selectbox("Select Session", session_ids, index=session_ids.index(st.session_state.current_session_id))

    # Update current session when a different session is selected
    if selected_session_id != st.session_state.current_session_id:
        st.session_state.current_session_id = selected_session_id
        st.session_state.refresh = not st.session_state.refresh  # Toggle refresh flag

    # Font size selection
    font_size = st.selectbox("Select Font Size", ["Small", "Medium", "Large"])

    # Input fields for background and text color
    background_color = st.text_input("Background Color (e.g., 'lightblue', '#f0f0f0')", value="white")
    text_color = st.text_input("Text Color (e.g., 'black', '#333333')", value="black")

# Define font size styles
font_styles = {
    "Small": "font-size: 14px;",
    "Medium": "font-size: 16px;",
    "Large": "font-size: 20px;"
}

# Set selected font size, background color, and text color
selected_font_style = font_styles[font_size]
selected_bg_style = f"background-color: {background_color};"
selected_text_style = f"color: {text_color};"

st.title("Customizable Chatbot Interface")

# Display chat history for the selected session
current_session_history = st.session_state.all_sessions[st.session_state.current_session_id]
for message in current_session_history:
    if message["role"] == "user":
        st.markdown(f"<div class='user-message' style='{selected_font_style} {selected_bg_style} {selected_text_style} padding: 8px; border-radius: 5px; margin-bottom: 5px; max-width: 80%;'><strong>User:</strong> {message['text']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='assistant-message' style='{selected_font_style} {selected_bg_style} {selected_text_style} padding: 8px; border-radius: 5px; margin-bottom: 5px; max-width: 80%;'><strong>Assistant:</strong> {message['text']}</div>", unsafe_allow_html=True)

# Function to generate a response using OpenAI GPT API
def generate_gpt_response(prompt):
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Replace with "gpt-4" if desired
            messages=prompt,
            max_tokens=200,
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# Text input at the bottom
user_input = st.text_input("Type here...", "")
if st.button("Send"):
    if user_input:
        # Add user message to the current session history
        current_session_history.append({"role": "user", "text": user_input})

        # Prepare the prompt for OpenAI GPT API
        prompt = [{"role": "system", "content": "You are a helpful assistant."}]
        for message in current_session_history:
            prompt.append({"role": message["role"], "content": message["text"]})
        prompt.append({"role": "user", "content": user_input})

        # Generate response using OpenAI GPT API
        bot_response = generate_gpt_response(prompt)

        # Add bot response to the current session history
        current_session_history.append({"role": "assistant", "text": bot_response})

        # Update the session history with the new messages
        st.session_state.all_sessions[st.session_state.current_session_id] = current_session_history

        # Clear the input box
        st.session_state.refresh = not st.session_state.refresh


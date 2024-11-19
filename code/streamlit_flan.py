import streamlit as st
from datetime import datetime
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Load FLAN-T5 Base model and tokenizer
@st.cache_resource  # Cache the model to avoid reloading on every app rerun
def load_flan_model():
    model_name = "google/flan-t5-base"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    return model, tokenizer

model, tokenizer = load_flan_model()

# Initialize session storage for multiple sessions
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = {}  # Dictionary to store multiple sessions
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "refresh" not in st.session_state:
    st.session_state.refresh = False  # A flag to trigger UI refresh

# Function to start a new session
def start_new_session():
    # Create a unique session ID based on timestamp
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

# Text input at the bottom
user_input = st.text_input("Type here...", "")
if st.button("Send"):
    if user_input:
        # Add user message to the current session history
        current_session_history.append({"role": "user", "text": user_input})
        
        # Generate a response using the FLAN-T5 model
        input_ids = tokenizer.encode(user_input, return_tensors="pt")
        # output_ids = model.generate(input_ids)
        output_ids = model.generate(input_ids, max_length=50, num_return_sequences=1, temperature=0.7)
        bot_response = tokenizer.decode(output_ids[0], skip_special_tokens=True)

        # Add bot response to the current session history
        current_session_history.append({"role": "assistant", "text": bot_response})

        # Update the session history with the new messages
        st.session_state.all_sessions[st.session_state.current_session_id] = current_session_history

        # Clear user input by toggling the refresh flag
        st.session_state.refresh = not st.session_state.refresh  # Toggle refresh flag

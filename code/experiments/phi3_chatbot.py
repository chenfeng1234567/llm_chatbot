import streamlit as st
from datetime import datetime
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os

# Suppress tokenizer parallelism warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Load the model and tokenizer
@st.cache_resource  # Cache the model to avoid reloading on every app rerun
def load_phi3_model():
    model_name = "microsoft/Phi-3-mini-4k-instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True)

    # Ensure the tokenizer has a pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Use CPU for better performance on Apple Silicon
    device = torch.device("cpu")  # Switch back to CPU
    model = model.to(device)

    return model, tokenizer, device

model, tokenizer, device = load_phi3_model()

# Initialize session storage for multiple sessions
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = {}  # Dictionary to store multiple sessions
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "user_input" not in st.session_state:
    st.session_state.user_input = ""  # Track the input text

# Function to start a new session
def start_new_session():
    session_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.all_sessions[session_id] = []  # Initialize empty chat history
    st.session_state.current_session_id = session_id

# Check if there are no sessions yet, start one
if not st.session_state.all_sessions:
    start_new_session()

# Sidebar for settings
with st.sidebar:
    st.header("Chat Settings")
    if st.button("Start New Session"):
        start_new_session()

    session_ids = list(st.session_state.all_sessions.keys())
    selected_session_id = st.selectbox("Select Session", session_ids, index=session_ids.index(st.session_state.current_session_id))

    if selected_session_id != st.session_state.current_session_id:
        st.session_state.current_session_id = selected_session_id

# Display chat history
current_session_history = st.session_state.all_sessions[st.session_state.current_session_id]
for message in current_session_history:
    if message["role"] == "user":
        st.markdown(f"**User:** {message['text']}")
    else:
        st.markdown(f"**Assistant:** {message['text']}")

# Text input and response generation
user_input = st.text_input("Type here...", "")
if st.button("Send"):
    if user_input:
        # Add user message
        current_session_history.append({"role": "user", "text": user_input})

        # Generate response
        prompt = f"User: {user_input}\nAssistant:"
        max_input_length = 256  # Limit input length
        input_ids = tokenizer.encode(prompt, return_tensors="pt", max_length=max_input_length, truncation=True).to(device)
        attention_mask = input_ids.ne(tokenizer.pad_token_id).to(device)

        output_ids = model.generate(
            input_ids, 
            attention_mask=attention_mask, 
            max_length=200, 
            temperature=0.7, 
            do_sample=True
        )
        bot_response = tokenizer.decode(output_ids[0], skip_special_tokens=True).replace(prompt, "").strip()

        # Add bot response
        current_session_history.append({"role": "assistant", "text": bot_response})

        # Clear input box
        st.session_state.user_input = ""

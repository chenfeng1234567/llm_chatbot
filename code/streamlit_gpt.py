# To run the app, enter the following command in the terminal:
# streamlit run streamlit_gpt.py

import streamlit as st
from datetime import datetime
from openai import OpenAI
import re
import os
import sys
import tempfile
from dotenv import load_dotenv

#########################
# CONFIGURATION & SETUP #
#########################

# Load environment variables
load_dotenv()

# Get API key from Streamlit secrets or environment variables
try:
    api_key = st.secrets["openai"]["api_key"]
except (KeyError, FileNotFoundError):
    # Fall back to environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OpenAI API key not found! Please add it to your environment variables or Streamlit secrets.")
        st.stop()

if not api_key:
    api_key = st.text_input("Enter your OpenAI API key:", type="password")
    if not api_key:
        st.warning("Please enter an OpenAI API key to continue.")
        st.stop()

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

#######################
# LOAD PROMPT FILES   #
#######################

# Helper function to load text from files
def load_text_file(filepath):
    """Loads text content from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        st.error(f"File not found: {filepath}")
        return f"Error loading file: {filepath}"
    except Exception as e:
        st.error(f"Error reading file {filepath}: {str(e)}")
        return f"Error loading content: {str(e)}"

# Determine base path
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    base_path = os.path.dirname(sys.executable)
else:
    # Running as script
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define prompt file paths
prompt_dir = os.path.join(base_path, "prompts")
default_prompt_path = os.path.join(prompt_dir, "default_prompt.txt")
retirement_prompt_path = os.path.join(prompt_dir, "retirement_assistant_prompt.txt")
schedule_prompt_path = os.path.join(prompt_dir, "schedule_menu_prompt.txt")
questions_path = os.path.join(prompt_dir, "example_questions.txt")
transcribe_prompt_path = os.path.join(prompt_dir, "transcribe_prompt.txt")

# Pre-defined system prompts for different contexts
SYSTEM_PROMPTS = {
    "default": load_text_file(default_prompt_path),
    "retirement_assistant": load_text_file(retirement_prompt_path),
    "schedule_menu": load_text_file(schedule_prompt_path)
}

# Load example questions from file
example_questions_text = load_text_file(questions_path)
example_questions = [q.strip() for q in example_questions_text.split('\n') if q.strip()]

####################
# UTILITY FUNCTIONS #
####################

# Transcribe audio using OpenAI Whisper API
def transcribe_audio(audio_bytes):
    """Transcribes audio bytes using OpenAI's Whisper API with elderly-friendly prompting."""
    try:
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name

        # Open the temporary file and transcribe
        with open(tmp_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                prompt=load_text_file(transcribe_prompt_path)
            )
        
        # Clean up the temporary file
        os.unlink(tmp_file_path)
        
        return transcript.text.strip()
    
    except Exception as e:
        st.error(f"Error transcribing audio: {str(e)}")
        return ""

# Select appropriate system prompt based on user input
def select_prompt_by_context(user_input: str) -> str:
    """Determines which system prompt to use based on keywords in user input."""
    try:
        schedule_menu_keywords = ['menu', 'dining', 'breakfast', 'lunch', 'dinner', 'schedule', 'activity', 'activities', "today's"]
        health_tech_keywords = ['health', 'app', 'phone', 'vitamin', 'diet', 'exercise', 'install', 'setup', 'computer']
        
        if any(keyword in user_input.lower() for keyword in schedule_menu_keywords):
            return SYSTEM_PROMPTS["schedule_menu"]
        if any(keyword in user_input.lower() for keyword in health_tech_keywords):
            return SYSTEM_PROMPTS["retirement_assistant"]
        return SYSTEM_PROMPTS["default"]
    except Exception as e:
        st.error(f"Error in prompt selection: {str(e)}")
        return SYSTEM_PROMPTS["default"]

# Generate context information for the current session
def get_context_data() -> str:
    """Creates context data about the current session for the AI."""
    try:
        message_count = len(st.session_state["all_sessions"][st.session_state["current_session_id"]])
        return f"""
        Current time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        Session length: {message_count} messages
        """
    except Exception as e:
        return f"""
        Current time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        Session length: 0 messages
        """

# Remove markdown formatting from text
def sanitize_markdown(text):
    """Removes common Markdown symbols from the given text."""
    # Remove bold/italic markers (* or _)
    text = re.sub(r'[*_]+', '', text)
    return text
    
# Clean up follow-up questions formatting
def sanitize_followup_questions(questions):
    """Removes leading numbers and formatting from questions."""
    sanitized = []
    for question in questions:
        # Remove leading numbers and whitespace
        sanitized.append(question.lstrip("1234567890. ").strip())
    return sanitized

# Generate follow-up questions using GPT
def generate_followup_questions(response):
    """Creates relevant follow-up questions based on the assistant's response."""
    prompt = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Generate three follow-up questions that the user may want to ask within 10 words based on this response:"},
        {"role": "assistant", "content": response}
    ]
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=prompt,
            max_tokens=100,
            temperature=0.7,
        )
        followup_text = completion.choices[0].message.content.strip()
        raw_questions = followup_text.split("\n")  # Split lines
        return sanitize_followup_questions(raw_questions)
    except Exception as e:
        return [f"Error generating follow-up questions: {e}"]

# Force Streamlit to rerun the app
def force_rerun():
    """Forces Streamlit to rerun the app, refreshing the UI."""
    st.rerun()
    
#######################
# UI THEME MANAGEMENT #
#######################
    
# Update chat display to apply consistent font styling
def update_chat_display():
    """Renders the chat history with appropriate styling."""
    with chat_placeholder.container():
        for message in current_session_history:
            if message["role"] == "user":
                st.markdown(
                    f"<div class='user-message' style='{selected_font_style} background-color: {selected_colors['background']}; color: {selected_colors['text']}; padding: 8px; border-radius: 5px; margin-bottom: 5px; max-width: 80%;'><strong>👤 User:</strong> {message['text']}</div>",
                    unsafe_allow_html=True
                )
            else:
                # Render Assistant's response as custom HTML
                formatted_response = message['text'].replace("\n", "<br>")  # Replace newlines with <br> for HTML formatting
                st.markdown(
                    f"<div class='assistant-message' style='{selected_font_style} background-color: {selected_colors['background']}; color: {selected_colors['text']}; padding: 8px; border-radius: 5px; margin-bottom: 5px; max-width: 80%;'><strong>🤖 Assistant:</strong> {formatted_response}</div>",
                    unsafe_allow_html=True
                )

########################
# SESSION STATE MANAGEMENT #
########################

# Initialize session state variables
def initialize_session_state():
    """Sets up all necessary session state variables with default values."""
    session_defaults = {
        "current_question": None,       # Currently selected example question
        "current_followups": [],        # Currently active follow-up questions
        "followup_questions": [],       # All generated follow-up questions
        "all_sessions": {},             # To store chat sessions
        "current_session_id": None,     # Current active session ID
        "wide_mode": False,             # Layout mode flag
        "theme": "Light",               # Current theme setting
        "font_size": "Medium",          # Current font size setting
        "is_thinking": False,           # Flag to track response generation
        "show_example_questions": True, # Flag to show/hide example questions
        "color_theme": "White",         # Current color theme setting
        "is_transcribing": False,       # Flag to track transcription process
        "last_audio_input": None,       # Store last audio input for processing
        "transcription_status": "",     # Status message for transcription
        "current_input": "",            # Current text in input field
        "last_audio_input_processed": 0, # Counter to force audio widget reset
    }
    for key, default_value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# Function to start a new chat session
def start_new_session():
    """Creates a new chat session with a unique timestamp ID."""
    session_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state["all_sessions"][session_id] = []  # Initialize empty chat history
    st.session_state["current_session_id"] = session_id
    st.session_state["show_example_questions"] = True
    st.session_state["current_question"] = None  # Reset current question
    st.session_state["current_followups"] = []  # Reset follow-up questions
    st.session_state["is_thinking"] = False
    st.session_state["transcription_status"] = ""  # Clear transcription status
    st.session_state["last_audio_input"] = None  # Clear audio input
    st.session_state["current_input"] = ""  # Clear current input
    st.session_state["last_audio_input_processed"] = 0  # Reset audio widget counter

######################
# PROCESSING FUNCTIONS #
######################

# Process user input and generate response
def process_input(input_text):
    """Processes user input, calls OpenAI API, and updates chat history."""
    current_session_history.append({"role": "user", "text": input_text})
    st.session_state["is_thinking"] = True
    thinking_placeholder.markdown("## 🤔 **Assistant is thinking... Please wait.**")

    try:
        # Select appropriate system prompt and get context
        system_prompt = select_prompt_by_context(input_text)
        context_data = get_context_data()
        
        # Prepare messages for the API call
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": context_data}
        ]
        
        # Add conversation history
        for message in current_session_history:
            messages.append({"role": message["role"], "content": message["text"]})

        # Generate response
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=400,
            temperature=0.1
        )
        bot_response = response.choices[0].message.content
        bot_response = sanitize_markdown(bot_response)
        current_session_history.append({"role": "assistant", "text": bot_response})
        update_chat_display()

        # Generate follow-up questions
        st.session_state["current_followups"] = generate_followup_questions(bot_response)

    except Exception as e:
        current_session_history.append({"role": "assistant", "text": f"Error: {e}"})
        st.session_state["current_followups"] = []

    # Complete cleanup after processing
    st.session_state["is_thinking"] = False
    st.session_state["show_example_questions"] = False  # Always hide example questions after any input
    st.session_state["transcription_status"] = ""  # Clear transcription status
    st.session_state["last_audio_input"] = None  # Clear audio input
    st.session_state["current_input"] = ""  # Clear current input
    thinking_placeholder.empty()
    force_rerun()  # Force rerun to update UI

# Handle audio input processing
def handle_audio_input(audio_bytes):
    """Handles audio input by transcribing it and updating the text input buffer."""
    if audio_bytes and not st.session_state.get("is_transcribing", False):
        st.session_state["is_transcribing"] = True
        st.session_state["transcription_status"] = "🎤 Transcribing audio... Please wait."
        
        try:
            # Transcribe the audio
            transcribed_text = transcribe_audio(audio_bytes)
            
            if transcribed_text:
                # Set transcribed text as current input so it appears in the text field
                st.session_state["current_input"] = transcribed_text
                st.session_state["transcription_status"] = f"✅ Transcribed and ready to send"
            else:
                st.session_state["transcription_status"] = "❌ Could not transcribe audio. Please try again."
                
        except Exception as e:
            st.session_state["transcription_status"] = f"❌ Transcription error: {str(e)}"
        
        st.session_state["is_transcribing"] = False

#####################
# INITIALIZE THE APP #
#####################

# Call the initialization function
initialize_session_state()

# Set page layout dynamically based on mode setting
layout = "wide" if st.session_state["wide_mode"] else "centered"
st.set_page_config(layout=layout)

# Start the first session if none exists
if not st.session_state["all_sessions"]:
    start_new_session()

#################
# SIDEBAR LAYOUT #
#################

# Apply custom CSS to fix select box height
st.markdown(
    """
    <style>
    /* Aggressively target select box heights */
    div[data-baseweb="select"] {
        height: auto !important;
    }
    
    /* Control the button part of select boxes */
    div[data-baseweb="select"] > div {
        height: auto !important;
        min-height: 45px !important; 
        max-height: none !important;
    }
    
    /* Make inner content of select box visible */
    div[data-baseweb="select"] span {
        line-height: 40px !important;
        vertical-align: middle !important;
    }
    
    /* Target the dropdown options */
    div[data-baseweb="popover"] div[role="option"] {
        min-height: 40px !important;
        line-height: 40px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar for settings
with st.sidebar:
    st.markdown("<h2 style='color: black;'>App Settings</h2>", unsafe_allow_html=True)

    # Theme selection - with direct force_rerun call
    theme_selected = st.radio("Theme", ["Light", "Dark"], index=0 if st.session_state["theme"] == "Light" else 1)
    if theme_selected != st.session_state["theme"]:
        st.session_state["theme"] = theme_selected
        force_rerun()

    # Wide mode toggle - with direct force_rerun call
    wide_mode_selected = st.checkbox("Wide Mode", value=st.session_state["wide_mode"])
    if wide_mode_selected != st.session_state["wide_mode"]:
        st.session_state["wide_mode"] = wide_mode_selected
        force_rerun()

    # Start a new session button
    if st.button("Start New Session"):
        start_new_session()
        force_rerun()  # Direct call

    # Session selection dropdown
    session_ids = list(st.session_state["all_sessions"].keys())
    selected_session_id = st.selectbox("Select Session", session_ids, index=session_ids.index(st.session_state["current_session_id"]))
    if selected_session_id != st.session_state["current_session_id"]:
        st.session_state["current_session_id"] = selected_session_id
        force_rerun()

    # Font size selection
    font_size = st.selectbox("Font Size", ["Small", "Medium", "Large", "Extra Large"], 
                           index=["Small", "Medium", "Large", "Extra Large"].index(st.session_state["font_size"]))
    if font_size != st.session_state["font_size"]:
        st.session_state["font_size"] = font_size
        force_rerun()

    # Predefined color themes
    color_options = {
        "White": {"background": "white", "text": "black"},
        "Light Blue": {"background": "lightblue", "text": "darkblue"},
        "Light Grey": {"background": "#f0f0f0", "text": "#333333"},
        "Beige": {"background": "#f5f5dc", "text": "black"}
    }
    color_choice = st.selectbox("Custom Theme Color", list(color_options.keys()), 
                               index=list(color_options.keys()).index(st.session_state.get("color_theme", "White")))
    selected_colors = color_options[color_choice]

    # Update the color theme in session state if changed
    if color_choice != st.session_state.get("color_theme", "White"):
        st.session_state["color_theme"] = color_choice
        force_rerun()

    # Upload background image
    uploaded_image = st.file_uploader("Upload Background Image", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        st.session_state["background_image"] = uploaded_image.getvalue()
        force_rerun()

################
# STYLE SETTINGS #
################

# Apply background image if one is uploaded
if "background_image" in st.session_state and st.session_state["background_image"]:
    import base64

    # Convert the uploaded image to a base64 string
    background_image_base64 = base64.b64encode(st.session_state["background_image"]).decode()

    # Add CSS for the background
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: url("data:image/png;base64,{background_image_base64}") no-repeat center center fixed;
            background-size: cover;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Apply theme-based styles
if st.session_state["theme"] == "Light":
    app_bg_color = "white"
    app_text_color = "black"
    sidebar_bg_color = "#f5f5f5"
    sidebar_text_color = "black"
    input_placeholder_color = "black"
    input_text_color = "black"
else:
    app_bg_color = "#1e1e1e"
    app_text_color = "white"
    sidebar_bg_color = "#333333"
    sidebar_text_color = "white"
    input_placeholder_color = "white"
    input_text_color = "white"

# Font size styles
font_styles = {
    "Small": "font-size: 14px;",
    "Medium": "font-size: 16px;",
    "Large": "font-size: 20px;",
    "Extra Large": "font-size: 24px;"
}
selected_font_style = font_styles[st.session_state["font_size"]]

# Custom CSS styling
if "background_image" not in st.session_state or not st.session_state["background_image"]:
    st.markdown(
        f"""
        <style>
        /* Global font size for the entire app */
        .stApp, .stApp *, .sidebar, .sidebar *, button, input, h1, h2, h3, h4, h5, h6, p, div, span, label {{
            {selected_font_style}
        }}
        
        .appview-container {{
            background-color: {app_bg_color};
            color: {app_text_color};
        }}
        .sidebar .sidebar-content {{
            background-color: {sidebar_bg_color};
            color: {sidebar_text_color};
        }}
        .sidebar .sidebar-content h2, .sidebar-content button {{
            color: {sidebar_text_color};
        }}
        input {{
            color: {input_text_color};
        }}
        input::placeholder {{
            color: {input_placeholder_color};
        }}
        .user-message, .assistant-message, .markdown-response {{
            {selected_font_style}
        }}
        /* Apply font size to all elements inside message containers */
        .user-message *, .assistant-message * {{
            {selected_font_style}
        }}
        button {{
            color: black !important;  /* Force button text color to black */
        }}
        .stButton > button {{
            color: black !important; /* Ensure button text is black */
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

###############
# MAIN APP UI #
###############

# Main App Title
st.title("Retirenet Chatbot")

# Get current session history
current_session_history = st.session_state["all_sessions"][st.session_state["current_session_id"]]

# Display chat history dynamically
chat_placeholder = st.empty()
with chat_placeholder.container():
    for message in current_session_history:
        if message["role"] == "user":
            st.markdown(f"<div class='user-message' style='{selected_font_style} background-color: {selected_colors['background']}; color: {selected_colors['text']}; padding: 8px; border-radius: 5px; margin-bottom: 5px; max-width: 80%;'><strong>👤 User:</strong> {message['text']}</div>", unsafe_allow_html=True)
        else:
            formatted_response = message['text'].replace("\n", "<br>")  # Replace newlines with <br> for HTML formatting
            st.markdown(f"<div class='assistant-message' style='{selected_font_style} background-color: {selected_colors['background']}; color: {selected_colors['text']}; padding: 8px; border-radius: 5px; margin-bottom: 5px; max-width: 80%;'><strong>🤖 Assistant:</strong> {formatted_response}</div>", unsafe_allow_html=True)

# Placeholder for "Thinking..." message
thinking_placeholder = st.empty()

# Show thinking indicator when processing
if st.session_state.get("is_thinking", False):
    thinking_placeholder.markdown("## 🤔 **Assistant is thinking... Please wait.**")
elif st.session_state.get("is_transcribing", False):
    thinking_placeholder.markdown("## 🎤 **Transcribing your voice... Please wait.**")

# Display example questions for new sessions
if st.session_state.get("show_example_questions", True) and len(current_session_history) == 0:
    st.markdown("### Example Questions")

    # Render example questions dynamically
    for i, question in enumerate(example_questions):
        if st.button(question, key=f"example_{i}"):
            # Immediate cleanup before processing
            st.session_state["transcription_status"] = ""
            st.session_state["last_audio_input"] = None
            st.session_state["current_input"] = ""
            st.session_state["last_audio_input_processed"] += 1
            process_input(question)

# Process any selected question
if st.session_state.get("selected_question"):
    question = st.session_state["selected_question"]
    st.session_state["show_example_questions"] = False  # Hide example questions
    st.session_state["current_question"] = question
    st.session_state["current_followups"] = []  # Clear follow-up questions
    st.session_state["is_thinking"] = True  # Indicate processing
    # Immediate cleanup before processing
    st.session_state["transcription_status"] = ""
    st.session_state["last_audio_input"] = None
    st.session_state["current_input"] = ""
    st.session_state["last_audio_input_processed"] += 1
    process_input(question)  # Process the question
    st.session_state["selected_question"] = None  # Clear selected question

# Show transcription status if there is one
if st.session_state.get("transcription_status", ""):
    st.markdown(f"**{st.session_state['transcription_status']}**")

# Voice input button with dynamic key to force reset
audio_reset_key = f"audio_input_{len(current_session_history)}_{st.session_state.get('last_audio_input_processed', 0)}"
audio_input = st.audio_input(
    "Record your question:",
    key=audio_reset_key,
    disabled=st.session_state.get("is_thinking", False) or st.session_state.get("is_transcribing", False)
)

# Process audio input when new audio is recorded
if audio_input is not None:
    audio_bytes = audio_input.read()
    if audio_bytes != st.session_state.get("last_audio_input"):
        st.session_state["last_audio_input"] = audio_bytes
        handle_audio_input(audio_bytes)

# Input form for proper submission handling
with st.form(key="input_form", clear_on_submit=True):
    # Get current input value (either from typing or transcription)
    input_value = st.session_state.get("current_input", "")
    
    user_input = st.text_input(
        "Or type your question:",
        value=input_value,
        placeholder="Type your message and press Enter, or use voice input above...",
        disabled=st.session_state.get("is_thinking", False) or st.session_state.get("is_transcribing", False)
    )
    
    submitted = st.form_submit_button(
        "Enter",
        disabled=st.session_state.get("is_thinking", False) or st.session_state.get("is_transcribing", False)
    )
    
    if submitted and user_input.strip():
        # Immediate cleanup before processing
        st.session_state["transcription_status"] = ""  # Clear transcription status
        st.session_state["last_audio_input"] = None  # Clear audio input
        st.session_state["current_input"] = ""  # Clear current input
        st.session_state["last_audio_input_processed"] += 1  # Force audio widget reset
        # Process the input
        process_input(user_input.strip())

# Follow-Up Questions Section
if st.session_state["current_followups"]:
    st.markdown("### Suggested Follow-Up Questions")
    for i, followup in enumerate(st.session_state["current_followups"]):
        if st.button(followup, key=f"followup_{i}"):
            # Immediate cleanup before processing
            st.session_state["transcription_status"] = ""
            st.session_state["last_audio_input"] = None
            st.session_state["current_input"] = ""
            st.session_state["last_audio_input_processed"] += 1
            st.session_state["current_followups"] = []
            st.session_state["is_thinking"] = True
            process_input(followup)

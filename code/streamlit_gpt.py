# API key
api_key =

import streamlit as st
from datetime import datetime
from openai import OpenAI

# Example questions
example_questions = [
    "What are some exercises for seniors?",
    "How can I make healthy cookies?",
    "What is today's dining menu?",
    "Who can I contact for medical assistance?",
    "What is today's community activity schedule?"
]

# Initialize session state variables explicitly
def initialize_session_state():
    session_defaults = {
        "input_buffer": "",  # Buffer to handle user input
        "current_question": None,  # Currently selected example question
        "current_followups": [],  # Currently active follow-up questions
        "followup_questions": [],  # All generated follow-up questions
        "all_sessions": {},  # To store chat sessions
        "current_session_id": None,
        "wide_mode": False,
        "theme": "Light",
        "font_size": "Medium",
        "is_thinking": False,  # To track response generation
        "show_example_questions": True,  # Track whether to show example questions
    }
    for key, default_value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# Call the initialization function
initialize_session_state()

# Set page layout dynamically
layout = "wide" if st.session_state["wide_mode"] else "centered"
st.set_page_config(layout=layout)

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Function to start a new session
def start_new_session():
    session_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state["all_sessions"][session_id] = []  # Initialize empty chat history
    st.session_state["current_session_id"] = session_id
    st.session_state["show_example_questions"] = True
    st.session_state["current_question"] = None  # Reset current question
    st.session_state["current_followups"] = []  # Reset follow-up questions
    st.session_state["input_buffer"] = ""  # Clear input buffer
    st.session_state["is_thinking"] = False

# Start the first session if none exists
if not st.session_state["all_sessions"]:
    start_new_session()

# Sidebar for settings
with st.sidebar:
    st.markdown("<h2 style='color: black;'>App Settings</h2>", unsafe_allow_html=True)

    # Theme selection
    st.session_state["theme"] = st.radio("Theme", ["Light", "Dark"], index=0 if st.session_state["theme"] == "Light" else 1)

    # Wide mode toggle
    wide_mode_selected = st.checkbox("Wide Mode", value=st.session_state["wide_mode"])
    if wide_mode_selected != st.session_state["wide_mode"]:
        st.session_state["wide_mode"] = wide_mode_selected

    # Start a new session
    if st.button("Start New Session"):
        start_new_session()

    # Select a session to view
    session_ids = list(st.session_state["all_sessions"].keys())
    selected_session_id = st.selectbox("Select Session", session_ids, index=session_ids.index(st.session_state["current_session_id"]))
    if selected_session_id != st.session_state["current_session_id"]:
        st.session_state["current_session_id"] = selected_session_id

    # Font size selection
    st.session_state["font_size"] = st.selectbox("Font Size", ["Small", "Medium", "Large"])

    # Predefined colors
    color_options = {
        "White": {"background": "white", "text": "black"},
        "Light Blue": {"background": "lightblue", "text": "darkblue"},
        "Light Grey": {"background": "#f0f0f0", "text": "#333333"},
        "Beige": {"background": "#f5f5dc", "text": "black"}
    }
    color_choice = st.selectbox("Custom Theme Color", list(color_options.keys()))
    selected_colors = color_options[color_choice]

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
    "Large": "font-size: 20px;"
}
selected_font_style = font_styles[st.session_state["font_size"]]

# Custom CSS styling
st.markdown(
    f"""
    <style>
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

# Main App Title
st.title("Miranet Chatbot")

# Display chat history dynamically
chat_placeholder = st.empty()
current_session_history = st.session_state["all_sessions"][st.session_state["current_session_id"]]
with chat_placeholder.container():
    for message in current_session_history:
        if message["role"] == "user":
            st.markdown(f"<div class='user-message' style='background-color: {selected_colors['background']}; color: {selected_colors['text']}; padding: 8px; border-radius: 5px; margin-bottom: 5px; max-width: 80%;'><strong>User:</strong> {message['text']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='assistant-message' style='background-color: {selected_colors['background']}; color: {selected_colors['text']}; padding: 8px; border-radius: 5px; margin-bottom: 5px; max-width: 80%;'><strong>Assistant:</strong> {message['text']}</div>", unsafe_allow_html=True)

# Placeholder for "Thinking..." message
thinking_placeholder = st.empty()

def sanitize_followup_questions(questions):
    sanitized = []
    for question in questions:
        # Remove leading numbers and whitespace
        sanitized.append(question.lstrip("1234567890. ").strip())
    return sanitized

# Function to generate follow-up questions using GPT
def generate_followup_questions(response):
    prompt = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Generate three follow-up questions within 10 words based on this response:"},
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

# Process user input and generate response
def process_input(input_text):
    current_session_history.append({"role": "user", "text": input_text})

    # Dynamically update the chat history to show the user message immediately
    with chat_placeholder.container():
        for message in current_session_history:
            if message["role"] == "user":
                st.markdown(f"<div class='user-message' style='...'><strong>User:</strong> {message['text']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='markdown-response assistant-message' style='...'><strong>Assistant:</strong> {message['text']}</div>", unsafe_allow_html=True)

    # Show "Thinking..."
    st.session_state["is_thinking"] = True  # Disable input box
    thinking_placeholder.markdown("### Thinking... Please wait.")

    # Prepare prompt
    prompt = [{"role": "system", "content": "You are a helpful assistant."}]
    for message in current_session_history:
        prompt.append({"role": message["role"], "content": message["text"]})

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=prompt,
            max_tokens=200,
            temperature=0.7
        )
        bot_response = response.choices[0].message.content
        current_session_history.append({"role": "assistant", "text": bot_response})

        # Dynamically update chat history
        with chat_placeholder.container():
            for message in current_session_history:
                if message["role"] == "user":
                    st.markdown(f"<div class='user-message' style='...'><strong>User:</strong> {message['text']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='assistant-message' style='...'><strong>Assistant:</strong> {message['text']}</div>", unsafe_allow_html=True)

        # Generate follow-up questions
        st.session_state["current_followups"] = generate_followup_questions(bot_response)

    except Exception as e:
        current_session_history.append({"role": "assistant", "text": f"Error: {e}"})
        st.session_state["current_followups"] = []

    # Clear input buffer
    st.session_state["input_buffer"] = ""
    st.session_state["is_thinking"] = False
    thinking_placeholder.empty()

# Display example questions for new sessions
if st.session_state.get("show_example_questions", True) and len(current_session_history) == 0:
    st.markdown("### Example Questions")
    clicked_question = None  # Temporary variable to detect clicks

    # Render buttons for example questions
    for i, question in enumerate(example_questions):
        if st.button(question, key=f"example_{i}"):
            clicked_question = question  # Store the clicked question

    # If a question is clicked, process it
    if clicked_question:
        st.session_state["show_example_questions"] = False  # Hide example questions
        st.session_state["current_question"] = clicked_question
        st.session_state["current_followups"] = []  # Clear follow-up questions
        st.session_state["input_buffer"] = clicked_question
        st.session_state["is_thinking"] = True
        process_input(clicked_question)

def handle_input():
    """Handles input submission."""
    user_input = st.session_state.get("input_buffer", "").strip()
    if user_input:
        st.session_state["show_example_questions"] = False  # Hide example questions
        process_input(user_input)  # Process the input
        st.session_state["input_buffer"] = ""  # Clear the input buffer after processing

# Input field for user message
st.text_input(
    "Type here...",
    value=st.session_state.get("input_buffer", ""),  # Use "input_buffer" for the input field
    key="input_buffer",  # Link directly to "input_buffer"
    on_change=handle_input,  # Trigger on pressing "Enter" key
    placeholder="Type your message and press Enter...",
    disabled=st.session_state.get("is_thinking", False)
)

# Enter button for message submission
if st.button("Enter"):
    handle_input()  # Trigger the same function as the "Enter" key

# Follow-Up Questions Section
if st.session_state["current_followups"]:
    st.markdown("### Suggested Follow-Up Questions")
    for i, followup in enumerate(st.session_state["current_followups"]):
        if st.button(followup, key=f"followup_{i}"):
            st.session_state["input_buffer"] = followup
            st.session_state["show_example_questions"] = False 
            st.session_state["current_followups"] = []
            st.session_state["is_thinking"] = True
            process_input(followup)
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
        "followup_questions": [],  # To store dynamic follow-up questions
        "all_sessions": {},  # To store chat sessions
        "current_session_id": None,
        "wide_mode": False,
        "theme": "Light",
        "font_size": "Medium",
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
    st.session_state["followup_questions"] = []  # Reset follow-up questions
    st.session_state["input_buffer"] = ""  # Clear input buffer

# Start the first session if none exists
if not st.session_state["all_sessions"]:
    start_new_session()

# Sidebar for settings
with st.sidebar:
    st.markdown("<h2 style='color: inherit;'>App Settings</h2>", unsafe_allow_html=True)

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
    .user-message, .assistant-message {{
        {selected_font_style}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Main App Title
st.title("Miranet Chatbot")

# Display chat history
current_session_history = st.session_state["all_sessions"][st.session_state["current_session_id"]]
for message in current_session_history:
    if message["role"] == "user":
        st.markdown(f"<div class='user-message' style='background-color: {selected_colors['background']}; color: {selected_colors['text']}; padding: 8px; border-radius: 5px; margin-bottom: 5px; max-width: 80%;'><strong>User:</strong> {message['text']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='assistant-message' style='background-color: {selected_colors['background']}; color: {selected_colors['text']}; padding: 8px; border-radius: 5px; margin-bottom: 5px; max-width: 80%;'><strong>Assistant:</strong> {message['text']}</div>", unsafe_allow_html=True)

# Display example questions for new sessions
if len(current_session_history) == 0:
    st.markdown("### Example Questions")
    for question in example_questions:
        if st.button(question):
            st.session_state["input_buffer"] = question

# Input field for user message
user_input = st.text_input("Type here...", value=st.session_state["input_buffer"], key="user_input")

# Function to generate follow-up questions using GPT
def generate_followup_questions(response):
    prompt = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Generate three follow-up questions based on this response:"},
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
        return followup_text.split("\n")  # Assuming GPT returns questions as separate lines
    except Exception as e:
        return [f"Error generating follow-up questions: {e}"]

# Handle user input
if st.button("Send"):
    if user_input.strip():
        # Add user message to history
        current_session_history.append({"role": "user", "text": user_input.strip()})

        # Generate assistant response
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

            # Add assistant response to history
            current_session_history.append({"role": "assistant", "text": bot_response})

            # Generate follow-up questions
            followup_questions = generate_followup_questions(bot_response)
            st.session_state["followup_questions"] = followup_questions
        except Exception as e:
            current_session_history.append({"role": "assistant", "text": f"Error: {e}"})
            st.session_state["followup_questions"] = []

        # Clear input buffer
        st.session_state["input_buffer"] = ""

# Follow-Up Questions Section
if st.session_state["followup_questions"]:
    st.markdown("### Suggested Follow-Up Questions")
    for followup in st.session_state["followup_questions"]:
        if st.button(followup):
            st.session_state["input_buffer"] = followup

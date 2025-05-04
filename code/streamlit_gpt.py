# streamlit run streamlit_gpt.py

import streamlit as st
from datetime import datetime
from openai import OpenAI
import re
import os
from dotenv import load_dotenv
import locale
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8') 

# Load environment variables
load_dotenv()

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

#general prompt for the chatbot
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
7. Do not use any symbols or markdown formatting in your response. Just plain text.

### Three Key Scenarios You Handle:
1. **Technology-related queries:** For straightforward questions like "How do I install an app on my phone?", use the user's provided information (such as iPhone or Android) to give tailored responses. 

2. **Wellness and nutrition inquiries:** For questions such as "How do I increase Vitamin C intake?", use user information (e.g. their dietary preference) and your expertise in nutrition and wellness to give tailored responses. 

### Important: Avoid giving answers when users ask about complex medication, treatment, diagnosis, symptoms, or medical conditions.""",
    
    "schedule_menu": """You are a retirement community assistant providing information about daily menus and activities. When responding:
1. Generate realistic, varied daily menus including breakfast, lunch, and dinner options
2. Create engaging activity schedules with common retirement community events
3. Include specific times, locations, and brief descriptions
4. Ensure activities are age-appropriate and varied (e.g., exercise classes, arts & crafts, social events)
5. Make food options sound appetizing but realistic for a retirement community

Example Menu Format:
Breakfast (7:30 AM - 9:00 AM):
- Main: [Option]
- Side: [Options]
- Beverages: [Options]

Example Activity Format:
9:00 AM - Garden Room: Morning Stretch
10:30 AM - Community Center: [Activity]"""
}

# Select appropriate system prompt based on user input.
def select_prompt_by_context(user_input: str) -> str:
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

# Generate context information for the current session.
def get_context_data() -> str:
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

# Example questions
example_questions = [
    "What are some exercises for seniors?",
    "How can I make healthy cookies?",
    "What's on the dining menu today?",
    "How to set up phone calendar reminder for the event?",
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

    # Upload background image
    uploaded_image = st.file_uploader("Upload Background Image", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        st.session_state["background_image"] = uploaded_image.getvalue()

# Apply background image dynamically
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
    "Large": "font-size: 20px;"
}
selected_font_style = font_styles[st.session_state["font_size"]]

# Custom CSS styling
if "background_image" not in st.session_state or not st.session_state["background_image"]:
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

def sanitize_markdown(text):
    """
    Remove common Markdown symbols from the given text.
    """
    # Remove bold/italic markers (* or _)
    text = re.sub(r'[*_]+', '', text)
    return text
    
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

# Update chat display to apply consistent font styling
def update_chat_display():
    with chat_placeholder.container():
        for message in current_session_history:
            if message["role"] == "user":
                st.markdown(
                    f"<div class='user-message' style='{selected_font_style} background-color: {selected_colors['background']}; color: {selected_colors['text']}; padding: 8px; border-radius: 5px; margin-bottom: 5px; max-width: 80%;'><strong>User:</strong> {message['text']}</div>",
                    unsafe_allow_html=True
                )
            else:
                # Render Assistant's response as custom HTML
                formatted_response = message['text'].replace("\n", "<br>")  # Replace newlines with <br> for HTML formatting
                st.markdown(
                    f"<div class='assistant-message' style='{selected_font_style} background-color: {selected_colors['background']}; color: {selected_colors['text']}; padding: 8px; border-radius: 5px; margin-bottom: 5px; max-width: 80%;'><strong>Assistant:</strong> {formatted_response}</div>",
                    unsafe_allow_html=True
                )

#new prompt with prompt engineering
def process_input(input_text):
    current_session_history.append({"role": "user", "text": input_text})
    st.session_state["is_thinking"] = True
    thinking_placeholder.markdown("### Thinking... Please wait.")

    try:
        # Select appropriate system prompt and get context
        system_prompt = select_prompt_by_context(input_text)
        context_data = get_context_data()
        
        # Prepare engineered prompt
        engineered_prompt = [
            {"role": "system", "content": system_prompt + """
            IMPORTANT: Always follow these guidelines strictly:
            1. Keep responses concise under 200 words and in a single paragraph unless specifically asked for bullet points
            2. When providing bullet points or numbered lists:
            - Place each point on a new line
            - Add a blank line between points
            - Use clear numbering or bullet points"""
            },
            {"role": "system", "content": context_data}
        ]
        # Add conversation history
        for message in current_session_history:
            engineered_prompt.append({"role": message["role"], "content": message["text"]})

        # Generate response
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=engineered_prompt,
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

    st.session_state["is_thinking"] = False
    thinking_placeholder.empty()

# Display example questions for new sessions
if st.session_state.get("show_example_questions", True) and len(current_session_history) == 0:
    st.markdown("### Example Questions")

    # Use custom CSS for the buttons
    st.markdown(
        f"""
        <style>
        .example-question {{
            font-size: {selected_font_style};
            padding: 5px 5px;
            margin: 3px 0;
            background-color: #f8f9fa;
            color: {app_text_color};
            border: 1px solid #ddd;
            border-radius: 5px;
            cursor: pointer;
            display: inline-block;
            text-align: center;
        }}
        .example-question:hover {{
            background-color: #e2e6ea;
            border-color: #007bff;
            color: #007bff;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Render example questions dynamically
    for i, question in enumerate(example_questions):
        if st.button(question, key=f"example_{i}"):
            st.session_state["selected_question"] = question  # Save selected question in session state

# Process the selected question
if st.session_state.get("selected_question"):
    question = st.session_state["selected_question"]
    st.session_state["show_example_questions"] = False  # Hide example questions
    st.session_state["current_question"] = question
    st.session_state["current_followups"] = []  # Clear follow-up questions
    st.session_state["is_thinking"] = True  # Indicate processing
    process_input(question)  # Process the question
    st.session_state["selected_question"] = None  # Clear selected question





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
            st.session_state["show_example_questions"] = False 
            st.session_state["current_followups"] = []
            st.session_state["is_thinking"] = True
            process_input(followup)

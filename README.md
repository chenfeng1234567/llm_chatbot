# Streamlit GPT Chatbot for Retirement Communities

## Overview

This project is a Streamlit-based chatbot designed specifically for retirement communities. Its primary goal is to assist seniors in improving their **information retrieval** and fostering **technology literacy** in an intuitive and user-friendly way.

---

## Features

- **Interactive Chatbot**: Provides answers to common queries such as exercise tips, healthy recipes, community schedules, and more
- **Voice Input**: Record your voice and have it automatically transcribed using OpenAI's Whisper API, optimized for elderly speech patterns
- **Text Input**: Traditional typing interface for those who prefer keyboard input
- **Example Questions**: Includes pre-set example questions to guide users in interacting with the chatbot
- **Customizable Interface**: Allows users to adjust themes, font sizes, and layout for better accessibility
- **Session Management**: Keeps chat histories organized, enabling users to revisit past conversations
- **Conversation Guide**: Provides possible followup questions for users to click to enable easier conversation with the chatbot
- **Intelligent Context Selection**: Automatically selects appropriate system prompts based on your input
- **Event Information**: Displays community schedules, menus, and activities from `prompts/events.txt` (optional web scraping available)

---

## File Structure

- `code/streamlit_gpt.py`: Main application file
- `code/web_scrapper.py`: Optional web scraping module (disabled by default)
- `prompts/`: Directory containing system prompt files and events data
- `requirements.txt`: Python dependencies
- `.env`: Environment variables (create this file with your API key)

## Installation & Setup

1. **Install required packages**:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install streamlit==1.45.0 openai==1.77.0 python-dotenv
```

2. **Set up API key and credentials**:Create a .env file in the root directory and add the following lines:

```bash
OPENAI_API_KEY=your_api_key
```

your_api_key is the API key for the OpenAI API. You can get it from [here](https://platform.openai.com/api-keys).

3. **Run the application**:

```bash
streamlit run code/streamlit_gpt.py
```

4. **Open the chatbot in your browser:**

```
http://localhost:8501
```

**Note**: By default, the app uses static events from `prompts/events.txt`. Set `USE_WEB_SCRAPER=true` in `.env` to enable live web scraping (requires Chrome browser and Selenium dependencies).

---

## Goal

This chatbot aims to:

- Enhance **access to information** within the retirement community.
- Encourage **tech adoption** by providing a simple, approachable step-by-step guide.
- Promote **self-sufficiency** in using technology for daily tasks and queries.
- **Improve accessibility** through voice input options for users who may have difficulty typing.

By bridging the gap between technology and senior users, this project strives to empower retirees with knowledge and confidence in their digital interactions.

Authors:

- Feng
- Ray
- Luna
- Wenyu
- Yein
- Amy
- Ethan
- George
- Kaylee
- Ryker


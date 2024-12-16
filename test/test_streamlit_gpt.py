## It will fail to upload due to the missing api key. 
import pytest
from unittest.mock import patch
from ..streamlit_gpt import select_prompt_by_context

# Mock SYSTEM_PROMPTS
mock_system_prompts = {
    "schedule_menu": "Schedule menu prompt",
    "retirement_assistant": "Health tech prompt",
    "default": "Default prompt",
}

@patch("streamlit_gpt.SYSTEM_PROMPTS", mock_system_prompts)  # Mock the SYSTEM_PROMPTS dictionary
@patch("streamlit_gpt.st.error")  # Mock the Streamlit error handling
def test_select_prompt_by_context(mock_error):
    # Test case 1: Input matches schedule menu keywords
    user_input = "What is the dinner menu?"
    result = select_prompt_by_context(user_input)
    assert result == mock_system_prompts["schedule_menu"]

    # Test case 2: Input matches health tech keywords
    user_input = "How do I install the app?"
    result = select_prompt_by_context(user_input)
    assert result == mock_system_prompts["retirement_assistant"]

    # Test case 3: Input matches no keywords (default)
    user_input = "Tell me a story"
    result = select_prompt_by_context(user_input)
    assert result == mock_system_prompts["default"]

    # Test case 4: Error handling (simulating exception)
    with patch("streamlit_gpt.any", side_effect=Exception("Simulated error")):
        user_input = "This will cause an error"
        result = select_prompt_by_context(user_input)
        mock_error.assert_called_once_with("Error in prompt selection: Simulated error")
        assert result == mock_system_prompts["default"]

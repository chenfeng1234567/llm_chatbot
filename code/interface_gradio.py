import gradio as gr

# Placeholder function for chatbot response
def chatbot(user_input, history):
    history.append(("User", user_input))
    # Replace with model-generated response
    bot_response = f"This is a response to '{user_input}'"
    history.append(("Assistant", bot_response))
    return history, history

# Set up Gradio interface
with gr.Blocks(css=".chatbot-box {padding: 10px; border-radius: 5px; font-size: 14px; color: black; background-color: white;}") as demo:
    gr.Markdown("# Chatbot Interface")

    # User customization inputs
    bg_color = gr.ColorPicker(label="Background Color", value="#FFFFFF")
    font_color = gr.ColorPicker(label="Font Color", value="#000000")
    font_size = gr.Slider(label="Font Size", minimum=10, maximum=30, value=14, step=1)

    # Chatbot display
    chatbot_box = gr.Chatbot(label="Chat", elem_classes="chatbot-box")

    with gr.Row():
        user_input = gr.Textbox(label="Type here...")
        submit_button = gr.Button("Send")

    # Function to apply custom styles dynamically
    def apply_styles(history, bg_color, font_color, font_size):
        styles = f"""
        .chatbot-box {{
            background-color: {bg_color};
            color: {font_color};
            font-size: {font_size}px;
        }}
        """
        return gr.HTML.update(value=f"<style>{styles}</style>"), history

    # Button actions
    submit_button.click(chatbot, inputs=[user_input, chatbot_box], outputs=[chatbot_box, chatbot_box])
    apply_styles_button = gr.Button("Apply Styles")
    apply_styles_button.click(apply_styles, inputs=[chatbot_box, bg_color, font_color, font_size], outputs=[gr.HTML(), chatbot_box])

# Launch the interface
demo.launch()

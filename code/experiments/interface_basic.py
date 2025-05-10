import dash
from dash import dcc, html, Input, Output, State

# Set up the Dash app
app = dash.Dash(__name__)

# Define the layout
app.layout = html.Div(
    [
        html.H2("Simple Chat Interface"),
        dcc.Textarea(
            id="user_input",
            placeholder="Type your message here...",
            style={"width": "100%", "height": "100px"},
        ),
        html.Button("Send", id="send_button"),
        html.Div(id="chat_output", style={"border": "1px solid #ccc", "padding": "10px", "min-height": "200px", "margin-top": "10px"}),
        
        # Customization Controls
        html.Div(
            [
                html.Label("Font Size:"),
                html.Button("Small", id="font_small", n_clicks=0),
                html.Button("Medium", id="font_medium", n_clicks=0),
                html.Button("Large", id="font_large", n_clicks=0),
                html.Br(),
                
                html.Label("Background Color:"),
                html.Button("White", id="bg_white", n_clicks=0),
                html.Button("Light Grey", id="bg_lightgrey", n_clicks=0),
                html.Button("Yellow", id="bg_yellow", n_clicks=0),
            ],
            style={"margin-top": "20px"},
        ),
    ],
    style={"width": "500px", "margin": "auto", "padding": "20px"},
)

# Define the callback to update the chat output and customization
@app.callback(
    Output("chat_output", "children"),
    Output("chat_output", "style"),
    [Input("send_button", "n_clicks"),
     Input("font_small", "n_clicks"),
     Input("font_medium", "n_clicks"),
     Input("font_large", "n_clicks"),
     Input("bg_white", "n_clicks"),
     Input("bg_lightgrey", "n_clicks"),
     Input("bg_yellow", "n_clicks")],
    State("user_input", "value"),
    State("chat_output", "children"),
)
def update_chat_output(send_clicks, font_small, font_medium, font_large, bg_white, bg_lightgrey, bg_yellow, user_input, current_output):
    # Default styles
    font_size = "16px"
    background_color = "white"

    # Handle font size changes
    if font_small > font_medium and font_small > font_large:
        font_size = "14px"
    elif font_medium > font_small and font_medium > font_large:
        font_size = "16px"
    elif font_large > font_small and font_large > font_medium:
        font_size = "20px"

    # Handle background color changes
    if bg_lightgrey > bg_white and bg_lightgrey > bg_yellow:
        background_color = "#f0f0f0"
    elif bg_yellow > bg_white and bg_yellow > bg_lightgrey:
        background_color = "#fffacd"

    # Update chat output with the user's input
    if send_clicks and user_input:
        current_output = (current_output or []) + [html.P(f"You: {user_input}"), html.P("Bot: [Response goes here]")]
    
    # Update the chat output with font size and background color styles
    style = {"border": "1px solid #ccc", "padding": "10px", "min-height": "200px", "margin-top": "10px",
             "fontSize": font_size, "backgroundColor": background_color}
    return current_output, style

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)

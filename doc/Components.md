Component 1 <br/>
Name: Customizable User interface <br/>
What it does: allow users to adjust font size and background color <br/>
Inputs:  button clicks or selections <br/>
Outputs: changes in interface or font size <br/>
Components used: <br/>
Side effects: N/A <br/>


Component 2 <br/>
Name: **Prompt Suggestion and Input**
What it does: 
- Provide some sample prompts for the user to choose from based on their health condition and goals, and allow the user to input their own prompt
  
Inputs:
- User's prompt in text input
- User's prompt in voice input
- User's prompt history
- User's name
- User's age
- User's health condition
- User's health goal
- User's health history
- User's health concerns
- User's preferences
  
Outputs:
- A list of prompts for the user to choose from
  
Components:
- A list of suggested prompts 
- A button for the user to directly choose from the suggested prompts
- A text input for the user to enter their own prompt
- A submit button for the user to submit their prompt
- A clear button for the user to clear their prompt

How it uses other components:
- The user's prompt and prompt history are used to generate the suggested prompts
- The user's name, age, health condition, health goal, health history, health concerns, and preferences are saved in the database and used to generate the suggested prompts
- The user's input can be used as a warning sign for the detection component

Side effects:
- User's privacy issues
- User may not be able to find the prompt they want if the suggested prompts are not relevant to them

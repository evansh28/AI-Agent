from googlesearch import search
from groq import Groq  # Importing the Groq library to use its API.
from json import load, dump  # Importing functions to read and write JSON files.
import datetime  # Importing the datetime module for real-time date and time information.
from dotenv import dotenv_values  # Importing dotenv_values to read environment variables from a .env file.
import os  # For handling file paths

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")

# Retrieve environment variables for the chatbot configuration.
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize the Groq client with the provided API key.
client = Groq(api_key=GroqAPIKey)

# Define the system instructions for the chatbot.
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional way. ***"""

# Define file path
file_path = os.path.join("Data", "ChatLog.json")

# Try to load the chat log from a JSON file, or create an empty one if it doesn't exist.
try:
    with open(file_path, "r") as f:
        messages = load(f)
except FileNotFoundError:
    with open(file_path, "w") as f:
        dump([], f)
    messages = []

# Function to perform a Google search and format the results.
def GoogleSearch(query):
    results = list(search(query, advanced=True, num_results=5)) 
    Answer = f"The search results for '{query}' are:\n[start]\n"
    
    for i in results:
        Answer += f"Title: {i.title}\nDescription: {i.description}\n\n"
    Answer += "[end]"
    return Answer

# Function to clean up the answer by removing empty lines.
def AnswerModifier(Answer):
    return '\n'.join([line for line in Answer.split('\n') if line.strip()])

# Function to get real-time information.
def Information():
    current_date_time = datetime.datetime.now()
    data = f"""Use This Real-time Information if needed:
Day: {current_date_time.strftime('%A')}
Date: {current_date_time.strftime('%d')}
Month: {current_date_time.strftime('%B')}
Year: {current_date_time.strftime('%Y')}
Time: {current_date_time.strftime('%H')} hours, {current_date_time.strftime('%M')} minutes, {current_date_time.strftime('%S')} seconds.
"""
    return data

# Function to handle real-time search and response generation.
def RealtimeSearchEngine(prompt):
    global messages

    # Load chat log from JSON
    with open(file_path, "r") as f:
        messages = load(f)

    messages.append({"role": "user", "content": prompt})

    # Prepare conversation context
    chat_context = [
        {"role": "system", "content": System},
        {"role": "system", "content": GoogleSearch(prompt)},
        {"role": "system", "content": Information()}
    ] + messages

    # Generate response
    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=chat_context,
        temperature=0.7,
        max_tokens=2048,
        top_p=1,
        stream=True
    )

    Answer = "".join(chunk.choices[0].delta.content for chunk in completion if chunk.choices[0].delta.content)

    messages.append({"role": "assistant", "content": Answer})

    # Save updated chat log
    with open(file_path, "w") as f:
        dump(messages, f, indent=4)

    return AnswerModifier(Answer)

# Main execution
if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ")
        print(RealtimeSearchEngine(prompt))

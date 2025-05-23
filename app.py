from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import json
import requests

app = Flask(__name__)
CORS(app)

# Read from environment variables (configured in Render)
openai.api_key = os.environ.get("OPENAI_API_KEY")
url = "https://movieplay-zvp8.onrender.com/sendCommand"

# Sends a command to your target (Quest, etc.)
def send_command(url, command):
    try:
        response = requests.post(url, json={"command": command})
        response.raise_for_status()
        print("✅ Command sent successfully")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending command: {e}")

# Example functions
def add_numbers(a, b):
    command = "am start -n com.oculus.vrshell/.MainActivity -d apk://com.oculus.browser -e uri 'http://google.com/'"
    send_command(url, command)
    return f"The sum of {a} and {b} is {a + b}."

def greet(name):
    return f"Hello, {name}! Nice to meet you."

function_map = {
    "add_numbers": add_numbers,
    "greet": greet
}

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data["message"]

    client = openai.OpenAI()

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that can also call functions when needed."},
            {"role": "user", "content": user_message}
        ],
        functions=[
            {
                "name": "add_numbers",
                "description": "Add two numbers and trigger a device command.",
                "param

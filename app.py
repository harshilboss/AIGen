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
    send_command(COMMAND_TARGET_URL, command)
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
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer"},
                        "b": {"type": "integer"}
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "greet",
                "description": "Greet someone by name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    },
                    "required": ["name"]
                }
            }
        ],
        function_call="auto"
    )

    message = response.choices[0].message

    if message.function_call:
        fn_name = message.function_call.name
        args = json.loads(message.function_call.arguments)
        if fn_name in function_map:
            try:
                result = function_map[fn_name](**args)
                return jsonify({"response": result})
            except Exception as e:
                return jsonify({"response": f"Error: {str(e)}"})
    else:
        return jsonify({"response": message.content})

if __name__ == "__main__":
    app.run(debug=True)

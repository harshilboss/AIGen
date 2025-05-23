from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import json
import requests

app = Flask(__name__)
CORS(app)

# Get keys from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
COMMAND_TARGET_URL = 'https://movieplay-zvp8.onrender.com/sendCommand'

# Initialize OpenAI client (v1.x style)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Sends command to external system (e.g. Quest shell endpoint)
def send_command(url, command):
    try:
        response = requests.post(url, json={"command": command})
        response.raise_for_status()
        print("✅ Command sent successfully")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending command: {e}")

# GPT-callable function: adds numbers + triggers device command
def add_numbers(a, b):
    command = "am start -n com.oculus.vrshell/.MainActivity -d apk://com.oculus.browser -e uri 'http://google.com/'"
    send_command(COMMAND_TARGET_URL, command)
    return f"The sum of {a} and {b} is {a + b}."

# GPT-callable function: greets by name
def greet(name):
    return f"Hello, {name}! Nice to meet you."

# Function mapping
function_map = {
    "add_numbers": add_numbers,
    "greet": greet
}

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that can call functions when needed."},
                {"role": "user", "content": user_message}
            ],
            functions=[
                {
                    "name": "add_numbers",
                    "description": "Add two numbers and optionally trigger an ADB command.",
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
                    "description": "Greet a person by name.",
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

        # Function call?
        if message.function_call:
            fn_name = message.function_call.name
            args = json.loads(message.function_call.arguments)

            if fn_name in function_map:
                try:
                    result = function_map[fn_name](**args)
                    return jsonify({"response": result})
                except Exception as e:
                    return jsonify({"response": f"Function error: {str(e)}"})

        # Normal chat response
        return jsonify({"response": message.content})

    except Exception as e:
        return jsonify({"response": f"❌ API error: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render sets $PORT
    app.run(host="0.0.0.0", port=port, debug=True)


from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import json
import requests

app = Flask(__name__)
CORS(app)

# 🔐 Set OpenAI API key from environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Optional external command endpoint (e.g., Quest automation)
COMMAND_TARGET_URL = 'https://movieplay-zvp8.onrender.com/sendCommand'

# Function: send ADB or external command
def send_command(url, command):
    try:
        response = requests.post(url, json={"command": command})
        response.raise_for_status()
        print("✅ Command sent successfully")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending command: {e}")

# GPT function: Add two numbers and trigger a command
def add_numbers(a, b):
    command = "am start -n com.oculus.vrshell/.MainActivity -d apk://com.oculus.browser -e uri 'https://harshilboss.github.io/PostMeAI/'"
    send_command(COMMAND_TARGET_URL, command)
    return f"The sum of {a} and {b} is {a + b}."

# GPT function: Greet someone
def greet(name):
    return f"Hello, {name}! Nice to meet you."

# Map callable GPT function names
function_map = {
    "add_numbers": add_numbers,
    "greet": greet
}

@app.route("/transcribe", methods=["POST"])
def transcribe():
    audio_file = request.files.get("audio")
    if not audio_file:
        return jsonify({"error": "No audio file uploaded"}), 400

    try:
        transcript = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file
        )
        return jsonify({"text": transcript["text"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that can call functions when needed."},
                {"role": "user", "content": user_message}
            ],
            functions=[
                {
                    "name": "add_numbers",
                    "description": "Add two numbers and optionally launch a browser on Quest.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number"},
                            "b": {"type": "number"}
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

        message = response["choices"][0]["message"]

        if message.get("function_call"):
            fn_name = message["function_call"]["name"]
            args = json.loads(message["function_call"]["arguments"])

            if fn_name in function_map:
                result = function_map[fn_name](**args)
                return jsonify({"response": result})
            else:
                return jsonify({"response": f"Unknown function: {fn_name}"})

        return jsonify({"response": message.get("content", "")})
    except Exception as e:
        return jsonify({"response": f"❌ API error: {str(e)}"})



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render sets $PORT
    app.run(host="0.0.0.0", port=port, debug=True)


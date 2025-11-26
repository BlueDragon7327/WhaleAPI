from flask import Flask, render_template, request, jsonify
import requests
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)

WHALEAI_URL = "https://mira-ai-f296.onrender.com/v1/chat/completions"
MODELS_URL = "https://mira-ai-f296.onrender.com/v1/models"
CHATS_FILE = "chats.json"
API_KEYS_FILE = "key.txt"

AVAILABLE_MODELS = []

def load_api_keys():
    if os.path.exists(API_KEYS_FILE):
        with open(API_KEYS_FILE, "r") as f:
            keys = [line.strip() for line in f if line.strip()]
            return keys
    return []

API_KEYS = load_api_keys()
CURRENT_KEY_INDEX = 0

def get_next_api_key():
    global CURRENT_KEY_INDEX
    if not API_KEYS:
        raise Exception("No API key found in key.txt")
    
    key = API_KEYS[CURRENT_KEY_INDEX]
    CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(API_KEYS)
    return key

def load_models():
    global AVAILABLE_MODELS
    try:
        mira_api_key = get_next_api_key()
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {mira_api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(MODELS_URL, headers=headers)
        if response.status_code == 200:
            data = response.json()
            AVAILABLE_MODELS = data.get("data", [])
        return AVAILABLE_MODELS
    except Exception as e:
        print(f"Error loading models: {e}")
        return AVAILABLE_MODELS

load_models()

def load_chats():
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_chats(chats):
    with open(CHATS_FILE, "w") as f:
        json.dump(chats, f, indent=2)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/models", methods=["GET"])
def get_models():
    if not AVAILABLE_MODELS:
        load_models()
    return jsonify({"data": AVAILABLE_MODELS})

@app.route("/api/chats", methods=["GET"])
def get_chats():
    chats = load_chats()
    chat_list = [{"id": cid, "title": c["title"], "model": c["model"], "created_at": c["created_at"]} for cid, c in chats.items()]
    return jsonify(chat_list)

@app.route("/api/chat/<chat_id>", methods=["GET"])
def get_chat(chat_id):
    chats = load_chats()
    if chat_id not in chats:
        return jsonify({"error": "Chat not found"}), 404
    return jsonify(chats[chat_id])

@app.route("/api/chat", methods=["POST"])
def create_chat():
    data = request.json
    model = data.get("model", "gpt-5.1")
    
    chats = load_chats()
    chat_id = str(uuid.uuid4())
    
    chats[chat_id] = {
        "id": chat_id,
        "title": f"New chat - {model}",
        "model": model,
        "messages": [],
        "created_at": datetime.now().isoformat() + "Z"
    }
    
    save_chats(chats)
    return jsonify(chats[chat_id])

@app.route("/api/chat/<chat_id>/message", methods=["POST"])
def add_message(chat_id):
    data = request.json
    user_message = data.get("message")
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    chats = load_chats()
    if chat_id not in chats:
        return jsonify({"error": "Chat not found"}), 404
    
    chat = chats[chat_id]
    model = chat["model"]
    
    chat["messages"].append({"role": "user", "content": user_message})
    
    payload = {
        "messages": chat["messages"],
        "model": model
    }
    
    mira_api_key = get_next_api_key()
    
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {mira_api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(WHALEAI_URL, headers=headers, data=json.dumps(payload))
        data = response.json()
        
        assistant_msg = data["choices"][0]["message"]["content"]
        chat["messages"].append({"role": "assistant", "content": assistant_msg})
        
        if len(chat["messages"]) == 2:
            chat["title"] = user_message[:50]
        
        save_chats(chats)
        
        return jsonify({
            "reply": assistant_msg,
            "chat": chat
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/chat/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    chats = load_chats()
    if chat_id not in chats:
        return jsonify({"error": "Chat not found"}), 404
    
    del chats[chat_id]
    save_chats(chats)
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)

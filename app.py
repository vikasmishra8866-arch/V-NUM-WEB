import os
import random
import threading
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from telethon.sessions import StringSession
from telethon.sync import TelegramClient

app = Flask(__name__)
CORS(app)

# Render Environment Variables se credentials uthana (No config.py needed)
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
TARGET_BOT_USERNAME = os.environ.get("TARGET_BOT_USERNAME", "@V5rtobot")

rate_lock = threading.Lock()
last_request_time = 0

@app.route("/api/vahan", methods=["GET"])
def get_vehicle_api():
    global last_request_time

    vehicle_no = request.args.get("veh", "").strip().upper()
    if not vehicle_no:
        return jsonify({
            "status": "error",
            "message": "Vehicle number is required. Use ?veh=YOUR_VEHICLE_NO"
        }), 400

    session_str = os.environ.get("SESSION_STRING", "")
    if not session_str or not API_ID or not API_HASH:
        return jsonify({
            "status": "error",
            "message": "Required environment variables (SESSION_STRING, API_ID, API_HASH) are missing on Render!"
        }), 500

    try:
        with rate_lock:
            current_time = time.time()
            elapsed = current_time - last_request_time
            cooldown_target = random.uniform(7.0, 12.0)
            
            sleep_time = 0
            if elapsed < cooldown_target:
                sleep_time = cooldown_target - elapsed
            
            last_request_time = time.time() + sleep_time

        if sleep_time > 0:
            time.sleep(sleep_time)

        result_data = fetch_json_from_telegram(vehicle_no, session_str)
        return jsonify(result_data)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        }), 500

def fetch_json_from_telegram(vehicle_no, session_str):
    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    try:
        client.connect()
        if not client.is_user_authorized():
            return {
                "status": "error",
                "message": "Telegram session expired or unauthorized."
            }

        sent_msg = client.send_message(TARGET_BOT_USERNAME, vehicle_no)
        raw_text = "Target bot response timeout."
        start_time = time.time()

        while (time.time() - start_time) < 25:
            messages = client.get_messages(TARGET_BOT_USERNAME, limit=10)
            for msg in messages:
                if (
                    msg.id > sent_msg.id
                    and msg.text
                    and msg.sender_id != client.get_me().id
                ):
                    txt = msg.text.strip()
                    if (
                        "fetching" in txt.lower()
                        or "please wait" in txt.lower()
                        or txt == vehicle_no
                    ):
                        continue

                    raw_text = txt
                    client.disconnect()
                    return format_text_to_json(vehicle_no, raw_text)
            time.sleep(1.5)

        client.disconnect()
        return {"status": "error", "message": raw_text}

    except Exception as e:
        try:
            client.disconnect()
        except:
            pass
        return {"status": "error", "message": str(e)}

def format_text_to_json(vehicle_no, text):
    lines = text.split("\n")
    data_dict = {"vehicle_no": vehicle_no, "raw_response": text}

    parsed_details = {}
    for line in lines:
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip().lower().replace(" ", "_")
            val = parts[1].strip()
            parsed_details[key] = val

    if parsed_details:
        data_dict["details"] = parsed_details

    return {"status": "success", "data": data_dict}

@app.route("/", methods=["GET"])
def home():
    return "Vahan Master API System is Live!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

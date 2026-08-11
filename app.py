import os
import random
import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Rotating Browser User-Agents to prevent bot blocking
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
]

UPSTREAM_API = "https://vahan-system.onrender.com/api/vahan"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/vahan", methods=["GET"])
def proxy_vahan():
    vehicle_no = request.args.get("veh", "").strip().upper()
    if not vehicle_no:
        return jsonify({"status": "error", "message": "Vehicle registration number is required."}), 400

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json",
        "Referer": "https://vahan-system.onrender.com/"
    }

    try:
        response = requests.get(
            UPSTREAM_API, 
            params={"veh": vehicle_no}, 
            headers=headers, 
            timeout=20
        )
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error", 
            "message": f"Upstream service connection error: {str(e)}"
        }), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)

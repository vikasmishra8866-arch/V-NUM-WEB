from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time

app = Flask(__name__)
CORS(app)

# Simple rate limiting tracker
last_request_time = {}

@app.route('/api/vahan', methods=['GET'])
def get_vahan_details():
    veh_no = request.args.get('veh')
    if not veh_no:
        return jsonify({"error": "Vehicle number required"}), 400

    # Basic rate limiting (7 seconds)
    client_ip = request.remote_addr
    now = time.time()
    if client_ip in last_request_time and (now - last_request_time[client_ip] < 7):
        return jsonify({"error": "Rate limit exceeded. Please wait 7 seconds."}), 429

    try:
        url = f"https://vahan-system.onrender.com/api/vahan?veh={veh_no}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=20)
        
        last_request_time[client_ip] = now
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

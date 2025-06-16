from flask import Flask, request, jsonify
import os
import requests
from config import DEFECTDOJO_URL, DEFECTDOJO_API_KEY, DEFECTDOJO_ENGAGEMENT_ID, DEFECTDOJO_SCAN_TYPE, LIST_OF_TOOLS

app = Flask(__name__)
received_tools = set()

@app.route("/upload/<tool_name>", methods=["POST"])
def upload(tool_name):
    if tool_name not in LIST_OF_TOOLS:
        return jsonify({"error": "Unknown tool"}), 400

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    # Пересылаем в DefectDojo
    files = {'file': (file.filename, file.stream, file.mimetype)}
    data = {
        "scan_type": DEFECTDOJO_SCAN_TYPE,
        "engagement": DEFECTDOJO_ENGAGEMENT_ID,
        "active": "true",
        "verified": "false",
    }
    headers = {
        "Authorization": f"Token {DEFECTDOJO_API_KEY}"
    }
    response = requests.post(DEFECTDOJO_URL, files=files, data=data, headers=headers)

    if response.status_code >= 200 and response.status_code < 300:
        received_tools.add(tool_name)
        return jsonify({"status": "File uploaded and forwarded"}), 200
    else:
        return jsonify({"error": "Failed to forward to DefectDojo", "details": response.text}), 500


@app.route("/status", methods=["GET"])
def status():
    done = all(tool in received_tools for tool in LIST_OF_TOOLS)
    return jsonify({
        "all_received": done,
        "received": list(received_tools),
        "remaining": list(set(LIST_OF_TOOLS) - received_tools)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

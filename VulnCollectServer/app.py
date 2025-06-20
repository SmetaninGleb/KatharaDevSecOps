from flask import Flask, request, jsonify
import os
import json
import requests

app = Flask(__name__)

server_config = {
    "tools": set(),
    "products": {},
    "defectdojo": {}
}
received_tools = set()
log_entries = []

def log_error(message, error=None):
    log_entries.append({"error": message, "details": str(error)})

@app.route("/configure", methods=["POST"])
def configure():
    try:
        data = request.get_json(force=True)
        server_config["tools"] = set(data["tools"])
        server_config["products"] = data.get("products", {})
        server_config["defectdojo"] = data["defectdojo"]
        received_tools.clear()
        log_entries.append({"message": "Configuration updated", "config": data})
        return jsonify({"status": "configured"}), 200
    except Exception as e:
        log_error("Failed to configure server", e)
        return jsonify({"error": "Configuration failed"}), 500

def ensure_product_exists(name):
    url = server_config["defectdojo"]["url"].rstrip("/") + "/products/"
    headers = {"Authorization": f"Token {server_config['defectdojo']['api_key']}"}
    resp = requests.get(url, params={"name": name}, headers=headers)
    if resp.status_code == 200 and resp.json().get("count", 0) > 0:
        return resp.json()["results"][0]["id"]
    create_resp = requests.post(url, headers=headers, json={"name": name})
    if create_resp.status_code == 201:
        return create_resp.json()["id"]
    log_error(f"Failed to create product {name}: {create_resp.text}")
    return None

@app.route("/upload/<tool_id>", methods=["POST"])
def upload(tool_id):
    try:
        if tool_id in received_tools:
            return jsonify({"status": "already received"}), 200

        file = request.files["file"]
        product_name = server_config["products"].get(tool_id, "DefaultProduct")
        product_id = ensure_product_exists(product_name)
        if not product_id:
            return jsonify({"error": "Failed to ensure product"}), 500

        headers = {
            "Authorization": f"Token {server_config['defectdojo']['api_key']}"
        }
        # Поддержка доп. заголовков
        user_headers = request.headers.get("X-Forward-Headers")
        if user_headers:
            headers.update(json.loads(user_headers))

        scan_data = {
            "scan_type": server_config["defectdojo"]["scan_type"],
            "product": product_id,
            "engagement": None,  # или создать через API, если нужно
            "active": True,
            "verified": True
        }
        files = {"file": (file.filename, file.stream, file.mimetype)}
        defectdojo_upload_url = server_config["defectdojo"]["url"].rstrip("/") + "/import-scan/"

        resp = requests.post(defectdojo_upload_url, headers=headers, data=scan_data, files=files)

        if resp.status_code in [200, 201]:
            received_tools.add(tool_id)
            return jsonify({"status": "received"}), 200
        else:
            log_error("Upload failed", resp.text)
            return jsonify({"error": "Upload failed"}), 500

    except Exception as e:
        log_error("Upload error", e)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/status", methods=["GET"])
def status():
    remaining = list(server_config["tools"] - received_tools)
    return jsonify({"waiting_for": remaining})

@app.route("/logs", methods=["GET"])
def logs():
    return jsonify(log_entries[-50:])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

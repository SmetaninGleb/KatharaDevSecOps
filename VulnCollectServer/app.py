from flask import Flask, request, jsonify
import os
import json
import requests
import traceback

app = Flask(__name__)

server_config = {
    "tools": [],
    "defectdojo": {
        "ip": "",
        "port": "",
        "token": "",
    }
}
received_tools = set()
log_entries = []

def log_error(message, exception=None):
    """Логирует ошибку в память"""
    entry = {"message": message}
    if exception:
        entry["exception"] = traceback.format_exc()
    log_entries.append(entry)
    print(f"LOGGED ERROR: {entry}")

@app.route("/configure", methods=["POST"])
def configure():
    try:
        data = request.get_json(force=True)
        server_config["tools"] = data["tools"]
        server_config["defectdojo"] = data["defectdojo"]
        received_tools.clear()
        log_entries.append({"message": "Configuration updated", "config": data})
        return jsonify({"status": "configured"}), 200
    except Exception as e:
        log_error("Failed to configure server", e)
        return jsonify({"error": "Configuration failed"}), 500

def ensure_product_exists(name):
    dojo_url = f"http://{server_config['defectdojo']['ip']}:{server_config['defectdojo']['port']}"
    url = dojo_url.rstrip("/") + "/api/v2/products/"
    headers = {"Authorization": f"Token {server_config['defectdojo']['token']}"}
    resp = requests.get(url, params={"name": name}, headers=headers)
    if resp.status_code == 200 and resp.json().get("count", 0) > 0:
        return resp.json()["results"][0]["id"]
    data = {
        "name": name,
        "description": "Created automatically",
        "prod_type": 1
    }
    create_resp = requests.post(url, headers=headers, json=data)
    if create_resp.status_code == 201:
        return create_resp.json()["id"]
    log_error(f"Failed to create product {name}: {create_resp.text}")
    return None

@app.route("/upload/<tool_id>", methods=["POST"])
def upload(tool_id):
    try:
        if tool_id not in server_config["tools"]:
            msg = f"Unknown tool: {tool_id}"
            log_error(msg)
            return jsonify({"error": msg}), 400

        if tool_id in received_tools:
            log_error(f"Tool id {tool_id} already received!")
            return jsonify({"status": "already received"}), 200

        product_name = request.form.get('product_name')
        if product_name is None:
            log_error(f"On tool {tool_id} no product_name!")
            return jsonify({"error": "Failed to ensure product"}), 500
        product_id = ensure_product_exists(product_name)
        if not product_id:
            log_error(f"On tool {tool_id} product_name not correct!")
            return jsonify({"error": "Failed to ensure product"}), 500

        headers = {
            "Authorization": f"Token {server_config['defectdojo']['token']}"
        }

        form_data = request.form.to_dict()

        files = {}
        for key, file_storage in request.files.items():
            files[key] = (file_storage.filename, file_storage.stream, file_storage.content_type)
        # scan_data = {
        #     "scan_type": data.get("scan_type"),
        #     "product": product_id,
        #     "engagement_name": data.get("engagement_name"),  # или создать через API, если нужно
        #     "active": True,
        #     "verified": True
        # }
        # files = {"file": (file.filename, file.stream, file.mimetype)}
        
        
        # DEBUG LOG — перед отправкой
        log_entries.append({
            "message": "Preparing upload to DefectDojo",
            "form_data": form_data,
            "file_keys": list(files.keys())
        })

        dojo_url = f"http://{server_config['defectdojo']['ip']}:{server_config['defectdojo']['port']}"
        defectdojo_upload_url = dojo_url.rstrip("/") + "/api/v2/import-scan/"

        resp = requests.post(defectdojo_upload_url, headers=headers, data=form_data, files=files)

        if resp.status_code in [200, 201]:
            received_tools.add(tool_id)
            return jsonify({"status": "received"}), 200
        else:
            log_entries.append({
                "message": "Upload failed",
                "status_code": resp.status_code,
                "response_text": resp.text
            })
            return jsonify({"error": "Upload failed"}), 500

    except Exception as e:
        log_error("Upload error", e)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/status", methods=["GET"])
def status():
    done = all(tool in received_tools for tool in server_config["tools"])
    return jsonify({
        "all_received": done,
        "received": list(received_tools),
        "remaining": list(set(server_config["tools"]) - received_tools)
    })

@app.route("/logs", methods=["GET"])
def logs():
    return jsonify(log_entries)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

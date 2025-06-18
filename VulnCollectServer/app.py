from flask import Flask, request, jsonify
import os
from datetime import datetime
import requests
import traceback
from config import DEFECTDOJO_URL, DEFECTDOJO_API_KEY, DEFECTDOJO_ENGAGEMENT_ID, DEFECTDOJO_SCAN_TYPE, LIST_OF_TOOLS

app = Flask(__name__)
received_tools = set()
log_entries = []  # Храним логи в памяти

def log_error(message, exception=None):
    """Логирует ошибку в память"""
    entry = {"message": message}
    if exception:
        entry["exception"] = traceback.format_exc()
    log_entries.append(entry)
    print(f"LOGGED ERROR: {entry}")

@app.route("/upload/<tool_name>", methods=["POST"])
def upload(tool_name):
    try:
        if tool_name not in LIST_OF_TOOLS:
            msg = f"Unknown tool: {tool_name}"
            log_error(msg)
            return jsonify({"error": msg}), 400

        if 'file' not in request.files:
            msg = f"No file part in upload from {tool_name}"
            log_error(msg)
            return jsonify({"error": msg}), 400

        file = request.files['file']
        if file.filename == '':
            msg = f"Empty filename from {tool_name}"
            log_error(msg)
            return jsonify({"error": msg}), 400

        # Пересылаем в DefectDojo
        files = {
            "file": (file.filename, file.stream, "application/json")  # или file.mimetype
            }
        data = {
            "active": "true",
            "do_not_reactivate": "false",
            "verified": "true",
            "close_old_findings": "true",
            "test_title": "FVWA",
            "engagement_name": "Test",
            "deduplication_on_engagement": "true",
            "push_to_jira": "false",
            "minimum_severity": "Info",
            "close_old_findings_product_scope": "false",
            "scan_date": datetime.now().strftime("%Y-%m-%d"),
            "create_finding_groups_for_all_findings": "true",
            "group_by": "component_name",
            "apply_tags_to_findings": "true",
            "product_name": "FVWA",
            "auto_create_context": "true",
            "scan_type": DEFECTDOJO_SCAN_TYPE
        }
        headers = {
            "Authorization": f"Token {DEFECTDOJO_API_KEY}"
        }

        response = requests.post(DEFECTDOJO_URL, files=files, data=data, headers=headers)

        if response.status_code >= 200 and response.status_code < 300:
            received_tools.add(tool_name)
            return jsonify({"status": "File uploaded and forwarded"}), 200
        else:
            msg = f"DefectDojo error ({response.status_code}): {response.text}"
            log_error(msg)
            return jsonify({"error": "Failed to forward to DefectDojo", "details": response.text}), 500

    except Exception as e:
        log_error("Exception in upload handler", e)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/status", methods=["GET"])
def status():
    done = all(tool in received_tools for tool in LIST_OF_TOOLS)
    return jsonify({
        "all_received": done,
        "received": list(received_tools),
        "remaining": list(set(LIST_OF_TOOLS) - received_tools)
    })

@app.route("/logs", methods=["GET"])
def logs():
    return jsonify(log_entries)

if __name__ == "__main__":
    # Логируем конфиг один раз при старте
    config_log = {
        "message": "Configuration loaded",
        "DEFECTDOJO_IP": os.getenv("DEFECTDOJO_IP", "localhost"),
        "DEFECTDOJO_PORT": os.getenv("DEFECTDOJO_PORT", "8080"),
        "DEFECTDOJO_URL": DEFECTDOJO_URL,
        "DEFECTDOJO_API_KEY": "***" if DEFECTDOJO_API_KEY else "(empty)",
        "DEFECTDOJO_ENGAGEMENT_ID": DEFECTDOJO_ENGAGEMENT_ID,
        "DEFECTDOJO_SCAN_TYPE": DEFECTDOJO_SCAN_TYPE,
        "LIST_OF_TOOLS": LIST_OF_TOOLS,
    }

    log_entries.append(config_log)
    print(f"LOGGED CONFIG: {config_log}")
    
    app.run(host="0.0.0.0", port=5000)

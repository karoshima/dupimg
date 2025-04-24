import os
from flask import jsonify

def list_subdirectories(base_path):
    try:
        directories = [
            {"name": name, "path": os.path.join(base_path, name)}
            for name in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, name))
        ]
        return jsonify({"status": "success", "directories": directories})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

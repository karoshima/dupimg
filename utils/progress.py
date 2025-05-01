from flask import jsonify
from datetime import datetime
from utils.image_processing import get_progress

def get_progress_data():
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    progress_data = get_progress()
    progress_data["time"] = current_time
    return jsonify(progress_data)

from flask import jsonify
from utils.image_processing import get_progress

def get_progress_data() -> str:
    return jsonify(get_progress())

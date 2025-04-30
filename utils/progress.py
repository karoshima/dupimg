from flask import jsonify
from datetime import datetime

def get_progress_data():
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({'time': current_time, 'progress': 50, 'status': 'Processing', 'message': 'Processing images...'})

from flask import jsonify, request, render_template
from utils.directory_utils import list_subdirectories
from utils.mock_data import get_progress_data, get_results_data, get_trash_data

def register_routes(app):
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/settings", methods=["GET", "POST"])
    def settings():
        if request.method == "POST":
            directories = request.form.get("directories")
            algorithm = request.form.get("algorithm")
            similarity = request.form.get("similarity")
            directories = json.loads(directories) if directories else []
            return jsonify({
                "status": "success",
                "directories": directories,
                "algorithm": algorithm,
                "similarity": similarity
            })
        return render_template("settings.html")

    @app.route("/progress")
    def progress():
        return jsonify(get_progress_data())

    @app.route("/results")
    def results():
        return jsonify(get_results_data())

    @app.route("/trash", methods=["GET", "POST"])
    def trash():
        if request.method == "POST":
            file_id = request.form.get("file_id")
            return jsonify({"status": "deleted", "file_id": file_id})
        return jsonify(get_trash_data())

    @app.route("/list_directories", methods=["GET"])
    def list_directories():
        base_path = request.args.get("path", "/")
        return list_subdirectories(base_path)

    @app.route("/openapi.yaml")
    def openapi():
        return app.send_static_file("openapi.yaml")

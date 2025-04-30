import json
import os
from flask import jsonify, request, render_template
from utils.directory_utils import list_subdirectories, is_directory_allowed, allowed_directories
from utils.progress import get_progress_data
from utils.mock_data import get_results_data, get_trash_data

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

    @app.route("/progress", methods=["GET"])
    def progress():
        return render_template("progress.html")

    @app.route("/progress/data", methods=["GET"])
    def progress_data():
        return get_progress_data()

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

    @app.route("/add_directory", methods=["POST"])
    def add_directory():
        """
        手入力されたディレクトリを追加するエンドポイント。
        """
        directory = request.form.get("directory")
        if not directory:
            return jsonify({"status": "error", "message": "ディレクトリが指定されていません。"}), 400

        # パスを正規化してチェック
        abs_directory = os.path.normpath(os.path.abspath(directory))
        if any(abs_directory == os.path.normpath(allowed_dir) for allowed_dir in allowed_directories):
            return jsonify({"status": "error", "message": "指定されたディレクトリはすでに登録されています。"}), 400

        if not is_directory_allowed(directory):
            return jsonify({"status": "error", "message": "指定されたディレクトリは許可されていません。"}), 400

        # 許可されたディレクトリの場合の処理（例: ディレクトリをリストに追加）
        return jsonify({"status": "success", "message": "ディレクトリが追加されました。"})

    @app.route("/openapi.yaml")
    def openapi():
        return app.send_static_file("openapi.yaml")

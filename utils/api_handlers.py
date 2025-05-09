import json
import mimetypes
import os
from datetime import datetime
from flask import jsonify, request, render_template, send_file
from functools import wraps
from utils.directory_utils import list_subdirectories, is_directory_allowed, allowed_directories
from utils.image_processing import start_background_processing, handle_drag_drop_action
from utils.progress import get_progress_data
from utils.mock_data import get_trash_data

def register_routes(app) -> None:
    @app.route("/")
    def index() -> str:
        """
        ルートエンドポイント。メインページを表示する。
        """
        return render_template("index.html")

    @app.route("/settings", methods=["GET", "POST"])
    def settings() -> str:
        """
        設定ページ。POSTリクエストでディレクトリ、アルゴリズム、類似度を受け取り、
        バックグラウンドで画像探索処理を開始する。
        """
        if request.method == "POST":
            directories = request.form.get("directories")
            algorithm = request.form.get("algorithm")
            similarity = request.form.get("similarity")
            directories = json.loads(directories) if directories else []
            start_background_processing(directories, algorithm, similarity)
            return jsonify({
                "status": "success",
                "directories": directories,
                "algorithm": algorithm,
                "similarity": similarity
            })
        return render_template("settings.html")

    @app.route("/progress", methods=["GET"])
    def progress() -> str:
        """
        進捗状況ページ。GETリクエストで進捗状況を取得し、HTMLを返す。
        """
        return render_template("progress.html")

    @app.route("/progress/data", methods=["GET"])
    def progress_data() -> str:
        """
        進捗状況をJSON形式で返すエンドポイント。"""
        return get_progress_data()

    @app.route("/results")
    def results() -> str:
        """
        結果ページ。
        """
        return render_template("results.html")

    @app.route("/trash", methods=["GET", "POST"])
    def trash() -> str:
        """
        ゴミ箱ページ。GETリクエストでゴミ箱のデータを取得し、POSTリクエストでファイルを削除する。"""
        if request.method == "POST":
            file_id = request.form.get("file_id")
            return jsonify({"status": "deleted", "file_id": file_id})
        return jsonify(get_trash_data())

    @app.route("/list_directories", methods=["GET"])
    def list_directories() -> str:
        """
        指定されたディレクトリのサブディレクトリをリストするエンドポイント。
        """
        base_path = request.args.get("path", "/")
        return list_subdirectories(base_path)

    @app.route("/add_directory", methods=["POST"])
    def add_directory() -> str:
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

    @app.route("/api/image", methods=["GET"])
    def get_image():
        """
        指定された画像ファイルを返すエンドポイント。
        """
        image_path = request.args.get("path")
        if not image_path or not os.path.exists(image_path):
            return jsonify({"error": "Invalid or missing image path"}), 404

        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "application/octet-stream"
        try:
            return send_file(image_path, mimetype=mime_type)
        except Exception as e:
            return jsonify({"error": f"Failed to load image: {str(e)}"}), 500

    @app.route("/api/handle_drag_drop", methods=["POST"])
    def handle_drag_drop():
        """
        ドラッグ＆ドロップのアクションを処理するエンドポイント。
        """
        data = request.json
        source = data.get("source")
        target = data.get("target")
        action = data.get("action")

        if not source or not target or not action:
            return jsonify({"error": "Invalid parameters"}), 400

        # `image_processing.py` の関数を呼び出して処理を実行
        success, message = handle_drag_drop_action(source, target, action)

        if success:
            return jsonify({"status": "success", "message": message})
        else:
            return jsonify({"status": "error", "message": message}), 400

    @app.route("/openapi.yaml")
    def openapi() -> str:
        """
        OpenAPI仕様書を返すエンドポイント。
        """
        return app.send_static_file("openapi.yaml")

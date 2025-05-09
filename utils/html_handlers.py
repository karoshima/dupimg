from utils.image_processing import start_background_processing
from utils.mock_data import get_trash_data

from flask import jsonify, render_template, request
import json

def register_html_routes(app) -> None:
    """
    HTMLルートをFlaskアプリケーションに登録する関数。
    """
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
        return render_template("settings.html")

    @app.route("/progress", methods=["GET"])
    def progress() -> str:
        """
        進捗状況ページ。GETリクエストで進捗状況を取得し、HTMLを返す。
        """
        return render_template("progress.html")

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

    @app.route("/openapi.yaml")
    def openapi() -> str:
        """
        OpenAPI仕様書を返すエンドポイント。
        """
        return app.send_static_file("openapi.yaml")

import argparse
import json
import os

from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# 初期ページ
@app.route("/")
def index():
    return render_template("index.html")

# 対象ディレクトリ設定ページ
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        # フォームデータを取得
        directories = request.form.get("directories")
        algorithm = request.form.get("algorithm")
        similarity = request.form.get("similarity")

        # ディレクトリリストを JSON 形式から Python リストに変換
        directories = json.loads(directories) if directories else []

        # 仮のレスポンス
        return jsonify({
            "status": "success",
            "directories": directories,
            "algorithm": algorithm,
            "similarity": similarity
        })
    return render_template("settings.html")

# 検出中ページ
@app.route("/progress")
def progress():
    # 仮の進捗データ
    progress_data = {"progress": 50}
    return jsonify(progress_data)

# 検出結果ページ
@app.route("/results")
def results():
    # 仮の検出結果データ
    results_data = [
        {"id": 1, "filename": "image1.jpg", "status": "duplicate"},
        {"id": 2, "filename": "image2.jpg", "status": "unique"}
    ]
    return jsonify(results_data)

# ごみ箱ページ
@app.route("/trash")
def trash():
    if request.method == "POST":
        # 仮の削除処理
        file_id = request.form.get("file_id")
        return jsonify({"status": "deleted", "file_id": file_id})
    # 仮のごみ箱データ
    trash_data = [
        {"id": 1, "filename": "deleted_image1.jpg"},
        {"id": 2, "filename": "deleted_image2.jpg"}
    ]
    return jsonify(trash_data)

####
# 上記の各ページ内で使用する、ユーティリティエンドポイント

# サーバー側のディレクトリ構造を取得するエンドポイント
@app.route("/list_directories", methods=["GET"])
def list_directories():
    """
    指定されたパスのディレクトリ構造を取得して返すエンドポイント。
    クエリパラメータ 'path' を使用して基準となるディレクトリを指定。
    """
    base_path = request.args.get("path", "/")  # デフォルトはルートディレクトリ
    try:
        # 指定されたパス内のディレクトリをリストアップ
        directories = [
            {"name": name, "path": os.path.join(base_path, name)}
            for name in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, name))
        ]
        return jsonify({"status": "success", "directories": directories})
    except Exception as e:
        # エラーが発生した場合はエラーメッセージを返す
        return jsonify({"status": "error", "message": str(e)})


if __name__ == "__main__":
    # 引数のパーサーを設定
    parser = argparse.ArgumentParser(description="Run the Flask app.")
    parser.add_argument("--host", default="0.0.0.0", help="Host to listen on (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on (default: 5000)")
    args = parser.parse_args()

    # Flask アプリを起動
    app.run(host=args.host, port=args.port, debug=True)

from flask import Flask, request, jsonify, render_template
import argparse

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
        directory = request.form.get("directory")
        algorithm = request.form.get("algorithm")
        similarity = request.form.get("similarity")
        # 仮のレスポンス
        return jsonify({
            "status": "success",
            "directory": directory,
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

if __name__ == "__main__":
    # 引数のパーサーを設定
    parser = argparse.ArgumentParser(description="Run the Flask app.")
    parser.add_argument("--host", default="0.0.0.0", help="Host to listen on (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on (default: 5000)")
    args = parser.parse_args()

    # Flask アプリを起動
    app.run(host=args.host, port=args.port, debug=True)

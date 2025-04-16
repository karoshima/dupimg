from flask import Flask, render_template
import argparse

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/progress")
def progress():
    return render_template("progress.html")

@app.route("/results")
def results():
    return render_template("results.html")

@app.route("/trash")
def trash():
    return render_template("trash.html")

if __name__ == "__main__":
    # 引数のパーサーを設定
    parser = argparse.ArgumentParser(description="Run the Flask app.")
    parser.add_argument("--host", default="0.0.0.0", help="Host to listen on (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on (default: 5000)")
    args = parser.parse_args()

    # Flask アプリを起動
    app.run(host=args.host, port=args.port, debug=True)

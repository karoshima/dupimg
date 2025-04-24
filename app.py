import argparse
import os
from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint
from utils.api_handlers import register_routes
from utils.directory_utils import set_allowed_directories

SWAGGER_URL = '/api/docs'
API_URL = '/openapi.yaml'
swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL)

app = Flask(__name__)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# エンドポイントを登録
register_routes(app)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Flask app.")
    parser.add_argument(
        "directories",
        nargs="+",
        help="処理対象のディレクトリを1つ以上指定してください"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to listen on (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on (default: 5000)")
    args = parser.parse_args()

    # 指定されたディレクトリを絶対パスに変換して保持
    set_allowed_directories(args.directories)

    app.run(host=args.host, port=args.port, debug=True)

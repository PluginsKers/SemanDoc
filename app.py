from flask import Flask
from flask_cors import CORS

import os
from dotenv import load_dotenv

from src.views.api import api_blueprint
from src import initialize

# Load environment variables from the .env file
load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__, static_url_path="/")
    app.url_map.strict_slashes = False
    app.config.from_mapping(SECRET_KEY="super_secret_key")

    # 注册蓝图
    app.register_blueprint(api_blueprint, url_prefix="/api")

    # 允许 CORS
    # CORS(app, resources={r"/api/*": {"origins": "http://your_frontend_domain.com"}})
    # 或者使用通配符允许所有源访问（不推荐在生产环境中使用）
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    return app


if __name__ == "__main__":
    initialize()
    runtime = create_app()
    runtime.run("0.0.0.0", 7002, debug=bool(os.getenv(
        "DEBUG")))

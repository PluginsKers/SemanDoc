"""
文档
"""
from flask import Flask
from src.views.api import api_blue
from src.models.response import Response


def create_app() -> Flask:
    """
    创建服务
    """
    app = Flask(__name__, static_url_path='/')
    app.url_map.strict_slashes = False
    app.config.from_mapping(
        SECRET_KEY='super_secret_key'
    )

    @app.route('/')
    def hello():
        return Response("服务已经成功运行了").success()

    app.register_blueprint(api_blue, url_prefix='/api')
    return app

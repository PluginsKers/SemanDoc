from flask import Flask
from src.views.api import api_blueprint


from src.global_initializer import initialize


initialize()


def create_app() -> Flask:
    app = Flask(__name__, static_url_path='/')
    app.url_map.strict_slashes = False
    app.config.from_mapping(
        SECRET_KEY='super_secret_key'
    )

    app.register_blueprint(api_blueprint, url_prefix='/api')
    return app

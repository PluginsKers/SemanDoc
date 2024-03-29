from flask import Flask
from flask_cors import CORS

from src import app_manager
from src.views.api import blueprint


def create_app() -> Flask:
    app = Flask(__name__, static_url_path="/")
    app.url_map.strict_slashes = False

    app.register_blueprint(blueprint, url_prefix="/api")

    CORS(app, resources={r"/*": {"origins": "*"}})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(app_manager.IP, app_manager.PORT, debug=False)

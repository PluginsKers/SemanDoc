import logging
from flask import Flask
from flask_cors import CORS

from dotenv import load_dotenv

from src.views.api import api_blueprint
from src import initialize

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Load environment variables from the .env file
load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__, static_url_path="/")
    app.url_map.strict_slashes = False

    app.register_blueprint(api_blueprint, url_prefix="/api")

    CORS(app, resources={r"/*": {"origins": "*"}})

    return app


if __name__ == "__main__":
    initialize()
    runtime = create_app()
    runtime.run("0.0.0.0", 7002, debug=False)

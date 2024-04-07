from flask import g, Flask, request
from flask_cors import CORS
from flask_restful import Api
from config import BaseConfig
from src.utils.security import verify_jwt_token
from src.views import register_resources


def create_app() -> Flask:
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    CORS(app, resources={r"/*": {"origins": "*"}})

    @app.before_request
    def before_request_func():
        if request.path in BaseConfig.UNPROTECTED_ROUTES:
            return
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return {"message": BaseConfig.RESPONSE_LOGIN_INVALID_CREDENTIALS}, 403
        token = token.replace('Bearer ', '', 1)
        user_id = verify_jwt_token(token)
        if user_id:
            g.user_id = user_id  # Store user ID in Flask's global g object
            return
        else:
            return {"message": BaseConfig.RESPONSE_LOGIN_INVALID_CREDENTIALS}, 401
    api = Api(app)

    register_resources(api)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(BaseConfig.IP, BaseConfig.PORT, debug=False)


from functools import wraps
from flask import Blueprint, request

from src.utils.security import verify_jwt_token

from src.modules.response import Response

from src.views.routes.edit_routes import editor_blueprint
from src.views.routes.query_routes import query_blueprint
from src.views.routes.wecom_routes import wecom_blueprint
from src.views.routes.auth_routes import auth_blueprint

api_blueprint = Blueprint("api", __name__)


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return Response("Token is missing!", 403)

        token = token.replace('Bearer ', '', 1)
        if not verify_jwt_token(token):
            return Response("Token is invalid or has expired!", 401)

        return f(*args, **kwargs)

    return decorated_function


@api_blueprint.before_request
def before_request_func():
    if request.path.startswith("/api/auth/login") or request.path.startswith("/api/wecom"):
        return None
    return token_required(lambda: None)()


api_blueprint.register_blueprint(query_blueprint, url_prefix="/query")
api_blueprint.register_blueprint(editor_blueprint, url_prefix="/edit")
api_blueprint.register_blueprint(wecom_blueprint, url_prefix="/wecom")
api_blueprint.register_blueprint(auth_blueprint, url_prefix="/auth")

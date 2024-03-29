from functools import wraps
from flask import (
    Blueprint,
    request
)

from src import app_manager
from src.utils.security import verify_jwt_token
from src.modules import Response

from src.views.routes import (
    editor_blueprint,
    search_blueprint,
    wecom_blueprint,
    user_blueprint,
    auth_blueprint
)

blueprint = Blueprint("api", __name__)


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return Response(app_manager.RESPONSE_LOGIN_INVALID_CREDENTIALS, 403)

        token = token.replace('Bearer ', '', 1)
        if not verify_jwt_token(token):
            return Response(app_manager.RESPONSE_LOGIN_INVALID_CREDENTIALS, 401)

        return f(*args, **kwargs)

    return decorated_function


@blueprint.before_request
def before_request_func():
    if request.path.startswith("/api/auth/login") or request.path.startswith("/api/wecom"):
        return None
    return token_required(lambda: None)()


if app_manager.wecom_application is not None:
    blueprint.register_blueprint(wecom_blueprint, url_prefix="/wecom")

blueprint.register_blueprint(search_blueprint, url_prefix="/search")
blueprint.register_blueprint(editor_blueprint, url_prefix="/edit")

blueprint.register_blueprint(user_blueprint, url_prefix="/user")
blueprint.register_blueprint(auth_blueprint, url_prefix="/auth")

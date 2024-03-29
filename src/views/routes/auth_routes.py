from flask import Blueprint
from webargs import fields
from webargs.flaskparser import use_kwargs

from src import app_manager
from src.modules import Response
from src.controllers.auth_controllers import authenticate

auth_blueprint = Blueprint('auth', __name__)

login_args = {
    "username": fields.Str(required=True),
    "password": fields.Str(required=True)
}


@auth_blueprint.route('/login', methods=['POST'])
@use_kwargs(login_args, location="json")
def login(username, password):
    token = authenticate(username, password)
    if token:
        return Response(app_manager.RESPONSE_LOGIN_SUCCESS, 200, {"token": token})
    else:
        return Response(app_manager.RESPONSE_LOGIN_FAILED, 401)

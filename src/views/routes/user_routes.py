from flask import Blueprint, jsonify
from webargs import fields
from webargs.flaskparser import use_kwargs

from src.controllers.auth_controller import create_user
from src.modules.response import Response

user_blueprint = Blueprint('user', __name__)


create_user_args = {
    "username": fields.Str(required=True),
    "password": fields.Str(required=True),
    "nickname": fields.Str(missing="Test User")
}


@user_blueprint.route('/create', methods=['GET'])
@use_kwargs(create_user_args, location="query")
def create_user(username, password, nickname):
    ret, msg = create_user(username, password, nickname)
    if ret:
        return Response(msg, 200)
    else:
        return Response(msg, 400)

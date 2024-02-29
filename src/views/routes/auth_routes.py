from flask import Blueprint, jsonify
from webargs import fields
from webargs.flaskparser import use_kwargs

from src.controllers.auth_controller import authenticate, create_user
from src.modules.response import Response

auth_blueprint = Blueprint('auth', __name__)

login_args = {
    "username": fields.Str(required=True),
    "password": fields.Str(required=True)
}


@auth_blueprint.route('/login', methods=['POST', 'OPTIONS'])
@use_kwargs(login_args, location="json")
def login(username, password):
    token = authenticate(username, password)
    if token:
        return Response("Successful login", 200, data={"token": token})
    else:
        return Response("Invalid credentials", 401)


create_user_args = {
    "username": fields.Str(required=True),
    "password": fields.Str(required=True),
    "nickname": fields.Str(missing="Test User")  # Optional with default value
}


@auth_blueprint.route('/create_test_user', methods=['GET'])
@use_kwargs(create_user_args, location="query")
def create_test_user(username, password, nickname):
    result, msg = create_user(username, password, nickname)
    if result:
        return Response(msg, 200)
    else:
        return Response(msg, 400)

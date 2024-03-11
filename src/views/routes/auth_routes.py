from flask import Blueprint, jsonify
from webargs import fields
from webargs.flaskparser import use_kwargs

from src.controllers.auth_controller import authenticate
from src.modules.response import Response

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
        return Response("Successful login", 200, data={"token": token})
    else:
        return Response("Invalid credentials", 401)

from flask import Blueprint, request
from src.modules.response import Response
from src.controllers.support import error as error_func, reward as reward_func

support_blueprint = Blueprint('support', __name__)


@support_blueprint.route('/error', methods=['GET'])
def error_route():
    location = request.args.get('location', type=str)
    if not location:
        return Response('The "location" parameter is required.', 400)
    comment = request.args.get('comment', default='', type=str)
    return error_func(location, comment)


@support_blueprint.route('/reward')
def reward_route():
    location = request.args.get('location', type=str)
    if not location:
        return Response('The "location" parameter is required.', 400)
    comment = request.args.get('comment', default='', type=str)
    return reward_func(location, comment)

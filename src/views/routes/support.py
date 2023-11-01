from flask import Blueprint, request
from src.models.response import Response
from src.controllers.support import error as error_func, reward as reward_func

# Create a Flask Blueprint for the support routes
support_blue = Blueprint('support', __name__)


@support_blue.route('/error', methods=['GET'])
def error_route():
    """
    Route to report errors.

    Args:
        - location (str, required): The location where the error occurred.
        - remark (str, optional):
            Additional remarks (default is an empty string).

    Returns:
        - str: Response from the error reporting function.
    """
    argv_location = request.args.get('location', type=str)
    if not argv_location:
        return Response('The "location" parameter is required.').error()
    argv_remark = request.args.get('remark', default='', type=str)
    return error_func(argv_location, argv_remark)


@support_blue.route('/reward')
def reward_route():
    """
    Route to report rewards.

    Args:
        location (str, required): The location where the reward is granted.
        remark (str, optional): Additional remarks (default is an empty string).

    Returns:
        str: Response from the reward reporting function.
    """
    argv_location = request.args.get('location', type=str)
    if not argv_location:
        return Response('The "location" parameter is required.').error()
    argv_remark = request.args.get('remark', default='', type=str)
    return reward_func(argv_location, argv_remark)

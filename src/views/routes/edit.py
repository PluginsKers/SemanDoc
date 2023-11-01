from flask import Blueprint, request
from src.controllers.edit import add as add_func
from src.controllers.edit import delete as delete_func
from src.controllers.edit import update as update_func

# Create a Flask blueprint for the editor functionality
editor_blue = Blueprint('editor', __name__)

# Route for updating content in the index


@editor_blue.route('/update', methods=['GET'])
def update():
    """
    Update content in the index.
    """
    # Get the 'data' and 'remark' parameters from the request's query string
    args_data: str = request.args.get('data', type=str)
    args_remark: str = request.args.get('remark', type=str)

    # Call the update function from the controller with the obtained parameters
    return update_func(args_data, args_remark)

# Route for deleting content from the index


@editor_blue.route('/delete')
def delete():
    """
    Delete content from the index.
    """
    # Get the 'data' and 'remark' parameters from the request's query string
    args_data: str = request.args.get('data', type=str)
    args_remark: str = request.args.get('remark', type=str)

    # Call the delete function from the controller with the obtained parameters
    return delete_func(args_data, args_remark)

# Route for adding content to the index


@editor_blue.route('/add')
def add():
    """
    Add content to the index.
    """
    # Get the 'data' and 'remark' parameters from the request's query string
    args_data: str = request.args.get('data', type=str)
    args_remark: str = request.args.get('remark', type=str)

    # Call the add function from the controller with the obtained parameters
    return add_func(args_data, args_remark)

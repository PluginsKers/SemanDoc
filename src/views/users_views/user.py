from typing import Optional
from flask_restful import Resource, reqparse

from src import app_manager
from src import include_user_id
from src.services.user_service import create_user, delete_user_by_id, get_user_by_id, update_user


class UserResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser(bundle_errors=True)
        super().__init__()

    @include_user_id
    def get(self, id: Optional[int] = None, **kwargs):
        """
        TODO:
        - Implement the functionality to filter users by nickname.
        - Ensure that the 'id' and 'role_id' parameters are numeric (currently enforced by the route).
        - Add error handling to manage cases where the user cannot be found.

        Note:
        - Currently, the numeric constraints on 'id' and 'role_id' are enforced directly by the routing logic.
        - The 'nickname' parameter is only received through the query parameters of a GET request.
        """
        try:
            success, data = get_user_by_id(id, **kwargs)
            if success:
                return {'message': app_manager.RESPONSE_USER_QUERY_SUCCESS, 'data': data}, 200
            else:
                return {'message': app_manager.RESPONSE_USER_QUERY_FAILED}, 400
        except Exception as e:
            return {"message": f"{app_manager.RESPONSE_USER_QUERY_FAILED}: {str(e)}"}, 400

    @include_user_id
    def post(self, **kwargs):
        self.parser.add_argument(
            'username', type=str, required=True, help='Username is required.')
        self.parser.add_argument(
            'password', type=str, required=True, help='Password is required.')
        self.parser.add_argument(
            'role', type=int, required=True, help='Role of the user.')
        self.parser.add_argument(
            'nickname', type=str, default='User', help='Nickname of the user.')

        args = self.parser.parse_args()
        try:
            success, user_info = create_user(**args, **kwargs)

            if success:
                return {'message': app_manager.RESPONSE_USER_CREATE_SUCCESS, 'data': user_info}, 200
            else:
                return {'message': app_manager.RESPONSE_USER_CREATE_FAILED}, 400
        except Exception as e:
            return {"message": f"{app_manager.RESPONSE_USER_CREATE_FAILED}: {str(e)}"}, 400

    @include_user_id
    def delete(self, id: int, **kwargs):
        try:
            success = delete_user_by_id(id, **kwargs)
            if success:
                return {'message': app_manager.RESPONSE_USER_DELETE_SUCCESS}, 200
            else:
                return {'message': app_manager.RESPONSE_USER_DELETE_FAILED}, 400
        except Exception as e:
            return {"message": f"{app_manager.RESPONSE_USER_DELETE_FAILED}: {str(e)}"}, 400

    @include_user_id
    def put(self, id: Optional[int] = None, **kwargs):
        self.parser.add_argument('password', type=str,
                                 required=False, help='Password of the user.')
        self.parser.add_argument(
            'role', type=int, required=False, help='Role of the user.')
        self.parser.add_argument('nickname', type=str,
                                 required=False, help='Nickname of the user.')

        args = self.parser.parse_args()

        try:
            success = update_user(id, **args, **kwargs)

            if success:
                return {'message': app_manager.RESPONSE_USER_UPDATE_SUCCESS}, 200
            else:
                return {'message': app_manager.RESPONSE_USER_UPDATE_FAILED}, 400
        except Exception as e:
            return {"message": f"{app_manager.RESPONSE_USER_UPDATE_FAILED}: {str(e)}"}, 400

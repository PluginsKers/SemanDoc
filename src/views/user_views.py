from flask_restful import Resource, reqparse

from src.services.auth_service import create_user


class UserResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser(bundle_errors=True)
        super().__init__()  # Updated to use Python 3 super() syntax

    def get(self, id=None):
        # Implementation for retrieving user data by id
        pass

    def post(self):
        self.parser.add_argument(
            'username', type=str, required=True, help='Username is required.')
        self.parser.add_argument(
            'password', type=str, required=True, help='Password is required.')
        self.parser.add_argument(
            'nickname', type=str, default='Test User', help='Nickname of the user.')

        args = self.parser.parse_args()

        success, message = create_user(**args)

        return {'message': message}, 200 if success else 400

    def delete(self, id):
        # Implementation for deleting user data by id
        pass

from . import AuthResource
from src import app_manager
from src.services.auth_service import authenticate


class LoginResource(AuthResource):
    def __init__(self):
        super(LoginResource, self).__init__()

    def post(self):
        self.reqparse.add_argument('username', type=str, required=True,
                                   help='Username cannot be blank')
        self.reqparse.add_argument('password', type=str, required=True,
                                   help='Password cannot be blank')

        args = self.reqparse.parse_args()

        token = authenticate(args['username'], args['password'])

        if token:
            return {"message": app_manager.RESPONSE_LOGIN_SUCCESS, "token": token}, 200
        else:
            return {"message": app_manager.RESPONSE_LOGIN_FAILED}, 401

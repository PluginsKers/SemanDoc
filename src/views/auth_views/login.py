from . import AuthResource
from src import app_manager
from src.services.auth_service import authenticate


class LoginResource(AuthResource):
    def __init__(self):
        super(LoginResource, self).__init__()

    def post(self):
        self.reqparse.add_argument(
            'username', type=str, required=True, help='Username cannot be blank'
        )
        self.reqparse.add_argument(
            'password', type=str, required=True, help='Password cannot be blank'
        )

        args = self.reqparse.parse_args()

        try:
            token, userdata = authenticate(**args)

            del userdata["password"]
            del userdata["id"]

            if token:
                return {
                    "message": app_manager.RESPONSE_LOGIN_SUCCESS,
                    "token": token,
                    "data": userdata
                }, 200
            else:
                return {
                    "message": app_manager.RESPONSE_LOGIN_FAILED
                }, 401
        except Exception as e:
            return {
                "message": f"{app_manager.RESPONSE_LOGIN_FAILED}: {str(e)}"
            }, 400

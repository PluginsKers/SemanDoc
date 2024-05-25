from flask_restful import Resource, reqparse

from src.services.chat_service import chat


class ChatResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser(bundle_errors=True)
        super().__init__()

    def get(self):
        self.parser.add_argument(
            'query', type=str, required=True, help='No query provided', location='args'
        )
        self.parser.add_argument(
            'dep_name', type=str, required=True, help='No dep_name provided', location='args'
        )
        args = self.parser.parse_args()

        try:
            success, data = chat(**args)
            if success:
                return {
                    'data': data
                }
            else:
                return {
                    'message': None
                }, 400
        except Exception as e:
            return {
                "message": f"{str(e)}"
            }, 400

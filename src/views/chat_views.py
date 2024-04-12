from flask_restful import Resource, reqparse

from src.services.document_service import chat_with_kb
from src import app_manager
from src import include_user_id


class ChatResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser(bundle_errors=True)
        super().__init__()

    def get(self):
        self.parser.add_argument(
            'query', type=str, required=True, help='No query provided', location='args')
        self.parser.add_argument(
            'dep_name', type=str, required=True, help='No dep_name provided', location='args')
        args = self.parser.parse_args()
        response = chat_with_kb(**args)
        return {'data': response}

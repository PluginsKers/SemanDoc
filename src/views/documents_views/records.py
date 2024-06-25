import json
from flask_restful import Resource, reqparse, inputs
from flask import request
from src import app_manager, include_user_id
from src.services.document_service import get_documents_records


class DocumentsRecordsResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument(
            'limit', type=int, required=False, default=50, help='Limit the number of records returned')
        super(DocumentsRecordsResource, self).__init__()

    @include_user_id
    def get(self, **kwargs):
        try:
            # Check if Content-Type is set to application/json, but only for methods that need it
            if request.content_type and request.content_type != 'application/json':
                return {
                    "message": "Unsupported Media Type: Content-Type must be application/json"
                }, 415

            records = get_documents_records(**kwargs)
            return {
                "message": app_manager.RESPONSE_DOCUMENTS_RECORDS_LOAD_SUCCESS,
                "data": records
            }, 200
        except Exception as e:
            return {
                "message": f"{app_manager.RESPONSE_DOCUMENTS_RECORDS_LOAD_FAILED}: {str(e)}"
            }, 400

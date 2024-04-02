from flask_restful import Resource, reqparse, inputs

from src import app_manager
from src.services.document_service import (
    get_documents,
    add_document,
    delete_documents_by_ids,
    update_document
)


class DocumentResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser(bundle_errors=True)
        super(DocumentResource, self).__init__()

    def get(self):
        self.parser.add_argument(
            'query', type=str, required=True, help='No query provided', location='args')
        self.parser.add_argument('k', type=int, default=6, location='args')
        self.parser.add_argument('filter', type=dict, location='args')
        self.parser.add_argument(
            'score_threshold', type=float, default=1.0, location='args')
        self.parser.add_argument(
            'powerset', type=inputs.boolean, default=True, location='args')
        args = self.parser.parse_args()

        documents = get_documents(**args)
        return {"message": app_manager.RESPONSE_DOCUMENT_SEARCH_SUCCESS, "data": documents}, 200

    def post(self):
        self.parser.add_argument(
            'data', type=str, required=True, help='No data provided', location='json')
        self.parser.add_argument(
            'metadata', type=dict, required=True, location='json')
        args = self.parser.parse_args()
        document = add_document(**args)
        return {"message": app_manager.RESPONSE_DOCUMENT_ADD_SUCCESS, "data": [d.to_dict() for d in document]}, 201

    def put(self, id):
        self.parser.add_argument(
            'data', type=str, required=True, help='No data provided', location='json')
        self.parser.add_argument(
            'metadata', type=dict, required=True, location='json')
        args = self.parser.parse_args()

        updated_document = update_document(id, args)

        if updated_document is None:
            return {"message": app_manager.RESPONSE_DOCUMENT_UPDATE_FAIL}, 404

        return {"message": app_manager.RESPONSE_DOCUMENT_UPDATE_SUCCESS, "data": updated_document.to_dict()}, 200

    def delete(self, id):
        deletion_result = delete_documents_by_ids([id])
        if isinstance(deletion_result, tuple) and deletion_result[0] != 0:
            return {"message": app_manager.RESPONSE_DOCUMENT_REMOVE_SUCCESS, "data": deletion_result}

        return {"message": app_manager.RESPONSE_DOCUMENT_REMOVE_FAIL}, 404

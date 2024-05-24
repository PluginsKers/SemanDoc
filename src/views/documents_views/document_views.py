import json
from flask_restful import Resource, reqparse

from src import app_manager, include_user_id
from src.services.document_service import (
    add_document,
    delete_documents_by_ids,
    update_document
)


class DocumentResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser(bundle_errors=True)
        super(DocumentResource, self).__init__()

    @include_user_id
    def post(self, **kwargs):
        self.parser.add_argument(
            'data', type=str, required=True, help='No data provided', location='json'
        )
        self.parser.add_argument(
            'metadata', type=dict, required=True, location='json'
        )
        args = self.parser.parse_args()
        try:
            document = add_document(**args, **kwargs)

            if document:
                return {
                    "message": app_manager.RESPONSE_DOCUMENT_ADD_SUCCESS,
                    "data": [d.to_dict() for d in document]
                }, 200
            else:
                return {"message": app_manager.RESPONSE_DOCUMENT_ADD_FAILED}, 400
        except Exception as e:
            return {
                "message": f"{app_manager.RESPONSE_DOCUMENT_ADD_FAILED}: {str(e)}"
            }, 400

    @include_user_id
    def put(self, id, **kwargs):
        self.parser.add_argument(
            'data', type=str, required=True, help='No data provided', location='json'
        )
        self.parser.add_argument(
            'metadata', type=dict, required=True, location='json'
        )
        args = self.parser.parse_args()

        updated_document = update_document(id, args, **kwargs)

        if updated_document is None:
            return {"message": app_manager.RESPONSE_DOCUMENT_UPDATE_FAILED}, 404

        return {
            "message": app_manager.RESPONSE_DOCUMENT_UPDATE_SUCCESS,
            "data": updated_document.to_dict()
        }, 200

    @include_user_id
    def delete(self, id, **kwargs):
        try:
            deletion_result = delete_documents_by_ids([id], **kwargs)
            if isinstance(deletion_result, tuple) and deletion_result[0] != 0:
                return {
                    "message": app_manager.RESPONSE_DOCUMENT_REMOVE_SUCCESS,
                    "data": deletion_result
                }

            return {"message": app_manager.RESPONSE_DOCUMENT_REMOVE_FAILED}, 404
        except Exception as e:
            return {
                "message": f"{app_manager.RESPONSE_DOCUMENT_REMOVE_FAILED}: {str(e)}"
            }, 400

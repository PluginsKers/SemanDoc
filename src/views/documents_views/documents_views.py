import json
from flask_restful import Resource, reqparse, inputs

from src import app_manager, include_user_id
from src.services.document_service import (
    delete_documents_by_ids,
    get_documents
)


class DocumentsResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser(bundle_errors=True)
        super(DocumentsResource, self).__init__()

    @include_user_id
    def get(self, **kwargs):
        self.parser.add_argument(
            'query', type=str, required=True, help='No query provided', location='args'
        )
        self.parser.add_argument('k', type=int, default=6, location='args'
                                 )
        self.parser.add_argument('filter', type=str, location='args'
                                 )
        self.parser.add_argument(
            'score_threshold', type=float, default=1.0, location='args'
        )
        self.parser.add_argument(
            'powerset', type=inputs.boolean, default=True, location='args'
        )
        args = self.parser.parse_args()
        try:
            if args['filter']:
                try:
                    args['filter'] = json.loads(args['filter'])
                except ValueError:
                    return {
                        "message": "Invalid 'filter' format, must be a valid JSON string."
                    }, 400

            documents = get_documents(**args, **kwargs)
            return {
                "message": app_manager.RESPONSE_DOCUMENT_SEARCH_SUCCESS, "data": documents
            }, 200
        except Exception as e:
            return {
                "message": f"{app_manager.RESPONSE_DOCUMENT_SEARCH_SUCCESS}: {str(e)}"
            }, 400

    @include_user_id
    def delete(self, **kwargs):
        self.parser.add_argument(
            'ids', type=list, required=True, help='No target ids provided', location='json'
        )
        args = self.parser.parse_args()
        try:
            deletion_result = delete_documents_by_ids(
                args['ids'], **kwargs
            )
            if isinstance(deletion_result, tuple) and deletion_result[0] != 0:
                return {
                    "message": app_manager.RESPONSE_DOCUMENT_REMOVE_SUCCESS + f" 共删除{deletion_result[0]}条",
                    "data": deletion_result
                }

            return {
                "message": app_manager.RESPONSE_DOCUMENT_REMOVE_FAILED
            }, 404
        except Exception as e:
            return {
                "message": f"{app_manager.RESPONSE_DOCUMENT_REMOVE_FAILED}: {str(e)}"
            }, 400

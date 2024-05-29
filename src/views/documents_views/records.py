import json
from flask_restful import Resource, reqparse, inputs

from src import app_manager, include_user_id
from src.services.document_service import (
    get_documents_records
)


class DocumentsRecordsResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser(bundle_errors=True)
        super(DocumentsRecordsResource, self).__init__()

    @include_user_id
    def get(self, **kwargs):
        try:
            records = get_documents_records(**kwargs)
            return {
                "message": app_manager.RESPONSE_DOCUMENTS_RECORDS_LOAD_SUCCESS, "data": records
            }, 200
        except Exception as e:
            return {
                "message": f"{app_manager.RESPONSE_DOCUMENTS_RECORDS_LOAD_FAILED}: {str(e)}"
            }, 400

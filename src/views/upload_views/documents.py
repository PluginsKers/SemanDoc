import os
from flask import request
from flask_restful import Resource
from werkzeug.utils import secure_filename

from src import app_manager, include_user_id
from src.services.document_service import add_documents
from src.utils.formatting import process_excel_file


class DocumentUploadResource(Resource):
    def __init__(self):
        super().__init__()

    @include_user_id
    def post(self, **kwargs):
        if 'file' not in request.files:
            return {"message": app_manager.RESPONSE_DOCUMENT_ADD_FAILED}, 400

        file = request.files['file']

        # empty part without filename
        if file.filename == '':
            return {"message": app_manager.RESPONSE_DOCUMENT_ADD_FAILED}, 400

        if file and file.filename.endswith('.xlsx'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app_manager.TMP_FILE_PATH, filename)
            file.save(filepath)

            processed_data = process_excel_file(filepath)

            if not processed_data:
                return {"message": app_manager.RESPONSE_DOCUMENT_ADD_FAILED}, 400

            documents = add_documents(processed_data, **kwargs)

            if documents:
                return {"message": app_manager.RESPONSE_DOCUMENT_ADD_SUCCESS, "data": [doc.to_dict() for doc in documents]}, 200
            else:
                return {"message": app_manager.RESPONSE_DOCUMENT_ADD_FAILED}, 400
        else:
            return {"message": app_manager.RESPONSE_DOCUMENT_ADD_FAILED}, 400

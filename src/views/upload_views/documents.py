import os
import hashlib
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
        try:
            if 'file' not in request.files:
                return {"message": app_manager.RESPONSE_DOCUMENT_ADD_FAILED}, 400

            file = request.files['file']

            if file.filename == '':
                return {"message": app_manager.RESPONSE_DOCUMENT_ADD_FAILED}, 400

            if file and file.filename.endswith('.xlsx'):
                original_filename = secure_filename(file.filename)
                # Create a secure hash of the original file name
                hash_filename = hashlib.sha256(
                    original_filename.encode()).hexdigest()
                # Append the file extension to maintain the file type
                encrypted_filename = f"{hash_filename}.xlsx"
                filepath = os.path.join(
                    app_manager.TMP_FILE_PATH, encrypted_filename)

                # Check and create the directory if it does not exist
                if not os.path.exists(app_manager.TMP_FILE_PATH):
                    try:
                        os.makedirs(app_manager.TMP_FILE_PATH)
                    except Exception as e:
                        return {"message": f"Failed to create directory: {e}"}, 500

                file.save(filepath)

                processed_data = process_excel_file(filepath)

                if not processed_data:
                    return {"message": app_manager.RESPONSE_DOCUMENT_ADD_FAILED}, 400

                # Initialize counters for statistics
                success_count = 0
                failure_count = 0

                documents = add_documents(processed_data, **kwargs)

                # Count successes and failures
                for document in processed_data:
                    if document in documents:
                        success_count += 1
                    else:
                        failure_count += 1

                if documents:
                    return {
                        "message": app_manager.RESPONSE_DOCUMENT_ADD_SUCCESS,
                        "data": [doc.to_dict() for doc in documents],
                        "statistics": {
                            "success_count": success_count,
                            "failure_count": failure_count
                        }
                    }, 200
                else:
                    return {"message": app_manager.RESPONSE_DOCUMENT_ADD_FAILED}, 400
            else:
                return {"message": app_manager.RESPONSE_DOCUMENT_ADD_FAILED}, 400
        except Exception as e:
            return {"message": f"{app_manager.RESPONSE_DOCUMENT_ADD_FAILED}: {str(e)}"}, 400

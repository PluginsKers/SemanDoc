import time
import pandas as pd
from io import BytesIO
from flask import Response
from flask_restful import Resource
from src import app_manager, include_user_id
from src.utils.formatting import reverse_document_formatting


class DocumentsDownloadResource(Resource):
    def __init__(self):
        self.document_service = app_manager.get_vector_store()
        super(DocumentsDownloadResource, self).__init__()

    @include_user_id
    def get(self, **kwargs):
        try:
            documents = self.document_service.get_all_documents()

            filename = str(time.time()) + ".xlsx"

            data = []
            for doc in documents:
                raw_metadata = reverse_document_formatting(doc)
                data.append([doc.page_content + raw_metadata])

            df = pd.DataFrame(data, columns=["data"])

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False,
                            sheet_name='Documents', header=False)
            output.seek(0)

            response = Response(
                output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            response.headers["Content-Disposition"] = f"attachment; filename={filename}"
            return response

        except Exception as e:
            return {
                "message": f"{app_manager.RESPONSE_DOCUMENT_SEARCH_SUCCESS}: {str(e)}"
            }, 400

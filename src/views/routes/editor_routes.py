import os
from flask import (
    request,
    Blueprint
)
from webargs.flaskparser import use_kwargs
from werkzeug.utils import secure_filename
from webargs import (
    fields,
    validate
)

from src import app_manager
from src.modules import Response
from src.modules.document import Document
from src.controllers.editor_controllers import (
    add_document,
    delete_documents_by_ids,
    update_document_by_ids
)

editor_blueprint = Blueprint("editor", __name__)

allow_ctl_method = ["ids"]

update_args = {
    "target": fields.Str(required=True),
    "type": fields.Str(required=True, validate=validate.OneOf(allow_ctl_method)),
    "data": fields.Str(required=True, validate=lambda val: len(val) > 5),
    "metadata": fields.Dict(required=True)
}

delete_args = {
    "target": fields.List(fields.Str(), required=True),
    "type": fields.Str(required=True, validate=validate.OneOf(allow_ctl_method))
}

add_args = {
    "data": fields.Str(required=True, validate=lambda val: len(val) > 5),
    "metadata": fields.Dict(required=True),
    "has_file": fields.Bool(required=False, missing=False)
}


@editor_blueprint.route("/update", methods=['POST'])
@use_kwargs(update_args, location="json")
def update_document_route(target: int, type: str, data: str, metadata: dict):
    try:
        _func = {
            "ids": update_document_by_ids,
        }

        doc = _func[type](
            target,
            Document(data, metadata).to_dict()
        )

        if isinstance(doc, Document):
            docs = [doc.to_dict()]
            return Response(app_manager.RESPONSE_DOCUMENT_UPDATE_SUCCESS, 200, docs)

        return Response(app_manager.RESPONSE_UNKNOWN_ERROR, 400)

    except Exception as error:
        return Response(app_manager.RESPONSE_CATCH_ERROR.format(error), 400)


@editor_blueprint.route("/delete", methods=['POST'])
@use_kwargs(delete_args, location="json")
def delete_documents_route(target: list, type: str):
    try:
        # Use a dictionary for type mapping for better readability
        _func = {
            "ids": delete_documents_by_ids
        }

        _ret = _func[type](target)

        if isinstance(_ret, tuple):
            n_removed, n_total = _ret
            return Response(
                app_manager.RESPONSE_DOCUMENT_REMOVE_SUCCESS,
                200,
                {
                    "removed": n_removed,
                    "total": n_total,
                    "remaining": n_total - n_removed,
                },
            )

        return Response(app_manager.RESPONSE_UNKNOWN_ERROR, 400)

    except Exception as error:
        return Response(app_manager.RESPONSE_CATCH_ERROR.format(error), 400)


@editor_blueprint.route("/add", methods=['POST'])
@use_kwargs(add_args, location="json")
def add_document_route(data: str, metadata: dict, has_file: bool):
    try:
        if has_file and 'file' in request.files:
            # TODO: Add functionality to read files and configure local file paths
            pass

        if not data:
            return Response("Data is required when no file is uploaded or has_file is false.", 400)

        if not has_file:
            doc_obj = {"page_content": data, "metadata": metadata}
            docs = add_document(doc_obj)
            if isinstance(docs, list):
                _docs = [doc.to_dict() for doc in docs]
                return Response(app_manager.RESPONSE_DOCUMENT_ADD_SUCCESS, 200, _docs)

        return Response(app_manager.RESPONSE_UNKNOWN_ERROR, 400)

    except Exception as error:
        return Response(app_manager.RESPONSE_CATCH_ERROR.format(error), 400)

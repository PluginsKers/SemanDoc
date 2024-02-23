import json
from flask import Blueprint
from webargs import fields, validate
from webargs.flaskparser import use_kwargs
from src.modules.response import Response
from src.modules.string_processor import processor
from src.controllers.edit_controller import (
    DatabaseEditError,
    add_document,
    delete_documents_by_id,
    delete_documents_by_ids,
    delete_documents_by_tags,
)

# Create Blueprint
editor_blueprint = Blueprint("editor", __name__)

# Define request arguments with improved type checking and default values
shared_args = {
    "comment": fields.Str(missing=None),
}

remove_args = {
    "target": fields.Str(required=True),
    "type": fields.Str(required=True, validate=validate.OneOf(["ids", "tags", "id"])),
    **shared_args,
}

add_args = {
    "data": fields.Str(required=True),
    "metadata": fields.Str(required=True),
    "preprocess": fields.Bool(missing=False),
    **shared_args,
}


@editor_blueprint.route("/remove")
@use_kwargs(remove_args, location="query")
def remove_document_route(target: str, type: str, comment: str):
    try:
        target_list = json.loads(target)
        if not isinstance(target_list, list):
            raise TypeError("Invalid target format. Expected list of IDs.")

        # Use a dictionary for type mapping for better readability
        delete_functions = {
            "ids": delete_documents_by_ids,
            "tags": delete_documents_by_tags,
            "id": delete_documents_by_id,
        }

        res = delete_functions[type](target_list, comment)

        if isinstance(res, tuple):
            n_removed, n_total = res
            return Response(
                "Documents deleted successfully.",
                200,
                data={
                    "removed": n_removed,
                    "total": n_total,
                    "remaining": n_total - n_removed,
                },
            )

        return Response("Unknown error occurred.", 400)

    except (json.JSONDecodeError, TypeError) as error:
        return Response(f"Invalid input data: {error}", 400)
    except DatabaseEditError as error:
        return Response(f"Database operation failed: {error}", 400)


@editor_blueprint.route("/add")
@use_kwargs(add_args, location="query")
async def add_document_route(data: str, metadata: str, comment: str, preprocess: bool):
    try:
        metadata_dict = json.loads(metadata)
        if not isinstance(metadata_dict, dict):
            raise TypeError("Invalid metadata format. Expected dictionary.")

        if preprocess:
            data = processor.replace_char_by_list(
                data, [(",", "，"), (": ", "："), ("!", "！"), ("?", "？")]
            )

        doc_obj = {"page_content": data, "metadata": metadata_dict}

        res = await add_document(doc_obj, comment)

        if isinstance(res, tuple) and res[0]:
            added_docs = [doc.to_dict() for doc in res[0]]
            return Response("Documents added successfully.", 200, data=added_docs)

        return Response("Unknown error occurred.", 400)

    except (json.JSONDecodeError, TypeError) as error:
        return Response(f"Invalid input data: {error}", 400)
    except DatabaseEditError as error:
        return Response(f"Database operation failed: {error}", 400)

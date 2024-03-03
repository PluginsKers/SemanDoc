import json
from flask import Blueprint
from webargs import fields, validate
from webargs.flaskparser import use_kwargs
from src.modules.document.vecstore import VectorStoreEditError
from src.modules.response import Response
from src.modules.string_processor import processor
from src.controllers.edit_controller import (
    add_document,
    delete_documents_by_id,
    delete_documents_by_ids,
    delete_documents_by_tags,
)

editor_blueprint = Blueprint("editor", __name__)

shared_args = {
    "comment": fields.Str(missing=None),
}

remove_args = {
    "target": fields.List(fields.Int(), required=True),
    "type": fields.Str(required=True, validate=validate.OneOf(["ids", "tags", "id"])),
    **shared_args,
}

add_args = {
    "data": fields.Str(required=True, validate=lambda val: len(val) > 5),
    "metadata": fields.Dict(required=True),
    "preprocess": fields.Bool(missing=False),
    **shared_args,
}


@editor_blueprint.route("/remove", methods=['POST', 'OPTIONS'])
@use_kwargs(remove_args, location="json")
def remove_document_route(target: list, type: str, comment: str):
    try:
        # Use a dictionary for type mapping for better readability
        delete_functions = {
            "ids": delete_documents_by_ids,
            "tags": delete_documents_by_tags,
            "id": delete_documents_by_id,
        }

        results = delete_functions[type](target, comment)

        if isinstance(results, tuple):
            n_removed, n_total = results
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
    except VectorStoreEditError as error:
        return Response(f"VectorStore operation failed: {error}", 400)


@editor_blueprint.route("/add", methods=['POST', 'OPTIONS'])
@use_kwargs(add_args, location="json")
async def add_document_route(data: str, metadata: dict, comment: str, preprocess: bool):
    try:
        if preprocess:
            data = processor.replace_char_by_list(
                data, [(",", "，"), (": ", "："), ("!", "！"), ("?", "？")]
            )

        doc_obj = {"page_content": data, "metadata": metadata}

        results = await add_document(doc_obj, comment)

        if isinstance(results, tuple) and results[0]:
            added_docs = [doc.to_dict() for doc in results[0]]
            return Response("Documents added successfully.", 200, data=added_docs)

        return Response("Unknown error occurred.", 400)

    except (json.JSONDecodeError, TypeError) as error:
        return Response(f"Invalid input data: {error}", 400)
    except VectorStoreEditError as error:
        return Response(f"VectorStore operation failed: {error}", 400)

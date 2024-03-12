import json
from typing import List
from flask import Blueprint
from webargs import fields, validate
from webargs.flaskparser import use_kwargs
from src.modules.document import Document
from src.modules.document.vecstore import VecstoreError
from src.modules.response import Response
from src.modules.string_processor import processor
from src.controllers.edit_controller import (
    add_document,
    delete_documents_by_ids,
    modify_document_by_ids,
    delete_documents_by_tags,
)

editor_blueprint = Blueprint("editor", __name__)

modify_args = {
    "target": fields.Int(required=True),
    "type": fields.Str(required=True, validate=validate.OneOf(["ids", "tags", "id"])),
    "data": fields.Str(required=True, validate=lambda val: len(val) > 5),
    "metadata": fields.Dict(required=True)
}

remove_args = {
    "target": fields.List(fields.Int(), required=True),
    "type": fields.Str(required=True, validate=validate.OneOf(["ids", "tags", "id"]))
}

add_args = {
    "data": fields.Str(required=True, validate=lambda val: len(val) > 5),
    "metadata": fields.Dict(required=True),
    "preprocess": fields.Bool(missing=False)
}


@editor_blueprint.route("/modify", methods=['POST'])
@use_kwargs(modify_args, location="json")
async def modify_document_route(target: int, type: str, data: str, metadata: dict):
    try:
        modify_functions = {
            "ids": modify_document_by_ids,
        }

        result_doc = await modify_functions[type](target, Document(data, metadata).to_dict())

        if isinstance(result_doc, Document):
            docs = [result_doc.to_dict()]
            return Response("Documents modify successfully.", 200, data=docs)

        return Response("Unknown error occurred.", 400)

    except (json.JSONDecodeError, TypeError) as error:
        return Response(f"Invalid input data: {error}", 400)
    except VecstoreError as error:
        return Response(f"VectorStore operation failed: {error}", 400)


@editor_blueprint.route("/remove", methods=['POST'])
@use_kwargs(remove_args, location="json")
async def remove_document_route(target: list, type: str):
    try:
        # Use a dictionary for type mapping for better readability
        delete_functions = {
            "ids": delete_documents_by_ids,
            "tags": delete_documents_by_tags,
        }

        results = await delete_functions[type](target)

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
    except VecstoreError as error:
        return Response(f"VectorStore operation failed: {error}", 400)


@editor_blueprint.route("/add", methods=['POST'])
@use_kwargs(add_args, location="json")
async def add_document_route(data: str, metadata: dict, preprocess: bool):
    try:
        if preprocess:
            data = processor.replace_char_by_list(
                data,
                [
                    (",", "，"),
                    (": ", "："),
                    ("!", "！"),
                    ("?", "？"),
                    ("\n", " ")
                ]
            )

        doc_obj = {"page_content": data, "metadata": metadata}

        result = await add_document(doc_obj)
        if isinstance(result, list):
            added_docs = [doc.to_dict() for doc in result]
            return Response("Documents added successfully.", 200, data=added_docs)

        return Response("Unknown error occurred.", 400)

    except (json.JSONDecodeError, TypeError) as error:
        return Response(f"Invalid input data: {error}", 400)
    except VecstoreError as error:
        return Response(f"VectorStore operation failed: {error}", 400)

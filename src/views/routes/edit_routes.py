import json
import os
from typing import List
from flask import request, Blueprint
from werkzeug.utils import secure_filename
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
    "has_file": fields.Bool(required=False, missing=False)
}


@editor_blueprint.route("/modify", methods=['POST'])
@use_kwargs(modify_args, location="json")
async def modify_document_route(target: int, type: str, data: str, metadata: dict):
    try:
        modify_functions = {
            "ids": modify_document_by_ids,
        }

        modify_result = await modify_functions[type](target, Document(data, metadata).to_dict())

        if isinstance(modify_result, Document):
            docs = [modify_result.to_dict()]
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
async def add_document_route(data: str, metadata: dict, has_file: bool):
    try:
        # 当有文件上传且has_file为true时的处理逻辑
        if has_file and 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return Response("No selected file", 400)
            if file:
                filename = secure_filename(file.filename)
                save_path = os.path.join("./data/.temp/", filename)
                file.save(save_path)
                # 使用file_reader处理文件并获取文档列表

                def file_reader():
                    return []
                documents = file_reader(save_path)  # 假设这个函数返回List[Document]

                # 处理完成，返回给前端，包含confirm: true标记
                # 假设你有方法将Document对象转换为dict
                documents_dict = [doc.to_dict() for doc in documents]
                return Response("测试成功", 200, {"data": documents_dict, "confirm": True})

        # 当不是通过文件上传文档时的处理逻辑
        if not data:
            return Response("Data is required when no file is uploaded or has_file is false.", 400)

        if not has_file:
            # 仅当没有文件上传时，才进行文档的数据库写入操作
            document_object = {"page_content": data, "metadata": metadata}
            add_result = await add_document(document_object)
            if isinstance(add_result, list):
                added_document_dicts = [doc.to_dict() for doc in add_result]
                return Response("Documents added successfully.", 200, data=added_document_dicts)

        return Response("Unknown error occurred.", 400)

    except (json.JSONDecodeError, TypeError) as error:
        return Response(f"Invalid input data: {error}", 400)
    except VecstoreError as error:
        return Response(f"VectorStore operation failed: {error}", 400)

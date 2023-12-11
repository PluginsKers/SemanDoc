import json
from flask import Blueprint, request
from src.modules.response import Response
from src.modules.string_processor import processor

from src.controllers.edit import (
    DatabaseEditError,
    add_document,
    delete_documents_by_id,
    delete_documents_by_ids,
    delete_documents_by_tags
)

editor_blueprint = Blueprint('editor', __name__)


# 这个部分本来是有关于修改内容的业务逻辑
# @editor_blueprint.route('/update', methods=['GET'])
# def update_document_route():
#     raw_data: str = request.args.get('data', type=str)
#     comment: str = request.args.get('comment', type=str, default=None)

#     try:
#         data_dict = json.loads(raw_data)
#     except json.JSONDecodeError:
#         return Response('参数错误', 400)

#     if isinstance(data_dict, dict):
#         if not data_dict.get('target_ids'):
#             return Response('参数错误，缺少target_ids', 400)

#     return update_document(data_dict, comment)


@editor_blueprint.route('/remove')
def remove_document_route():
    target: str = request.args.get('target', type=str)
    req_type: str = request.args.get('type', type=str)
    comment: str = request.args.get('comment', type=str, default=None)

    try:
        target_list = json.loads(target)
        if not isinstance(target_list, list):
            raise TypeError('参数 target 错误')

        valid_types = ["ids", "tags", "id"]
        if req_type not in valid_types:
            raise TypeError(f"应为 {', '.join(valid_types)}")

        if req_type == 'ids':
            res = delete_documents_by_ids(target_list, comment)
        elif req_type == 'tags':
            res = delete_documents_by_tags(target_list, comment)
        else:  # req_type == 'id'
            res = delete_documents_by_id(target_list, comment)

        if isinstance(res, tuple):
            n_removed, n_total = res
            return Response(
                '删除成功',
                200,
                data={
                    "removed": n_removed,
                    "total": n_total,
                    "now": n_total - n_removed
                }
            )

        return Response(f'未知错误: {res}', 400)
    except json.JSONDecodeError:
        return Response('JSON 解析错误: 无效的 JSON 格式', 400)
    except DatabaseEditError as error:
        return Response(f'操作时出错: {error}', 400)
    except ValueError as error:
        return Response(f'数据错误: {error}', 400)
    except TypeError as error:
        return Response(f'参数错误: {error}', 400)


@editor_blueprint.route('/add')
async def add_document_route():
    data: str = request.args.get('data', type=str)
    metadata: str = request.args.get('metadata', type=str)
    comment: str = request.args.get('comment', type=str, default=None)
    preprocess: str = request.args.get('preprocess', type=bool, default=False)

    try:
        if not data:
            raise ValueError('缺少 data 参数')

        metadata_dict = json.loads(metadata)

        if not isinstance(metadata_dict, dict):
            raise TypeError('参数 metadata 错误')

        if preprocess:
            data = processor.replace_char_by_list(
                data,
                [
                    [",", "，"],
                    [": ", "："],
                    ["!", "！"],
                    ["?", "？"]
                ]
            )

        doc_obj = {
            'page_content': data,
            'metadata': metadata_dict
        }

        res = await add_document(doc_obj, comment)

        if isinstance(res, tuple) and res[0]:
            added_docs = [doc.to_dict() for doc in res[0]]
            return Response('添加成功', 200, data=added_docs)

        return Response(f'未知错误: {res}', 400)
    except json.JSONDecodeError:
        return Response('JSON 解析错误: 无效的 JSON 格式', 400)
    except DatabaseEditError as error:
        return Response(f'操作时出错: {error}', 400)
    except ValueError as error:
        return Response(f'数据错误: {error}', 400)
    except TypeError as error:
        return Response(f'参数错误: {error}', 400)

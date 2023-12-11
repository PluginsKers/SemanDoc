import json

from flask import Blueprint, request
from src.modules.response import Response
from src.controllers.query import search_documents

query_blueprint = Blueprint('query', __name__)


@query_blueprint.route('/', methods=['GET'])
async def query_route():
    query = request.args.get('query', type=str)
    k = request.args.get('k', type=int)
    _filter = request.args.get('filter', type=str)

    try:
        if query is None or len(query) == 0:
            raise ValueError('参数 query 错误')

        f_dict = None
        if _filter:
            f_dict = json.loads(_filter)

            if not isinstance(f_dict, dict):
                raise TypeError('参数 filter 错误')

        res = await search_documents(
            query,
            k,
            f_dict
        )
        return Response('检索成功', 200, data=res)
    except ValueError as error:
        return Response(f'数据错误: {error}', 400)
    except TypeError as error:
        return Response(f'参数错误: {error}', 400)

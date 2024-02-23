import json
from flask import Blueprint, request

from src.modules.response import Response
from src.controllers.wecom_controller import handle_wecom_message

wecom_blueprint = Blueprint("wecom", __name__)


@wecom_blueprint.route("/", methods=["POST"])
def wecom_application_message():
    try:
        # 接收请求中的数据
        data = request.get_json(force=True)

        # 假设handle_wechat_message是一个处理企业微信消息的函数
        # 它应该接受一个字典类型的参数，并返回处理结果
        response = handle_wecom_message(data)

        # 返回处理结果
        return Response("Message processed successfully.", 200, data=response)
    except ValueError as error:
        return Response(f"Invalid request data: {error}", 400)
    except Exception as error:
        return Response(f"Internal server error: {error}", 500)

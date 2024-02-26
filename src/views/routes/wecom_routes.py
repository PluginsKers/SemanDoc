import threading

from flask import Blueprint, request, jsonify
from webargs import fields, flaskparser
from src.modules.response import Response
from src.controllers.wecom_controller import handle_wecom_message

wecom_blueprint = Blueprint("wecom", __name__)

# 定义期望接收的参数及其类型
wecom_args = {
    "msg_signature": fields.Str(required=True),
    "timestamp": fields.Str(required=True),
    "nonce": fields.Str(required=True),
}


@wecom_blueprint.route("/", methods=["POST"])
def wecom_route():
    # 使用webargs解析查询参数
    parsed_args = flaskparser.parser.parse(
        wecom_args, request, location="querystring")

    raw_xml_data = request.data.decode('utf-8')

    # 调用处理消息的函数，传入解析的参数和XML数据
    threading.Thread(target=handle_wecom_message, args=(
        raw_xml_data,), kwargs=parsed_args).start()

    # 假设handle_wecom_message函数返回的是处理结果
    return Response("success", 200)

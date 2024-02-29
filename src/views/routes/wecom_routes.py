import asyncio
import threading
from flask import Blueprint, request
from webargs import fields, flaskparser
from src.modules.response import Response
from src.controllers.wecom_controller import handle_wecom_message

wecom_blueprint = Blueprint("wecom", __name__)

wecom_args = {
    "msg_signature": fields.Str(required=True),
    "timestamp": fields.Str(required=True),
    "nonce": fields.Str(required=True),
}


@wecom_blueprint.route("/", methods=['POST', 'OPTIONS'])
def wecom_route():
    parsed_args = flaskparser.parser.parse(
        wecom_args, request, location="querystring")
    raw_xml_data = request.data.decode('utf-8')

    threading.Thread(target=lambda: asyncio.run(
        handle_wecom_message(raw_xml_data, **parsed_args))).start()

    return Response("success", 200)

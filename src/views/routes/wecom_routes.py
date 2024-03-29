import asyncio
import threading
from flask import (
    Blueprint,
    request
)
from webargs import (
    fields,
    flaskparser
)

from src import app_manager
from src.modules import Response
from src.controllers.wecom_controllers import process_wecom_message

wecom_blueprint = Blueprint("wecom", __name__)

wecom_args = {
    "msg_signature": fields.Str(required=True),
    "timestamp": fields.Str(required=True),
    "nonce": fields.Str(required=True),
}


@wecom_blueprint.route("/", methods=['POST'])
def wecom_route():
    try:
        parsed_args = flaskparser.parser.parse(
            wecom_args, request, location="querystring")
        raw_xml_data = request.data.decode('utf-8')

        threading.Thread(target=lambda: asyncio.run(
            process_wecom_message(raw_xml_data, **parsed_args))).start()

        return Response(app_manager.RESPONSE_WECOM_DEFAULT, 200)

    except Exception as error:
        return Response(app_manager.RESPONSE_CATCH_ERROR.format(error), 400)

import asyncio
import threading

from flask import Response, request
from flask_restful import Resource, reqparse

from src import app_manager
from src.services.wecom_service import process_message


class WecomResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            'msg_signature', type=str, required=True, location='args', help="Message signature is required.")
        self.parser.add_argument(
            'timestamp', type=str, required=True, location='args', help="Timestamp is required.")
        self.parser.add_argument(
            'nonce', type=str, required=True, location='args', help="Nonce is required.")
        super().__init__()

    def get(self):
        self.parser.add_argument(
            'echostr', type=str, required=False, location='args', help="Validtion with query checking.")
        args = self.parser.parse_args()

        ret, decrypt_msg_str = app_manager.get_wecom_application().wxcpt.DecryptMsg(
            sPostData=f"<xml><Encrypt><![CDATA[{args.get('echostr')}]]></Encrypt></xml>",
            sMsgSignature=args.get("msg_signature"),
            sTimeStamp=args.get("timestamp"),
            sNonce=args.get('nonce')
        )

        if ret == 0 and decrypt_msg_str:
            try:
                return Response(decrypt_msg_str.decode('utf-8'), content_type='text/plain; charset=utf-8')
            except Exception as e:
                return {"message": "Error processing the request"}, 500
        else:
            return {"message": "Failed to decrypt message or message is empty"}, 400

    def post(self):
        args = self.parser.parse_args()
        raw_xml_data = request.data.decode('utf-8')

        # Asynchronously process the WeCom message in a non-blocking manner.
        threading.Thread(target=lambda: asyncio.run(
            process_message(raw_xml_data, **args)), daemon=True).start()

        return {'message': app_manager.RESPONSE_WECOM_DEFAULT}, 200

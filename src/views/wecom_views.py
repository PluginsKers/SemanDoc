import asyncio
import threading

from flask import request
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
        # This method could be expanded to provide actual functionality if needed.
        return {'message': app_manager.RESPONSE_WECOM_DEFAULT}, 200

    def post(self):
        args = self.parser.parse_args()
        raw_xml_data = request.data.decode('utf-8')

        # Asynchronously process the WeCom message in a non-blocking manner.
        threading.Thread(target=lambda: asyncio.run(
            process_message(raw_xml_data, **args)), daemon=True).start()

        return {'message': app_manager.RESPONSE_WECOM_DEFAULT}, 200

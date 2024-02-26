# src/controllers/wecom_controller.py

import xml.etree.ElementTree as ET
from src.modules.wecom.message import WecomMessage

from src import get_wecom_app


def handle_wecom_message(xml_str: str, **kwargs):
    app = get_wecom_app()
    xml_data = ET.fromstring(xml_str)

    kwargs.update({
        **kwargs,
        'msg_crypt': app.wxcpt
    })

    wecom_msg = WecomMessage(xml_str, **kwargs)

    if not app.is_on_cooldown(wecom_msg.get_sender()):
        app.send_message_async(wecom_msg.get_sender(), wecom_msg.get_content())

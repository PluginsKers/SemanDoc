import xml.etree.ElementTree as ET
import threading
from src.modules.logging import logger
from src.utils.wxcrypt.WXBizMsgCrypt3 import WXBizMsgCrypt


class DuplicateMessageIDError(Exception):
    """Exception for duplicate message IDs."""

    def __init__(self, msg_id):
        super().__init__(f"Duplicate message ID: {msg_id}")
        self.msg_id = msg_id


class InvalidXMLDataError(Exception):
    """Exception for invalid XML data."""

    def __init__(self, message="Invalid XML data"):
        super().__init__(message)


class WecomMessage:
    processed_ids = set()
    processed_ids_lock = threading.Lock()  # Adding thread safety

    VALID_ENCRYPT_TEMPLATE = [{"AgentID": None},
                              {"ToUserName": None}, {"Encrypt": None}]
    DECRYPTED_TEMPLATE = [{"ToUserName": None}, {"MsgType": None}, {
        "Content": None}, {"MsgId": None}, {"AgentID": None}]

    def __init__(self, raw_xml_data: str, msg_signature: str, timestamp: str, nonce: str, msg_crypt: WXBizMsgCrypt):
        self.msg_crypt = msg_crypt
        self.msg_signature = msg_signature
        self.timestamp = timestamp
        self.nonce = nonce
        self.raw_xml_data = raw_xml_data

        self._validate_and_decrypt_message()

    def _validate_and_decrypt_message(self):
        if not self._contains_keys(ET.fromstring(self.raw_xml_data), self.VALID_ENCRYPT_TEMPLATE):
            raise InvalidXMLDataError("Invalid XML data for decryption.")

        self.xml_tree = self._decrypt_msg()

        if not self._contains_keys(self.xml_tree, self.DECRYPTED_TEMPLATE):
            raise InvalidXMLDataError("Invalid XML data in decrypted message.")

        self.msg_id = self._get_msg_id()

        with self.processed_ids_lock:  # Ensuring thread safety
            if self.msg_id in self.processed_ids:
                logger.error(f"Duplicate message ID: {self.msg_id}")
                raise DuplicateMessageIDError(self.msg_id)
            self.processed_ids.add(self.msg_id)

    def _decrypt_msg(self) -> ET.Element:
        ret, decrypt_msg_str = self.msg_crypt.DecryptMsg(
            self.raw_xml_data, self.msg_signature, self.timestamp, self.nonce)
        if ret != 0:
            logger.error(
                f'Wecom message AESDecrypt error: {self.raw_xml_data}, {self.msg_signature}, {self.timestamp}, {self.nonce}')
            raise InvalidXMLDataError('Wecom message AESDecrypt error')
        return ET.fromstring(decrypt_msg_str)

    def _get_msg_id(self) -> str:
        msg_id_element = self.xml_tree.find('MsgId')
        if msg_id_element is None:
            raise InvalidXMLDataError("Message ID not found")
        return msg_id_element.text

    def _contains_keys(self, xml_data: ET.Element, keys_list: list):
        """
        判断XML是否包含所有提供的键。
        参数 keys_list 是一个包含字典的列表，每个字典代表要检查的键路径。
        例如: [{"MsgType": None}, {"Content": None}]
        返回 True 如果所有键都找到，否则 False。
        """
        for key_dict in keys_list:
            if not self._find_key_in_xml(xml_data, key_dict):
                return False
        return True

    def _find_key_in_xml(self, element, key_dict):
        """
        递归搜索指定的键是否存在于给定的XML元素中。
        """
        for key, nested_keys in key_dict.items():
            found = element.find(key)
            if found is None:
                return False
            if nested_keys is not None:
                # 如果有嵌套键，递归检查这些键
                if isinstance(nested_keys, list):
                    # 如果嵌套键是列表，则继续检查每个字典
                    for nested_key_dict in nested_keys:
                        if not self._find_key_in_xml(found, nested_key_dict):
                            return False
                else:
                    # 如果嵌套键不是列表（单个嵌套键）
                    if not self._find_key_in_xml(found, nested_keys):
                        return False
        return True

    def get_content(self) -> str:
        content_element = self.xml_tree.find("Content")
        if content_element is None:
            raise InvalidXMLDataError("Content not found")
        return content_element.text

    def get_sender(self) -> str:
        sender_element = self.xml_tree.find("FromUserName")
        if sender_element is None:
            raise InvalidXMLDataError("Sender not found")
        return sender_element.text

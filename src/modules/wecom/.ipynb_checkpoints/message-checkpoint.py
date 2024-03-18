import xml.etree.ElementTree as ET
import threading
import logging
from src.utils.wxcrypt.WXBizMsgCrypt3 import WXBizMsgCrypt

logger = logging.getLogger(__name__)


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

    valid_encrypt_template = [{"AgentID": None},
                              {"ToUserName": None}, {"Encrypt": None}]
    decrypted_template = [{"ToUserName": None}, {"MsgType": None}, {
        "Content": None}, {"MsgId": None}, {"AgentID": None}]

    def __init__(self, raw_xml_data: str, msg_signature: str, timestamp: str, nonce: str, msg_crypt: WXBizMsgCrypt):
        self.msg_crypt = msg_crypt
        self.msg_signature = msg_signature
        self.timestamp = timestamp
        self.nonce = nonce
        self.raw_xml_data = raw_xml_data

        self._validate_and_decrypt_message()

    def _validate_and_decrypt_message(self):
        if not self._contains_keys(ET.fromstring(self.raw_xml_data), self.valid_encrypt_template):
            raise InvalidXMLDataError("Invalid XML data for decryption.")

        self.xml_tree = self._decrypt_msg()

        if not self._contains_keys(self.xml_tree, self.decrypted_template):
            raise InvalidXMLDataError(
                f"Invalid XML data in decrypted message: {self.xml_tree.text}")

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
            raise InvalidXMLDataError('Wecom message AES decrypt error')
        return ET.fromstring(decrypt_msg_str)

    def _get_msg_id(self) -> str:
        msg_id_element = self.xml_tree.find('MsgId')
        if msg_id_element is None:
            raise InvalidXMLDataError("Message ID not found")
        return msg_id_element.text

    def _contains_keys(self, xml_data: ET.Element, keys_list: list):
        """
        Check if XML contains all provided keys.
        The keys_list parameter is a list of dictionaries, each representing a key path to check.
        Example: [{"MsgType": None}, {"Content": None}]
        Returns True if all keys are found, False otherwise.
        """
        for key_dict in keys_list:
            if not self._find_key_in_xml(xml_data, key_dict):
                return False
        return True

    def _find_key_in_xml(self, element, key_dict):
        """
        Recursively search for the specified key in the given XML element.
        """
        for key, nested_keys in key_dict.items():
            found = element.find(key)
            if found is None:
                return False
            if nested_keys is not None:
                # Recursively check these keys if there are nested keys
                if isinstance(nested_keys, list):
                    # Continue checking each dictionary if nested keys are a list
                    for nested_key_dict in nested_keys:
                        if not self._find_key_in_xml(found, nested_key_dict):
                            return False
                else:
                    # If there's a single nested key (not a list)
                    if not self._find_key_in_xml(found, nested_keys):
                        return False
        return True

    def get_content(self) -> str:
        content_element = self.xml_tree.find("Content")
        if content_element is None:
            raise InvalidXMLDataError("Content not found")
        return content_element.text

    def get_create_time(self) -> str:
        create_time_element = self.xml_tree.find("CreateTime")
        if create_time_element is None:
            raise InvalidXMLDataError("CreateTime not found")
        return create_time_element.text

    def get_to_user(self) -> str:
        to_user_element = self.xml_tree.find("ToUserName")
        if to_user_element is None:
            raise InvalidXMLDataError("ToUserName not found")
        return to_user_element.text

    def get_msg_type(self) -> str:
        msg_type_element = self.xml_tree.find("MsgType")
        if msg_type_element is None:
            raise InvalidXMLDataError("MsgType not found")
        return msg_type_element.text

    def get_from_user(self) -> str:
        sender_element = self.xml_tree.find("FromUserName")
        if sender_element is None:
            raise InvalidXMLDataError("Sender not found")
        return sender_element.text

    def get_agent_id(self) -> str:
        agent_id_element = self.xml_tree.find("AgentID")
        if agent_id_element is None:
            raise InvalidXMLDataError("AgentID not found")
        return agent_id_element.text

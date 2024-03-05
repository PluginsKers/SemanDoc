from src.utils.wxcrypt.WXBizMsgCrypt3 import WXBizMsgCrypt
import time
from typing import Dict, List
import logging
import requests
import threading

from collections import deque


logger = logging.getLogger(__name__)


class TokenUpdateError(Exception):
    """Exception raised when an error occurs during the access token update process."""

    def __init__(self, error_message=""):
        super().__init__(f"Access token update failed: {error_message}")


class SendMessageError(Exception):
    """Exception raised for errors in the message sending process."""

    def __init__(self):
        super().__init__("An error occurred while sending the message.")


class HistoryRecords:
    def __init__(self, max_length=3):
        self.records = deque(maxlen=max_length)

    def add_record(self, question, answer):
        if not isinstance(question, str) or not isinstance(answer, str):
            raise ValueError("Both question and answer must be strings.")
        self.records.append([question, answer])

    def get_records(self) -> List[str]:
        return list(self.records)

    def get_raw_records(self) -> str:
        raw = ""
        for i, record in enumerate(self.records):
            raw += f"> 用户：{record[0]}\n> 助手：{record[1]}\n"

        return raw


class WeComApplication:
    API_URL = "https://qyapi.weixin.qq.com/cgi-bin/"
    TOKEN_URL = f"{API_URL}gettoken"

    COOLDOWN_TIME = 30

    def __init__(self, agent_id, corp_id, corp_secret, encoding_aes_key, stoken):
        self.cooldowns = {}
        self.historys: Dict[str, HistoryRecords] = {}

        self.agent_id = agent_id
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self.encoding_aes_key = encoding_aes_key
        self.stoken = stoken

        self.wxcpt = WXBizMsgCrypt(
            self.stoken, self.encoding_aes_key, self.corp_id)

        self.access_token = None
        self.token_expiration = 0
        logger.info(
            "WeCom application initialized for agent_id: %s", self.agent_id)

    async def send_message_async(self, user_id: str, content: str, question: str = None):
        # If the HistoryRecords object does not exist
        if user_id not in self.historys:
            self.historys[user_id] = HistoryRecords()

        try:
            self.set_cooldown(user_id, WeComApplication.COOLDOWN_TIME)
            self.update_access_token()
        except Exception as e:
            logger.exception(
                "Error setting cooldown or updating access token.")

        def send_message():
            send_url = f"{self.API_URL}message/send?access_token={self.access_token}"
            data = {
                "touser": user_id,
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {
                    "content": content
                },
                "safe": 0
            }
            try:
                response = requests.post(send_url, json=data)
                response.raise_for_status()  # Raises an HTTPError for bad responses
                result = response.json()

                if result.get("errcode") != 0:
                    logger.error("Failed to send message: %s",
                                 result.get("errmsg"))
                    raise SendMessageError(result.get("errmsg"))

                if question:
                    # Add record after successful message send
                    self.historys[user_id].add_record(question, content)
            except requests.exceptions.RequestException as e:
                logger.exception(
                    "Network error occurred while sending message.")
            except SendMessageError as e:
                logger.error(str(e))
            except Exception as e:
                logger.exception(
                    "Unexpected exception occurred while sending message.")
            finally:
                # Ensure cooldown is always canceled
                self.cancel_cooldown(user_id)

        thread = threading.Thread(target=send_message)
        thread.start()

    def update_access_token(self):
        if time.time() >= self.token_expiration:
            logger.info(
                "Updating WeCom access token for agent_id: %s", self.agent_id)
            params = {
                'corpid': self.corp_id,
                'corpsecret': self.corp_secret
            }
            try:
                response = requests.get(self.TOKEN_URL, params=params)
                response.raise_for_status()  # Raises HTTPError for bad responses
                data = response.json()

                if data.get('errcode') == 0:
                    self.access_token = data['access_token']
                    # Set expiration time to refresh 5 minutes before actual expiration
                    self.token_expiration = time.time() + \
                        data['expires_in'] - 300
                    logger.info("WeCom access token updated successfully for agent_id: %s. Token expires in %d seconds.",
                                self.agent_id, data['expires_in'])
                else:
                    error_message = data.get('errmsg', 'Unknown error')
                    logger.error(
                        "Failed to get WeCom access token for agent_id: %s. Error: %s", self.agent_id, error_message)
                    raise TokenUpdateError(error_message)

            except requests.exceptions.RequestException as e:
                logger.error(
                    "Network error occurred while updating WeCom access token for agent_id: %s.", self.agent_id)
                raise TokenUpdateError(
                    "Network error during token update") from e
            except Exception as e:
                logger.exception(
                    "Unexpected exception occurred while updating WeCom access token for agent_id: %s.", self.agent_id)
                raise TokenUpdateError(
                    "Unexpected error during token update") from e

    def is_on_cooldown(self, user_id: str) -> bool:
        """
        Check if user_id is in a cooling state.
        """
        current_time = time.time()
        if user_id in self.cooldowns and current_time < self.cooldowns[user_id]:
            return True
        return False

    def cancel_cooldown(self, user_id: str):
        """
        Cancel the cooling status of the specified user.
        """
        if user_id in self.cooldowns:
            del self.cooldowns[user_id]

    def set_cooldown(self, user_id: str, cooldown_seconds: int):
        """
        Set cooling time for specified users.
        """
        cooldown_end = time.time() + cooldown_seconds
        # Update dict
        self.cooldowns[user_id] = cooldown_end

from collections import deque
import time
from typing import Dict, List
import logging
import requests
import threading

from src.config import BaseConfig as cfg

from src.utils.wxcrypt.WXBizMsgCrypt3 import WXBizMsgCrypt

logger = logging.getLogger(__name__)


class DepartmentRetrievalError(Exception):
    def __init__(self, error_code, error_message):
        self.error_code = error_code
        self.error_message = error_message
        super().__init__(f"Error {error_code}: {error_message}")

    def __str__(self):
        return f"[{self.error_code}] {self.error_message}"


class TokenUpdateError(Exception):
    """Exception raised when an error occurs during the access token update process."""

    def __init__(self, error_message=""):
        super().__init__(f"Access token update failed: {error_message}")


class SendMessageError(Exception):
    """Exception raised for errors in the message sending process."""

    def __init__(self, error_message=""):
        super().__init__(f"Sending the message failed: {error_message}")


class HistoryRecords:
    def __init__(self, max_length=1):
        self.history = deque(maxlen=max_length)
        # Set the initial time as the current time
        self.time = time.time()

    def add_record(self, msg: str, answer: str):
        # Check if more than 3 hours have passed
        if time.time() - self.time > 10800:  # 3 hours in seconds
            self.clear_history()  # Clear history if more than 3 hours
        if not isinstance(msg, str) or not isinstance(answer, str):
            raise ValueError("Both question and answer must be strings.")
        self.history.append({"role": "user", "content": msg})
        self.history.append(
            {"role": "assistant", "metadata": "", "content": answer})
        # Update the time using time.time()
        self.time = time.time()

    def get_history(self) -> List[dict]:
        # Check if more than 3 hours have passed
        if time.time() - self.time > 10800:
            return []  # Return an empty list if more than 3 hours
        return list(self.history)

    def get_raw_history(self) -> str:
        raw = ""
        for record in self.history:
            raw += f"{record['role']}: {record['content']}\n"
        return raw

    def clear_history(self):
        # Clear the history
        self.history.clear()


class WeComApplication:
    API_URL = "https://qyapi.weixin.qq.com/cgi-bin/"
    DEPARTMENT_LIST_URL = f"{API_URL}department/list"
    SEND_MESSAGE_URL = f"{API_URL}message/send"
    USER_INFO_URL = f"{API_URL}user/get"
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

    async def send_message_async(self, user_id: str, content: str, message: str = None, on_ai: bool = False):
        # If the HistoryRecords object does not exist
        if user_id not in self.historys:
            self.historys[user_id] = HistoryRecords()

        try:
            self.update_access_token()
        except Exception as e:
            logger.exception(
                "Error updating access token.")

        try:
            self.set_cooldown(user_id, WeComApplication.COOLDOWN_TIME)
        except Exception as e:
            logger.exception(
                "Error setting cooldown.")

        def send_message():
            send_url = f"{self.SEND_MESSAGE_URL}?access_token={self.access_token}"
            send_message = content
            if on_ai:
                send_message += "\n" + cfg.GEN_AI_TIP
            data = {
                "touser": user_id,
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {
                    "content": send_message
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

                if message:
                    # Add record after successful message send
                    self.historys[user_id].add_record(message, content)
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

    def get_user_info(self, userid: str) -> dict:
        try:
            self.update_access_token()
        except Exception as e:
            logger.exception(
                "Error updating access token.")

        response = requests.get(self.USER_INFO_URL, params={
            'access_token': self.access_token,
            'userid': userid
        })
        response.raise_for_status()  # Raises an HTTPError for bad responses
        result = response.json()

        if result.get('errcode') == 0:
            return result
        else:
            raise DepartmentRetrievalError(
                result.get('errcode'), result.get('errmsg'))

    def get_dep_name(self, userid: str) -> str:
        user_info = self.get_user_info(userid)
        user_department = user_info.get('main_department')
        response = requests.get(self.DEPARTMENT_LIST_URL, params={
            'access_token': self.access_token,
            'id': 8  # Main Department ID
        })
        response.raise_for_status()  # Raises an HTTPError for bad responses
        result = response.json()

        if result.get('errcode') == 0 and result.get('department'):
            def find_parent_until_top(departments, dep_id):
                current_id = dep_id
                current_dep = None

                while current_id is not None:
                    # 查找当前部门
                    current_dep = next(
                        (dep for dep in departments if dep["id"] == current_id), None)

                    # 如果找不到部门或者父部门ID为8，则结束循环
                    if current_dep is None or current_dep["parentid"] == 8:
                        break

                    # 更新current_id为父部门ID以继续向上追溯
                    current_id = current_dep["parentid"]

                return current_dep

            deps: list = result['department']
            return find_parent_until_top(deps, user_department)['name']
        else:
            raise DepartmentRetrievalError(
                result.get('errcode'), result.get('errmsg'))

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

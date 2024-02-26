import time
from typing import Dict, List
import requests

import threading

from collections import deque

from src.modules.logging import logger
from src.utils.wxcrypt.WXBizMsgCrypt3 import WXBizMsgCrypt


class HistoryRecords:
    def __init__(self, max_length=3):
        self.records = deque(maxlen=max_length)

    def add_record(self, question, answer):
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

    def send_message_async(self, user_id: str, content: str, question: str):
        # If the HistoryRecords object does not exist
        if user_id not in self.historys:
            self.historys[user_id] = HistoryRecords()

        self.set_cooldown(user_id, WeComApplication.COOLDOWN_TIME)
        self.update_access_token()

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
                result = response.json()
                if result.get("errcode") != 0:
                    logger.error("Failed to send message: %s",
                                 result.get("errmsg"))

                self.historys[user_id].add_record(question, content)

                self.cancel_cooldown(user_id)
            except Exception as e:
                logger.exception("Exception occurred while sending message.")

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
                data = response.json()
                if data.get('errcode') == 0:
                    self.access_token = data['access_token']
                    # Set expiration time to refresh 5 minutes in advance
                    self.token_expiration = time.time() + \
                        data['expires_in'] - 300
                    logger.info("WeCom access token updated successfully for agent_id: %s. Token expires in %d seconds.",
                                self.agent_id, data['expires_in'])
                else:
                    logger.error(
                        "Failed to get WeCom access token for agent_id: %s. Error: %s", self.agent_id, data.get('errmsg'))
                    raise Exception(
                        f"Failed to get access token: {data.get('errmsg')}")
            except Exception as e:
                logger.exception(
                    "Exception occurred while updating WeCom access token for agent_id: %s.", self.agent_id)
                raise e

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

import json
import logging
from flask import Response as _Response

logger = logging.getLogger(__name__)


class Response(_Response):
    def __init__(
        self,
        msg=None,
        code=None,
        headers=None,
        data=None,
        content_type: str = "application/json",
        **kwargs
    ):

        if isinstance(msg, dict):
            msg = json.dumps(msg)

        if code is None:
            code = 404

        response = {"code": code, "msg": msg}
        if data is not None:
            if isinstance(data, (dict, list)):
                response["data"] = data
            else:
                try:
                    logger.info("尝试转化输出格式")
                    tmp_data = data
                    tmp_data = json.loads(tmp_data)
                    data = tmp_data
                except json.JSONDecodeError:
                    logger.warn("响应转化格式失败")
                response["data"] = json.dumps(data, ensure_ascii=False)

        super().__init__(
            json.dumps(response, ensure_ascii=False),
            response['code'],
            headers,
            content_type,
            **kwargs
        )

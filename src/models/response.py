import logging
import json
from typing import Tuple
from flask import Response as _Response


class Response:
    def __init__(self, *kwargs: Tuple[str]):
        self.code = None
        self.msg = '\n'.join(kwargs)
        self.logger = self.setup_logger()

    def setup_logger(self):
        """
        Sets up the logging configuration.
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def set_code(self, code: int):
        """
        Set the return code
        """
        self.code = code

    def set_msg(self, msg: str):
        """
        Set the return message
        """
        self.msg = msg

    def print(self) -> _Response:
        """
        Print the configured response
        """
        # Perform a check for missing code before printing
        if self.code is None:
            self.code = 400

        raw_dict = {
            "code": self.code,
            "msg": self.msg
        }
        return _Response(
            json.dumps(raw_dict, ensure_ascii=False),
            status=self.code,
            mimetype='application/json'
        )

    def success(self) -> _Response:
        """
        Success response
        """
        self.set_code(200)
        return self.print()

    def error(self, code: int = 400) -> _Response:
        """
        Error response
        """
        self.set_code(code)
        return self.print()

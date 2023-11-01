import json
import logging

from src.models.embedding_model import EmbeddingModelManager
from src.models.tag import TagManager


class Knowledge:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata
        self.logger = self.setup_logger()

    def setup_logger(self):
        # 设置日志记录
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def to_dict(self):
        data = {
            "page_content": self.page_content,
            "metadata": {
                "id": self.metadata.get("id"),
                "splitter": self.metadata.get("splitter"),
                "model": self.metadata.get("model"),
                "tag": self.metadata.get("tag"),
                "related": self.metadata.get("related"),
                "start_time": self.metadata.get("start_time"),
                "valid_time": self.metadata.get("valid_time")
            }
        }
        return data

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_csv(self):
        return ",".join([
            self.metadata.get("id"),
            self.metadata.get("splitter"),
            self.metadata.get("model"),
            self.metadata.get("tag"),
            self.metadata.get("related"),
            self.metadata.get("start_time"),
            self.metadata.get("valid_time"),
            self.page_content
        ])

    @staticmethod
    def create_new_knowledge(
        splitter="default",
        start_time: int = 0,
        valid_time: int = 3600
    ):
        metadata = {
            "id": id,
            "splitter": splitter,
            "model_manager": EmbeddingModelManager([]),
            "tag_manager": TagManager([]),
            "related": False,
            "start_time": start_time,
            "valid_time": valid_time
        }
        return Knowledge("", metadata)

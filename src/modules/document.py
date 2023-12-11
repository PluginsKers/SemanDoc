from typing import List

import time
from typing import List, Optional, Dict, Any


class Metadata:
    def __init__(
        self,
        ids: Optional[int] = None,
        splitter: str = 'default',
        valid_time: Optional[int] = None,
        start_time: Optional[int] = None,
        related: bool = False,
        tags: list = None
    ):
        self.ids = ids
        self.splitter = splitter
        self.related = related
        self.valid_time = valid_time if valid_time is not None else -1
        self.start_time = start_time if start_time is not None else time.time()
        self.tags = tags if tags is not None else []

    def to_dict(self):
        return {
            'ids': self.ids,
            'splitter': self.splitter,
            'valid_time': self.valid_time,
            'related': self.related,
            'start_time': self.start_time,
            'tags': self.tags
        }


class Document:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        if metadata is None:
            self.metadata = Metadata()
        elif isinstance(metadata, dict):
            self.metadata = Metadata(**metadata)
        elif isinstance(metadata, Metadata):
            self.metadata = metadata
        else:
            raise ValueError("Invalid metadata format provided.")

        self.metadata = self.metadata.to_dict()

    def to_dict(self):
        return {
            'page_content': self.page_content,
            'metadata': self.metadata
        }

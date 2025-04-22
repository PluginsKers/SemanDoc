from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Callable
import time
import uuid


@dataclass
class Metadata:
    ids: str | None = None
    valid_time: int = -1
    start_time: float | None = None
    tags: List[Any] = field(default_factory=list)
    categories: List[Any] = field(default_factory=list)

    _is_valid: Optional[bool] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.ids is None:
            self.ids = str(uuid.uuid4())
        if self.start_time is None:
            self.start_time = time.time()

    @property
    def is_valid(self) -> bool:
        if self._is_valid is None:
            self._is_valid = (
                True
                if self.valid_time == -1
                else (self.start_time + self.valid_time) >= time.time()
            )
        return self._is_valid

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ids": self.ids,
            "valid_time": self.valid_time,
            "start_time": self.start_time,
            "tags": self.tags,
            "categories": self.categories,
        }

    def __iter__(self):
        yield from self.to_dict().items()


@dataclass
class MetadataFilter:
    ids: Optional[List[str]] = None
    tags: Optional[List[Any]] = None
    categories: Optional[List[Any]] = None
    custom_filter: Optional[Callable[[Metadata], bool]] = None

    def match(self, metadata: Metadata) -> bool:
        if self.ids is not None and metadata.ids not in self.ids:
            return False

        if self.tags is not None and len(self.tags) > 0:
            if not any(tag in metadata.tags for tag in self.tags):
                return False

        if self.categories is not None and len(self.categories) > 0:
            if not any(cat in metadata.categories for cat in self.categories):
                return False

        if self.custom_filter is not None and not self.custom_filter(metadata):
            return False

        return True


@dataclass
class Document:
    content: str
    metadata: Union[Metadata, Dict[str, Any], None] = None
    _is_valid: Optional[bool] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.content:
            raise ValueError("Document content cannot be empty")
        if isinstance(self.metadata, dict):
            self.metadata = Metadata(**self.metadata)
        elif self.metadata is None:
            self.metadata = Metadata()

    @property
    def is_valid(self) -> bool:
        if self._is_valid is None:
            self._is_valid = self.metadata.is_valid
        return self._is_valid

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "metadata": self.metadata.to_dict(),
        }

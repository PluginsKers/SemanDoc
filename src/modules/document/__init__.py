import time
from typing import List, Optional, Union


class Tags:
    def __init__(self, tags: Optional[List[str]] = None):
        self.tags = tags if tags is not None else []

    def add_tag(self, tag: str):
        """Adds a new tag to the tags list if it's not already present."""
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        """Removes a tag from the tags list if it exists."""
        if tag in self.tags:
            self.tags.remove(tag)

    def has_tag(self, tag: str) -> bool:
        """Checks if a tag is present in the tags list."""
        return tag in self.tags

    def get_tags(self) -> List[str]:
        """Returns the list of tags."""
        return self.tags

    def get_powerset(self) -> List[List[str]]:
        result = [[]]
        for i in range(len(self.tags)):
            tag = self.tags[i]
            new_subsets = [subset + [tag] for subset in result]
            result.extend(new_subsets)
        return result

    def get_combinations(self) -> List[List[str]]:
        result = []
        for i in range(len(self.tags) - 1):  # Iterate until the second-to-last element
            # Start from the next element to avoid duplicates
            for j in range(i + 1, len(self.tags)):
                result.append([self.tags[i], self.tags[j]])
        return result


class Metadata:
    def __init__(
        self,
        ids: Optional[int] = None,
        splitter: str = "default",
        valid_time: Optional[int] = None,
        start_time: Optional[int] = None,
        related: bool = False,
        tags: Optional[List[str]] = None,
    ):
        self.ids = ids
        self.splitter = splitter
        self.related = related
        self.valid_time = valid_time if valid_time is not None else -1
        self.start_time = start_time if start_time is not None else time.time()
        self.tags = Tags(tags)

    def to_filter(self, powerset: bool = True) -> Optional[dict]:
        ret = {
            "tags": self.tags.get_powerset() if powerset else self.tags.get_combinations()
        }
        if len(self.tags.get_tags()) == 0:
            ret = None
        return ret

    def to_dict(self) -> dict:
        return {
            "ids": self.ids,
            "splitter": self.splitter,
            "valid_time": self.valid_time,
            "related": self.related,
            "start_time": self.start_time,
            "tags": self.tags.get_tags(),
        }


class Document:
    def __init__(self, page_content: str, metadata: Union[dict, Metadata] = None):
        self.page_content = page_content
        if metadata is None:
            self.metadata = Metadata()
        elif isinstance(metadata, dict):
            self.metadata = Metadata(**metadata)
        elif isinstance(metadata, Metadata):
            self.metadata = metadata
        else:
            raise ValueError("Invalid metadata format provided.")

        # Ensure the metadata stored in the document is in dictionary format
        self.metadata = self.metadata.to_dict()

    def to_dict(self):
        return {"page_content": self.page_content, "metadata": self.metadata}

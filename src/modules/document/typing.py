import time

import uuid
import hashlib
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Union
)


def uuid_to_sha256(uuid_str: str) -> str:
    """
    Converts a UUID string into a SHA-256 hash.

    Args:
    - uuid_str (str): A valid UUID string.

    Returns:
    Str: A hexadecimal string representing the SHA-256 hash of the UUID.

    Raises:
    ValueError: If the input string is not a valid UUID.
    """
    try:
        # This ensures the UUID is valid; if not, it raises a ValueError.
        uuid_obj = uuid.UUID(uuid_str)
    except ValueError:
        raise ValueError(f"Invalid UUID string: '{uuid_str}'")

    # Convert UUID to bytes, considering the hyphens.
    uuid_bytes = uuid_obj.bytes
    sha256_hash = hashlib.sha256(uuid_bytes).hexdigest()
    return sha256_hash


class Tags:
    """
    A class to manage a collection of unique tags.

    Attributes:
    tags (List[str]): A list of tags associated with an instance.
    """

    def __init__(self, tags: Optional[List[str]] = None):
        """
        Initializes the Tags object with an optional list of tags.

        Args:
        - tags (Optional[List[str]]): An initial list of tags. Defaults to None.
        """
        self.tags: Set[str] = set(tags) if tags is not None else set()

    def add_tag(self, tag: str):
        """
        Adds a new tag to the tags set if it's not already present.

        Args:
        - tag (str): The tag to add.
        """
        self.tags.add(tag)

    def remove_tag(self, tag: str):
        """
        Removes a tag from the tags set if it exists.

        Args:
        - tag (str): The tag to remove.
        """
        self.tags.discard(
            tag)  # Using discard to avoid KeyError if tag doesn't exist

    def has_tag(self, tag: str) -> bool:
        """
        Checks if a tag is present in the tags set.

        Args:
        - tag (str): The tag to check for.

        Returns:
        Bool: True if the tag is present, False otherwise.
        """
        return tag in self.tags

    def get_tags(self) -> List[str]:
        """
        Returns the list of tags.

        Returns:
        List[str]: A list of tags.
        """
        return list(self.tags)

    def get_powerset(self) -> List[List[str]]:
        """
        Generates the powerset of the tags set.

        Returns:
        List[List[str]]: A list of lists, where each sublist is a combination
        of tags representing a subset of the powerset.
        """
        # Converting the set to a list to support indexing
        tags_list = list(self.tags)
        result = [[]]
        for tag in tags_list:
            new_subsets = [subset + [tag] for subset in result]
            result.extend(new_subsets)
        return result

    def get_combinations(self) -> List[List[str]]:
        """
        Generates all unique combinations of two tags from the tags set.

        Returns:
        List[List[str]]: A list of lists, where each sublist is a combination of two tags.
        """
        tags_list = list(self.tags)
        result = []
        for i in range(len(tags_list) - 1):
            for j in range(i + 1, len(tags_list)):
                result.append([tags_list[i], tags_list[j]])
        return result


class Metadata:
    """
    Represents metadata associated with a document, including IDs, tags, and temporal information.

    Attributes:
    - ids (str): Unique identifier for the metadata, generated from a SHA-256 hash.
    - splitter (str): A string used to split or differentiate metadata, default is 'default'.
    - related (bool): Indicates if the metadata is related to another entity.
    - valid_time (int): Duration in seconds for which the metadata is considered valid.
    - start_time (int): Timestamp marking the start of the metadata's validity.
    - tags (Tags): A `Tags` object containing tags associated with the metadata.
    """

    def __init__(
        self,
        ids: Optional[str] = None,
        splitter: str = "default",
        valid_time: Optional[int] = None,
        start_time: Optional[int] = None,
        related: bool = False,
        tags: Optional[List[str]] = None,
    ):
        self.ids = ids if ids is not None else uuid_to_sha256(
            str(uuid.uuid4()))
        self.splitter = splitter
        self.related = related
        self.valid_time = valid_time if valid_time is not None else -1
        self.start_time = start_time if start_time is not None else time.time()
        self.tags = Tags(tags)

    def get_ids(self) -> str:
        """
        Retrieves the unique identifier of the metadata.

        Returns:
            str: The unique identifier.
        """
        return self.ids

    def to_filter(self, powerset: bool = True) -> Optional[Dict[str, Any]]:
        """
        Converts the metadata to a filter format, based on its tags.

        Args:
        - powerset (bool): If True, generates filters based on the powerset of tags; otherwise, uses tag combinations.

        Returns:
        Optional[Dict[str, Any]]: A dictionary representing the filter criteria, or None if no tags are defined.
        """
        tags_filter = self.tags.get_powerset() if powerset else self.tags.get_combinations()
        if not self.tags.get_tags():
            return None
        return {"tags": tags_filter}

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the metadata into a dictionary format.

        Returns:
        Dict[str, Any]: A dictionary representation of the metadata.
        """
        return {
            "ids": self.ids,
            "splitter": self.splitter,
            "valid_time": self.valid_time,
            "related": self.related,
            "start_time": self.start_time,
            "tags": self.tags.get_tags(),
        }


class Document:
    """
    Represents a document with content and associated metadata.

    Attributes:
    - page_content (str): The content of the document.
    - metadata (Metadata): The metadata associated with the document.
    """

    def __init__(self, page_content: str, metadata: Union[Dict[str, Any], Metadata] = None):
        self.page_content = page_content
        if isinstance(metadata, dict):
            self.metadata = Metadata(**metadata)
        elif isinstance(metadata, Metadata):
            self.metadata = metadata
        else:
            self.metadata = Metadata()

    def is_valid(self) -> bool:
        """
        Determines if the document is still valid based on its metadata's validity period.

        Returns:
        bool: True if the document is valid, False otherwise.
        """
        current_time = time.time()
        # Handle the case where valid_time is indefinite (-1).
        if self.metadata.valid_time == -1:
            return True

        return (self.metadata.start_time + self.metadata.valid_time) >= current_time

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the document into a dictionary format, including its content and metadata.

        Returns:
        Dict[str, Any]: A dictionary representation of the document.
        """
        return {"page_content": self.page_content, "metadata": self.metadata.to_dict()}

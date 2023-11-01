from typing import List
import logging


class TagManager:
    """
    Tag Manager class for managing a list of tags.
    """

    def __init__(self, tag_list: List[str] = []):
        """
        Initialize the TagManager with an optional list of tags.
        """
        self.tag_list = tag_list  # Fixed the parameter name
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

    def add_tag(self, tag):
        """
        Add a tag to the tag list.
        """

    def remove_tag_by_id(self, id: int):
        """
        Remove a tag from the list by its ID.
        """

    def get_tag_by_id(self, id: int):
        """
        Get a tag by its ID.
        """

    def get_tags(self):
        """
        Get all tags in the list.
        """

    def get_tags_by_name(self, name: str):
        """
        Get all tags with a specific name.
        """

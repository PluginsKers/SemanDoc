import json
import logging
from typing import Optional
from flask import Response as FlaskResponse

logger = logging.getLogger(__name__)


class Response(FlaskResponse):
    def __init__(
        self,
        message: Optional[str],
        status_code: Optional[int],
        data: Optional[dict] = None,
        headers=None,
        content_type: str = "application/json",
        **kwargs
    ):
        # Serialize message if it's a dictionary
        if isinstance(message, dict):
            message = json.dumps(message)

        # Set default status code if not provided
        if status_code is None:
            status_code = 404

        # Prepare the response dictionary
        response_dict = {"code": status_code, "msg": message}

        # Include data in the response if provided
        if data is not None:
            if isinstance(data, (dict, list)):
                response_dict["data"] = data
            else:
                # Attempt to parse the data as JSON
                try:
                    logger.info("Attempting to format output")
                    formatted_data = json.loads(data)
                    response_dict["data"] = formatted_data
                except json.JSONDecodeError:
                    logger.warning("Failed to format response")
                    response_dict["data"] = json.dumps(
                        data, ensure_ascii=False)

        # Initialize the parent Flask Response with the formatted JSON response
        super().__init__(
            json.dumps(response_dict, ensure_ascii=False),
            response_dict['code'],
            headers,
            content_type,
            **kwargs
        )


class StringProcessor:
    def __init__(self):
        logger.info("StringProcessor initialized")

    def replace_char_by_list(self, input_str: str, replace_char: list):
        """
        Replace characters in the input string based on the given list of replacements.

        Args:
            input_str (str): The input string.
            replace_char (list): List of tuples containing pairs of characters to be replaced.

        Returns:
            str: The modified input string after replacements.
        """
        for pair in replace_char:
            input_str = input_str.replace(pair[0], pair[1])
        return input_str

    def split_by_punctuation(self, input_str: str):
        """
        Split the input string into sentences based on punctuation marks.

        Args:
            input_str (str): The input string.

        Returns:
            list: A list of sentences extracted from the input string.
        """
        punctuation = ".!?。！？"
        sentences = []
        current_sentence = ""

        for char in input_str:
            if char not in punctuation:
                current_sentence += char
            else:
                # Remove leading and trailing spaces
                current_sentence = current_sentence.strip()
                if current_sentence:
                    sentences.append(current_sentence)
                current_sentence = ""

        if current_sentence:
            current_sentence = current_sentence.strip()
            sentences.append(current_sentence)

        return sentences


processor = StringProcessor()

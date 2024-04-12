import logging
from typing import List

logger = logging.getLogger(__name__)


class StringProcessor:
    def __init__(self):
        logger.info("StringProcessor initialized")

    def replace_char_by_list(self, input_str: str, replace_char: list) -> str:
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

    def split_by_punctuation(self, input_str: str) -> List[str]:
        """
        Split the input string into sentences based on punctuation marks.

        Args:
            input_str (str): The input string.

        Returns:
            List[str]: A list of sentences extracted from the input string.
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

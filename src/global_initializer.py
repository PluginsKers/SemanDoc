from typing import Optional
from src.modules.docstore import DocStore
from src.modules.logging import logger

import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()


# Global variable to store the initialized database
docstore: Optional[DocStore] = None


def initialize():
    """
    Initializes the global database variable if it is not already initialized.
    """
    global docstore
    if not docstore:
        logger.info("Loading knowledge base...")

        # Read paths from environment variables
        index_path = os.getenv("INDEX_PATH")
        model_path = os.getenv("MODEL_PATH")

        # Initialize the DocStore with the paths from the environment variables
        docstore = DocStore(index_path, model_path)

        logger.info("Knowledge base loaded!")


def get_docstore() -> DocStore:
    """
    Returns the initialized DocStore instance.

    Returns:
        DocStore: The initialized DocStore instance.
    """
    return docstore

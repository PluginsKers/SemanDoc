from typing import Optional
from src.modules.document_store import DocumentStore
from src.modules.logging import logger

import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()


# Global variable to store the initialized database
docstore: Optional[DocumentStore] = None


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

        # Initialize the DocumentStore with the paths from the environment variables
        docstore = DocumentStore(index_path, model_path)

        logger.info("Knowledge base loaded!")


def get_docstore() -> DocumentStore:
    """
    Returns the initialized DocumentStore instance.

    Returns:
        DocumentStore: The initialized DocumentStore instance.
    """
    return docstore

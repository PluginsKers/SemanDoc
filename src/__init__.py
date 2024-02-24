from typing import Optional
from src.modules.document_store import DocumentStore
from src.modules.wecom import WeComApplication
from src.modules.logging import logger

import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Global variable to store the initialized database instance. Initially set to None.
docstore: Optional[DocumentStore] = None

# Global variable to store the initialized WeCom application instance. Initially set to None.
wecom_app: Optional[WeComApplication] = None


def initialize():
    """
    Initializes the global variables for document store and WeCom application if they are not already initialized.
    Utilizes environment variables for configuration paths and credentials.
    """
    global docstore
    if not docstore:
        logger.info("Loading knowledge base...")

        # Initialize the DocumentStore with paths from environment variables
        docstore = DocumentStore(
            os.getenv("INDEX_PATH"), os.getenv("MODEL_PATH"))

        logger.info("Knowledge base loaded!")

    global wecom_app
    if not wecom_app:
        logger.info("Initializing WeCom application...")

        # Initialize the WeComApplication with credentials from environment variables
        wecom_app = WeComApplication(
            os.getenv("AGENT_ID"), os.getenv(
                "CORP_ID"), os.getenv("CORP_SECRET"),
            os.getenv("ENCODING_AES_KEY"), os.getenv("TOKEN"))

        logger.info("WeCom application initialized!")


def get_wecom_app() -> WeComApplication:
    """
    Returns the initialized WeComApplication instance

    Returns:
        WeComApplication: The initialized WeComApplication instance.
    """
    return wecom_app


def get_docstore() -> DocumentStore:
    """
    Returns the initialized DocumentStore instance.

    Returns:
        DocumentStore: The initialized DocumentStore instance.
    """
    return docstore

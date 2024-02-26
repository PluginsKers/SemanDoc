from typing import Optional

import torch

from src.modules.database import Database
from src.modules.document.vecstore import DocumentStore
from src.modules.llm.llm_model import LLMModel
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

# Global variable to store the language large model instance. Initially set to None.
db: Optional[Database] = None

# desc
llm: Optional[LLMModel] = None


def initialize():
    """
    Initializes the global variables for document store and WeCom application if they are not already initialized.
    Utilizes environment variables for configuration paths and credentials.
    """
    global llm
    if not llm:
        logger.info("Initializing llm model...")

        # Initialize the LLM Model with paths from environment variables
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        llm = LLMModel(device,
                       os.getenv("LLM_MODEL_PATH"))

        logger.info("llm model initialized!")

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

    global db
    if not db:
        logger.info("Initializing Database...")

        # Initialize the Database with the path from environment variables
        db = Database(
            os.getenv("DB_PATH"))

        logger.info("Database initialized!")


def get_llm() -> LLMModel:
    """
    Returns the initialized LLMModel instance.

    Returns:
        LLMModel: The initialized LLMModel instance.
    """
    return llm


def get_db() -> Database:
    """
    Returns the initialized Database instance.

    Returns:
        Database: The initialized Database instance.
    """
    assert db is not None, "Database must be initialized before accessing it."
    return db


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

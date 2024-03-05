from typing import Optional

import torch
import logging


from src.modules.database import Database
from src.modules.document.reranker import Reranker
from src.modules.document.vecstore import VectorStore
from src.modules.llm import LLMModel
from src.modules.wecom import WeComApplication

import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    '[%(levelname)s] %(asctime)s - %(name)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


load_dotenv()

# Global variable to store the initialized database instance. Initially set to None.
docstore: Optional[VectorStore] = None

# Global variable to store the initialized WeCom application instance. Initially set to None.
wecom_app: Optional[WeComApplication] = None

# Global variable to store the language large model instance. Initially set to None.
database: Optional[Database] = None

llm: Optional[LLMModel] = None

reranker: Optional[Reranker] = None


def initialize():
    """
    Initializes the global variables for document store and WeCom application if they are not already initialized.
    Utilizes environment variables for configuration paths and credentials.
    """
    global docstore
    if not docstore:
        logger.info("Loading Documents VectorStore...")

        docstore = VectorStore(
            os.getenv("INDEX_PATH"), os.getenv("MODEL_PATH"))

        logger.info("Documents VectorStore loaded!")

    global wecom_app
    if not wecom_app:
        logger.info("Initializing WeCom Application...")

        wecom_app = WeComApplication(
            os.getenv("AGENT_ID"), os.getenv(
                "CORP_ID"), os.getenv("CORP_SECRET"),
            os.getenv("ENCODING_AES_KEY"), os.getenv("TOKEN"))

        logger.info("WeCom Application initialized!")

    global database
    if not database:
        logger.info("Initializing Database...")

        database = Database(
            os.getenv("DB_PATH"))

        logger.info("Database initialized!")

    global llm
    if not llm:
        logger.info("Initializing LLM Model... %s",
                    os.getenv("LLM_MODEL_PATH"))

        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        llm = LLMModel(
            os.getenv("LLM_MODEL_PATH"), device)

        logger.info("LLM Model initialized on device %s", device)

    global reranker
    if not reranker:
        logger.info("Initializing Reranker Model... %s",
                    os.getenv("RERANKER_MODEL_PATH"))

        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        reranker = Reranker(
            os.getenv("RERANKER_MODEL_PATH"), device)

        logger.info("Reranker Model initialized on device %s", device)


def get_reranker() -> Reranker:
    return reranker


def get_llm() -> LLMModel:
    return llm


def get_database() -> Database:
    assert database is not None, "Database must be initialized before accessing it."
    return database


def get_wecom_app() -> WeComApplication:
    return wecom_app


def get_docstore() -> VectorStore:
    return docstore

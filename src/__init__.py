from typing import Optional
import torch
import logging
import os
from dotenv import load_dotenv

from src.modules.database import Database
from src.modules.models import Reranker
from src.modules.document.vectorstore import VectorStore
from src.modules.models import LLMModel
from src.modules.wecom import WeComApplication

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '[%(levelname)s] %(asctime)s - %(name)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Load environment variables
load_dotenv()

# Global variables for storing instances, initially set to None
vector_store: Optional[VectorStore] = None
wecom_application: Optional[WeComApplication] = None
database_instance: Optional[Database] = None
llm_model: Optional[LLMModel] = None
reranker_model: Optional[Reranker] = None


def initialize():
    """
    Initializes global instances for the document vector store, WeCom application,
    database, LLM model, and reranker model if they are not already initialized,
    using environment variables for configuration.
    """
    global vector_store
    if not vector_store:
        logger.info("Loading Documents VectorStore...")
        vector_store = VectorStore(
            os.getenv("INDEX_PATH"), os.getenv("MODEL_PATH"))
        logger.info("Documents VectorStore loaded!")

    global wecom_application
    if not wecom_application:
        logger.info("Initializing WeCom Application...")
        wecom_application = WeComApplication(
            os.getenv("AGENT_ID"), os.getenv(
                "CORP_ID"), os.getenv("CORP_SECRET"),
            os.getenv("ENCODING_AES_KEY"), os.getenv("TOKEN"))
        logger.info("WeCom Application initialized!")

    global database_instance
    if not database_instance:
        logger.info("Initializing Database...")
        database_instance = Database(os.getenv("DB_PATH"))
        logger.info("Database initialized!")

    global llm_model
    if not llm_model:
        logger.info("Initializing LLM Model... %s",
                    os.getenv("LLM_MODEL_PATH"))
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        llm_model = LLMModel(os.getenv("LLM_MODEL_PATH"), device)
        logger.info("LLM Model initialized on device %s.", device)

    global reranker_model
    if not reranker_model:
        logger.info("Initializing Reranker Model... %s",
                    os.getenv("RERANKER_MODEL_PATH"))
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        reranker_model = Reranker(os.getenv("RERANKER_MODEL_PATH"), device)
        logger.info("Reranker Model initialized on device %s.", device)


def get_reranker() -> Reranker:
    """Returns the reranker model instance."""
    return reranker_model


def get_llm_model() -> LLMModel:
    """Returns the LLM model instance."""
    return llm_model


def get_database_instance() -> Database:
    """Returns the database instance, ensuring it's initialized."""
    assert database_instance is not None, "Database must be initialized before accessing it."
    return database_instance


def get_wecom_application() -> WeComApplication:
    """Returns the WeCom application instance."""
    return wecom_application


def get_vector_store() -> VectorStore:
    """Returns the document vector store instance."""
    return vector_store

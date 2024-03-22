from typing import Optional
import torch

import logging

from src.config import BaseConfig as cfg
from src.modules.database import Database
from src.modules.models import Reranker
from src.modules.document.vectorstore import VectorStore
from src.modules.models import LLMModel
from src.modules.wecom import WeComApplication

logger = logging.getLogger(__name__)

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
        vector_store = VectorStore(cfg.INDEX_PATH, cfg.MODEL_PATH)
        logger.info("Documents VectorStore loaded!")

    global wecom_application
    if not wecom_application:
        logger.info("Initializing WeCom Application...")
        wecom_application = WeComApplication(
            cfg.AGENT_ID,
            cfg.CORP_ID,
            cfg.CORP_SECRET,
            cfg.ENCODING_AES_KEY,
            cfg.TOKEN
        )
        logger.info("WeCom Application initialized!")

    global database_instance
    if not database_instance:
        logger.info("Initializing Database...")
        database_instance = Database(cfg.DB_PATH)
        logger.info("Database initialized!")

    global llm_model
    if not llm_model:
        logger.info("Initializing LLM Model... %s", cfg.LLM_MODEL_PATH)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        llm_model = LLMModel(cfg.LLM_MODEL_PATH, device)
        logger.info("LLM Model initialized on device %s.", device)

    global reranker_model
    if not reranker_model:
        logger.info("Initializing Reranker Model... %s",
                    cfg.RERANKER_MODEL_PATH)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        reranker_model = Reranker(cfg.RERANKER_MODEL_PATH, device)
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

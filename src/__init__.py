
import os
import torch
import logging
from flask import g
from functools import wraps
from typing import Optional

from config import BaseConfig
from src.modules.database import Database
from src.modules.models import Reranker, LLMModel
from src.modules.document.vectorstore import VectorStore
from src.modules.wecom import WeComApplication


def include_user_id(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in kwargs:
            kwargs['user_id'] = g.user_id
        return func(*args, **kwargs)
    return wrapper


class ApplicationManager(BaseConfig):
    def __init__(self):
        super(BaseConfig).__init__()
        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '[%(levelname)s] %(asctime)s - %(name)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        # Initialize instances
        self.vector_store = None
        self.wecom_application = None
        self.database_instance = None
        self.llm_model = None
        self.reranker_model = None
        self.initialize()

    def initialize(self):
        """Initializes instances for various components."""
        if not self.vector_store:
            self.logger.info("Loading Documents VectorStore...")
            self.vector_store = VectorStore(
                self.INDEX_PATH,
                self.MODEL_PATH,
                self.EMBEDDING_QUERY_INSTRUCTION,
                self.device
            )
            self.logger.info("Documents VectorStore loaded!")

        wecom_required_config_attrs = [
            'AGENT_ID', 'TOKEN', 'ENCODING_AES_KEY', 'CORP_ID', 'CORP_SECRET']

        # Check if all required configuration attributes are present
        if all(hasattr(self, attr) for attr in wecom_required_config_attrs):
            if not self.wecom_application:
                self.logger.info("Initializing WeCom Application...")
                self.wecom_application = WeComApplication(
                    agent_id=self.AGENT_ID,
                    corp_id=self.CORP_ID,
                    corp_secret=self.CORP_SECRET,
                    encoding_aes_key=self.ENCODING_AES_KEY,
                    stoken=self.TOKEN,
                    ai_generated_notice=self.WECOM_AI_GENERATED_NOTICE
                )
                self.logger.info("WeCom Application initialized!")
        else:
            # Identify which required attributes are missing
            missing_attrs = [
                attr for attr in wecom_required_config_attrs if not hasattr(self, attr)]
            missing_attrs_str = ', '.join(missing_attrs)
            self.logger.info(
                f"Cannot initialize WeCom Application: Missing configuration items - {missing_attrs_str}.")

        if not self.database_instance:
            self.logger.info("Initializing Database...")
            self.database_instance = Database(self.DB_PATH)
            self.logger.info("Database initialized!")

        if not self.reranker_model:
            self.logger.info(
                "Initializing Reranker Model... %s",
                self.RERANKER_MODEL_PATH
            )
            self.reranker_model = Reranker(
                self.RERANKER_MODEL_PATH, self.device)
            self.logger.info(
                "Reranker Model initialized on device %s.",
                self.device
            )

        if hasattr(self, 'LLM_MODEL_PATH') and os.path.exists(self.LLM_MODEL_PATH):
            if not self.llm_model:
                self.logger.info(
                    "Initializing LLM Model... %s", self.LLM_MODEL_PATH)
                self.llm_model = LLMModel(
                    model_name=self.LLM_MODEL_PATH,
                    device=self.device
                )
                self.logger.info(
                    "LLM Model initialized on device %s.", self.device)
        else:
            # Log a message if LLM_MODEL_PATH is not set or the path does not exist
            if not hasattr(self, 'LLM_MODEL_PATH'):
                missing_attr = "LLM_MODEL_PATH not set."
            elif not os.path.exists(self.LLM_MODEL_PATH):
                missing_attr = f"Path does not exist: {self.LLM_MODEL_PATH}"
            else:
                missing_attr = "Unknown error."

            self.logger.info(f"Cannot initialize LLM Model: {missing_attr}")

    def get_reranker(self) -> Optional[Reranker]:
        """Returns the reranker model instance."""
        return self.reranker_model

    def get_llm_model(self) -> Optional[LLMModel]:
        """Returns the LLM model instance."""
        return self.llm_model

    def get_database_instance(self) -> Optional[Database]:
        """Returns the database instance, ensuring it's initialized."""
        assert self.database_instance is not None, "Database must be initialized before accessing it."
        return self.database_instance

    def get_wecom_application(self) -> Optional[WeComApplication]:
        """Returns the WeCom application instance."""
        return self.wecom_application

    def get_vector_store(self) -> Optional[VectorStore]:
        """Returns the document vector store instance."""
        return self.vector_store


app_manager = ApplicationManager()

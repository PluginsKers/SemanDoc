import logging
from typing import Any, Dict, List, Optional, Tuple

from src.services.document_service import find_and_optimize_documents
from src import app_manager
from src.modules.document import (
    Document
)
from src.modules.database import Document as Docdb
from src.modules.database.user import User, Role


logger = logging.getLogger(__name__)


user_db = User(app_manager.get_database_instance())
doc_db = Docdb(app_manager.get_database_instance())
role_db = Role(app_manager.get_database_instance())


def build_history(reranked_documents: List[Document]) -> List[Dict[str, str]]:
    if reranked_documents:
        document_texts = "".join(
            doc.page_content for doc in reranked_documents)
        system_prompt = app_manager.LLM_SYSTEM_PROMPT.format(document_texts)
    else:
        system_prompt = app_manager.LLM_SYSTEM_PROMPT.format(
            app_manager.LLM_SYSTEM_PROMPT_FILLNON)

    _history = [{"role": "system", "content": system_prompt}]
    return _history


def chat(query: str, dep_name: str = None) -> Tuple[bool, Optional[str]]:
    if not app_manager.LLM_MODEL_PATH:
        return False, app_manager.RESPONSE_LLM_MODEL_PATH_NOT_FOUND

    docs = find_and_optimize_documents(query, [dep_name])
    if docs:
        history = build_history(docs)
        model = app_manager.get_llm_model()
        response = model.get_response(
            query, app_manager.LLM_CHAT_PROMPT, history)
        return True, response

    return False, None

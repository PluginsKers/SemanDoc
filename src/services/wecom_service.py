import logging
from typing import Any, Dict, List, Optional, Tuple


from src import app_manager
from src.services.document_service import find_and_optimize_documents
from src.modules.models.llm import LLMModel
from src.modules.document import Document
from src.modules.wecom import (
    HistoryRecords,
    WecomMessage,
    WeComApplication
)

logger = logging.getLogger(__name__)


async def process_message(wecom_message_xml: str, **kwargs) -> None:
    sender_id = None
    llm_model, wecom_app = initialize_app_components()
    try:
        kwargs.update({'msg_crypt': wecom_app.wxcpt})
        sender_id, user_msg_content, user_msg_type = extract_message_info(
            wecom_message_xml, **kwargs)

        if not should_process_message(wecom_app, sender_id, user_msg_type):
            return

        wecom_app.set_cooldown(sender_id, wecom_app.COOLDOWN_TIME)
        predicted_tags = detect_user_intent(user_msg_content, llm_model)

        search_params = build_search_params(
            sender_id, user_msg_content, predicted_tags)
        documents = find_and_optimize_documents(**search_params)

        history = build_history(wecom_app.historys.get(sender_id), documents)
        response = llm_model.get_response(
            user_msg_content, app_manager.LLM_CHAT_PROMPT, history)

        await wecom_app.send_message_async(sender_id, response, user_msg_content, len(documents) < 1)
    except Exception as e:
        await handle_exception(e, sender_id, wecom_app)


def initialize_app_components() -> Tuple[LLMModel, WeComApplication]:
    llm_model = app_manager.get_llm_model()
    wecom_app = app_manager.get_wecom_application()

    if not llm_model:
        raise ValueError("LLM Model is not initialized.")

    return llm_model, wecom_app


def should_process_message(
    wecom_app: WeComApplication,
    sender_id: str,
    user_msg_type: str
) -> bool:
    if wecom_app.is_on_cooldown(sender_id) or user_msg_type != "text":
        return False
    return True


def build_search_params(
    sender_id: str,
    content: str,
    tags: List[str] = []
) -> Dict[str, Any]:
    wecom_app = app_manager.get_wecom_application()
    tags.append(wecom_app.get_dep_name(sender_id))
    return {"query": content, "tags": tags}


def build_history(
    records: HistoryRecords,
    reranked_documents: List[Document]
) -> List[Dict[str, str]]:
    system_prompt = app_manager.LLM_SYSTEM_PROMPT.format(
        "".join(doc.page_content for doc in reranked_documents) if reranked_documents else app_manager.LLM_SYSTEM_PROMPT_FILLNON
    )

    _history = [{"role": "system", "content": system_prompt}]
    if records:
        _history.extend(records.get_history())
    return _history


def extract_message_info(wecom_message_xml: str, **kwargs) -> Tuple[str, str, str]:
    wecom_message = WecomMessage(wecom_message_xml, **kwargs)
    return wecom_message.get_from_user(), wecom_message.get_content(), wecom_message.get_msg_type()


def detect_user_intent(user_msg_content: str, llm: LLMModel) -> Optional[List[str]]:

    # TODO: Modular user expectation classifier.

    try:
        intents = llm.predict_intent(
            user_msg_content,
            app_manager.GLM_TOOLS_PROMPT
        )
        if isinstance(intents, str):
            return [intents]
        elif isinstance(intents, list) and all(isinstance(intent, str) for intent in intents):
            return intents
        else:
            raise ValueError(
                f"Unexpected type for intents: {type(intents)} with value: {intents}")
    except Exception as e:
        logger.exception("Failed to determine intent with LLM: %s", e)

    return []


async def handle_exception(
    exception: Exception,
    sender_id: Optional[str],
    wecom_app: WeComApplication
) -> None:
    logger.exception("Failed to process WeCom message: %s", str(exception))
    if sender_id:
        await wecom_app.send_message_async(
            sender_id, app_manager.WECOM_APP_ERROR_MESSAGE)

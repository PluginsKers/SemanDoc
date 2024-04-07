import logging
from typing import Any, Dict, List, Optional, Tuple


from src import app_manager
from src.modules.models.llm import LLMModel
from src.services.document_service import find_and_optimize_documents
from src.modules.document import Document
from src.modules.wecom import (
    HistoryRecords,
    WecomMessage
)

logger = logging.getLogger(__name__)


async def process_message(wecom_message_xml: str, **kwargs) -> None:
    sender_id = None
    try:
        llm_model = app_manager.get_llm_model()
        wecom_app = app_manager.get_wecom_application()

        if not llm_model:
            raise ValueError("LLM Model is not initialized.")

        kwargs.update({'msg_crypt': wecom_app.wxcpt})
        sender_id, user_msg_content, user_msg_type = extract_message_info(
            wecom_message_xml, **kwargs)

        if wecom_app.is_on_cooldown(sender_id) or user_msg_type != "text":
            return

        wecom_app.set_cooldown(sender_id, wecom_app.COOLDOWN_TIME)
        predicted_tags = determine_intent(user_msg_content, llm_model)

        search_params = build_search_params(
            sender_id, user_msg_content, predicted_tags)
        documents = find_and_optimize_documents(**search_params)

        history = build_history(wecom_app.historys.get(sender_id), documents)
        response = llm_model.get_response(
            user_msg_content, app_manager.LLM_CHAT_PROMPT, history)

        await wecom_app.send_message_async(sender_id, response, user_msg_content, len(documents) < 1)
    except Exception as e:
        logger.exception("Failed to process WeCom message: %s", str(e))
        if sender_id:
            await wecom_app.send_message_async(sender_id, app_manager.WECOM_APP_ERROR_MESSAGE)


def build_search_params(sender_id: str, content: str, tags: List[str] = []) -> Dict[str, Any]:
    wecom_app = app_manager.get_wecom_application()
    tags.append(wecom_app.get_dep_name(sender_id))
    return {"query": content, "tags": tags}


def build_history(records: HistoryRecords, reranked_documents: List[Document]) -> List[Dict[str, str]]:
    if reranked_documents:
        document_texts = "".join(
            doc.page_content for doc in reranked_documents)
        system_prompt = app_manager.LLM_SYSTEM_PROMPT.format(document_texts)
    else:
        system_prompt = app_manager.LLM_SYSTEM_PROMPT.format(
            app_manager.LLM_SYSTEM_PROMPT_FILLNON)

    _history = [{"role": "system", "content": system_prompt}]

    if records:
        _history.extend(records.get_history())
    return _history


def extract_message_info(wecom_message_xml: str, **kwargs) -> Tuple[str, str, str]:
    wecom_message = WecomMessage(wecom_message_xml, **kwargs)
    return wecom_message.get_from_user(), wecom_message.get_content(), wecom_message.get_msg_type()


def determine_intent(user_msg_content: str, llm: LLMModel) -> Optional[List[str]]:

    # TODO: Modular user expectation classifier.

    keyword_to_intent = {
        '问路': '位置信息',
        '联系方式': '联系方式'
    }

    # Attempt to find a direct keyword match for quick intent determination
    for keyword, intent in keyword_to_intent.items():
        if keyword in user_msg_content:
            return [intent]

    try:
        predicted_intent = llm.predict_intent(
            user_msg_content,
            app_manager.LLM_CHAT_PROMPT,
            app_manager.GLM_TOOLS
        )
        if predicted_intent in keyword_to_intent.keys():
            return [keyword_to_intent[predicted_intent]]
        else:
            logger.info("LLM predicted an unknown intent: %s",
                        predicted_intent)
    except Exception as e:
        logger.exception("Failed to determine intent with LLM: %s", e)

    return []

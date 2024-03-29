import logging
from typing import List


from src import app_manager
from src.controllers import find_and_optimize_documents
from src.modules.document import Document
from src.modules.wecom import (
    HistoryRecords,
    WecomMessage
)

logger = logging.getLogger(__name__)


def extract_message_info(wecom_message_xml: str, **kwargs):
    wecom_message = WecomMessage(wecom_message_xml, **kwargs)
    return wecom_message.get_from_user(), wecom_message.get_content(), wecom_message.get_msg_type()


async def process_wecom_message(wecom_message_xml: str, **kwargs) -> None:
    sender_id = None  # Define outside try for scope in exception handling
    on_ai = False
    try:
        llm = app_manager.get_llm_model()
        if not llm:
            raise Exception("LLM Model is not initialized.")

        wecom_app = app_manager.get_wecom_application()

        kwargs.update({'msg_crypt': wecom_app.wxcpt})
        sender_id, user_msg_content, user_msg_type = extract_message_info(
            wecom_message_xml, **kwargs)

        if wecom_app.is_on_cooldown(sender_id) or user_msg_type != "text":
            return

        wecom_app.set_cooldown(sender_id, wecom_app.COOLDOWN_TIME)

        _params = {
            "dep_name": wecom_app.get_dep_name(sender_id),
            "query_text": user_msg_content
        }

        intent_mapping = {
            '问路': '位置信息',
            '联系方式': '联系方式'
        }

        predicted_intent = llm.get_response_by_tools(
            user_msg_content,
            app_manager.LLM_CHAT_PROMPT,
            app_manager.GLM_TOOLS
        )
        if isinstance(predicted_intent, dict) and predicted_intent.get('name') == 'classify':
            parameters = predicted_intent.get('parameters', {})
            symbol = parameters.get('symbol')
            if symbol in intent_mapping:
                _params.update({"intent_type": intent_mapping[symbol]})

        _documents = []
        _documents = find_and_optimize_documents(**_params)

        # Process message content
        history_record = wecom_app.historys.get(sender_id)

        # Generate response based on the history and the current message
        history = build_history(history_record, _documents)
        response = llm.get_response(
            user_msg_content,
            app_manager.LLM_CHAT_PROMPT,
            history
        )

        if len(_documents) < 1:
            on_ai = True

        await wecom_app.send_message_async(sender_id, response, user_msg_content, on_ai)
    except Exception as e:
        logger.exception(e)
        if sender_id:
            await wecom_app.send_message_async(sender_id, app_manager.WECOM_APP_ERROR_MESSAGE)


def build_history(records, reranked_documents: List[Document]):
    document_texts = "".join(doc.page_content for doc in reranked_documents)
    system_prompt = app_manager.LLM_SYSTEM_PROMPT.format(document_texts)

    if len(reranked_documents) < 1:
        app_manager.LLM_SYSTEM_PROMPT.format(
            app_manager.LLM_SYSTEM_PROMPT_FILLNON)
    _history = [{"role": "system", "content": system_prompt}]

    if records and isinstance(records, HistoryRecords):
        _history.extend(records.get_history())
    return _history

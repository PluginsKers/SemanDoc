import logging
from src import get_wecom_application, get_llm_model, get_vector_store, get_reranker
from src.modules.wecom import HistoryRecords
from src.modules.wecom.message import WecomMessage

logger = logging.getLogger(__name__)


def extract_message_info(wecom_message_xml: str, **kwargs):
    wecom_message = WecomMessage(wecom_message_xml, **kwargs)
    sender_id = wecom_message.get_from_user()
    message_content = wecom_message.get_content()
    message_type = wecom_message.get_msg_type()
    return sender_id, message_content, message_type


async def process_wecom_message(wecom_message_xml: str, **kwargs) -> None:
    sender_id = None  # Initial definition to ensure scope availability for error handling
    try:
        wecom_app = get_wecom_application()

        kwargs.update({
            'msg_crypt': wecom_app.wxcpt
        })

        sender_id, message_content, message_type = extract_message_info(
            wecom_message_xml, **kwargs)

        if not wecom_app.is_on_cooldown(sender_id) and message_type == "text":
            wecom_app.set_cooldown(sender_id, wecom_app.COOLDOWN_TIME)
            language_model = get_llm_model()
            document_reranker = get_reranker()
            initial_documents = await get_vector_store().query(query=message_content, k=4)
            reranked_documents = document_reranker.rerank_documents(
                initial_documents, message_content)
            document_texts = "- " + \
                "\n- ".join(doc.page_content for doc in reranked_documents)

            records = wecom_app.historys.get(sender_id)
            history = records.get_raw_records() if records and isinstance(
                records, HistoryRecords) else []
            if history:
                summary_prompt = language_model.prompt_manager.get_summarize(
                    history)
                summary = language_model.generate(summary_prompt)
                history = [{"role": "user", "content": "总结一下上面我们聊了什么？"},
                           {"role": "assistant", "metadata": "", "content": summary}]

            optimization_prompt = language_model.prompt_manager.get_optimize(
                document_texts, message_content)
            response = language_model.generate(optimization_prompt, history)

            await wecom_app.send_message_async(sender_id, response, message_content)
    except Exception as e:

        logger.exception(e)
        if sender_id:
            error_response = "处理信息时出现问题，请稍后重试。"
            await wecom_app.send_message_async(sender_id, error_response)

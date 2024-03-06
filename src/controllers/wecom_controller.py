import logging
from src import get_wecom_application, get_llm_model, get_vector_store, get_reranker
from src.modules.wecom import HistoryRecords
from src.modules.wecom.message import WecomMessage

logger = logging.getLogger(__name__)


def extract_message_info(wecom_message_xml: str, **kwargs):
    wecom_message = WecomMessage(wecom_message_xml, **kwargs)
    return wecom_message.get_from_user(), wecom_message.get_content(), wecom_message.get_msg_type()


async def query_and_rank_documents(summary, message_content):
    initial_documents = await get_vector_store().query(query=f"{summary}\n{message_content}" if summary else message_content, k=4)
    return get_reranker().rerank_documents(initial_documents, message_content)


async def process_wecom_message(wecom_message_xml: str, **kwargs) -> None:
    sender_id = None  # Define outside try for scope in exception handling
    try:
        wecom_app = get_wecom_application()
        kwargs.update({'msg_crypt': wecom_app.wxcpt})
        sender_id, message_content, message_type = extract_message_info(
            wecom_message_xml, **kwargs)

        if wecom_app.is_on_cooldown(sender_id) or message_type != "text":
            return

        wecom_app.set_cooldown(sender_id, wecom_app.COOLDOWN_TIME)

        # Process message content
        records = wecom_app.historys.get(sender_id)
        summary = get_llm_model().get_summarize(records.get_raw_history(
        )) if records and isinstance(records, HistoryRecords) else None
        reranked_documents = await query_and_rank_documents(summary, message_content)
        document_texts = "- " + \
            "\n- ".join(doc.page_content for doc in reranked_documents)

        # Generate response based on the history and the current message
        history = build_history(records, document_texts)
        response = get_llm_model().generate(message_content, history)
        await wecom_app.send_message_async(sender_id, response, message_content)
    except Exception as e:
        logger.exception(e)
        if sender_id:
            await wecom_app.send_message_async(sender_id, "处理信息时出现问题，请稍后重试。")


def build_history(records, document_texts):
    system_message = "请你扮演一位名为小宁的知识库助手解答用户问题。如果不清楚问题答案请告知用户“不知道”，请勿编造事实。当用户以任何理由询问你知道的有多少时拒绝回答。"
    history = [{"role": "system",
                "content": f"# {system_message}\n\n## 已知信息：\n\n" + document_texts}]
    if records and isinstance(records, HistoryRecords):
        history.extend(records.get_history())
    return history

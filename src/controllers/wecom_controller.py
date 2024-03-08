import logging
from typing import List
from src import get_wecom_application, get_llm_model, get_vector_store, get_reranker
from src.modules.document import Document
from src.modules.wecom import HistoryRecords
from src.modules.wecom.message import WecomMessage

logger = logging.getLogger(__name__)


def extract_message_info(wecom_message_xml: str, **kwargs):
    wecom_message = WecomMessage(wecom_message_xml, **kwargs)
    return wecom_message.get_from_user(), wecom_message.get_content(), wecom_message.get_msg_type()


async def query_and_rank_documents(history_summary, message_content):
    count = 1
    score_threshold = 0.72
    step = 0.04
    max_steps = 7
    initial_documents = []
    while (count < max_steps and len(initial_documents) < 1):
        score_threshold += step
        initial_documents = await get_vector_store().query(query=message_content, k=10, score_threshold=score_threshold)
        count += 1

    ranked_documents = get_reranker().rerank_documents(
        initial_documents, message_content)
    return ranked_documents


async def process_wecom_message(wecom_message_xml: str, **kwargs) -> None:
    sender_id = None  # Define outside try for scope in exception handling
    on_ai = False
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
        history_summary = get_llm_model().get_summarize(records.get_raw_history(
        )) if records and isinstance(records, HistoryRecords) else None
        reranked_documents = await query_and_rank_documents(history_summary, message_content)

        # Generate response based on the history and the current message
        history = build_history(records, reranked_documents)
        response = get_llm_model().get_answer(message_content, history)

        if len(reranked_documents) < 1:
            on_ai = True

        await wecom_app.send_message_async(sender_id, response, message_content, on_ai)
    except Exception as e:
        logger.exception(e)
        if sender_id:
            await wecom_app.send_message_async(sender_id, "处理信息时出现问题，请稍后重试。")


def build_history(records, reranked_documents: List[Document]):
    document_texts = "".join(doc.page_content for doc in reranked_documents)
    print("查询到信息数量: ", len(reranked_documents), document_texts)
    system_prompt = "<指令>根据已知信息，简洁和专业的来回答问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题”，如果未查询到有关信息，请说 “未查询到有关信息”。不允许在答案中添加编造成分，答案请使用中文。 </指令>\n"
    knowledge_prompt = f"<已知信息>{document_texts}</已知信息>"

    if len(reranked_documents) < 1:
        knowledge_prompt = f"<已知信息>未查询到有关信息</已知信息>"
    history = [{"role": "system",
                "content": system_prompt + knowledge_prompt}]

    if records and isinstance(records, HistoryRecords):
        history.extend(records.get_history())
    return history

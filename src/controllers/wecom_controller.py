import logging
from typing import List
from src import get_wecom_application, get_llm_model, get_vector_store, get_reranker
from src.modules.document import Document, Metadata
from src.modules.wecom import HistoryRecords
from src.modules.wecom.message import WecomMessage

logger = logging.getLogger(__name__)


def extract_message_info(wecom_message_xml: str, **kwargs):
    wecom_message = WecomMessage(wecom_message_xml, **kwargs)
    return wecom_message.get_from_user(), wecom_message.get_content(), wecom_message.get_msg_type()


async def find_and_optimize_documents(dep_name: str, query_text: str, intent_type: str = None):
    """
    Finds and optimizes documents based on the query text and department name.
    Allows specification of document type for more targeted searches.

    Args:
    dep_name (str): The department name to use as a search context.
    query_text (str): The text query to search for relevant documents.
    intent_type (str): Type of intent. Default is None.

    Returns:
    List[Document]: A list of optimized and relevant documents.
    """
    attempt_limit = 10
    min_documents_required = 1
    initial_score_threshold = 0.6
    score_adjustment_step = 0.05
    max_score_threshold = initial_score_threshold + \
        (score_adjustment_step * attempt_limit)

    metadata = Metadata()

    metadata.tags.add_tag(dep_name)
    metadata.tags.add_tag('通用')

    if intent_type is not None:
        metadata.tags.add_tag(intent_type)

    found_documents = []
    current_attempt = 0
    score_threshold = initial_score_threshold

    # Dynamically adjust score threshold to find at least the minimum required documents
    while current_attempt < attempt_limit and len(found_documents) < min_documents_required:
        found_documents = await get_vector_store().query(query=query_text, filter=metadata, k=10, score_threshold=score_threshold, use_powerset=True if intent_type is None else False)
        score_threshold = min(
            score_threshold + score_adjustment_step, max_score_threshold)
        current_attempt += 1

    # Rerank the found documents based on additional criteria, if needed
    optimized_documents = get_reranker().rerank_documents(found_documents, query_text)

    return optimized_documents


async def process_wecom_message(wecom_message_xml: str, **kwargs) -> None:
    sender_id = None  # Define outside try for scope in exception handling
    on_ai = False
    try:
        wecom_app = get_wecom_application()
        kwargs.update({'msg_crypt': wecom_app.wxcpt})
        sender_id, user_msg_content, user_msg_type = extract_message_info(
            wecom_message_xml, **kwargs)

        if wecom_app.is_on_cooldown(sender_id) or user_msg_type != "text":
            return

        llm_model = get_llm_model()

        wecom_app.set_cooldown(sender_id, wecom_app.COOLDOWN_TIME)

        _documents = []

        predicted_intent = llm_model.get_response_by_tools(user_msg_content)

        _params = {"dep_name": wecom_app.get_dep_name(
            sender_id), "query_text": user_msg_content}

        if isinstance(predicted_intent, dict):
            if predicted_intent.get('name') == 'classify':
                parameters = predicted_intent.get('parameters')
                if isinstance(parameters, dict):
                    if parameters.get('symbol') == '问路':
                        _params.update({"intent_type": "位置信息"})
                    elif parameters.get('symbol') == '联系方式':
                        _params.update({"intent_type": "联系方式"})
                    else:
                        pass

        _documents = await find_and_optimize_documents(**_params)

        # Process message content
        history_record = wecom_app.historys.get(sender_id)
        # history_summary = llm_model.get_summarize(history_record.get_raw_history(
        # )) if history_record and isinstance(history_record, HistoryRecords) else None

        # Generate response based on the history and the current message
        history = build_history(history_record, _documents)
        response = llm_model.get_response(user_msg_content, history)

        if len(_documents) < 1:
            on_ai = True

        await wecom_app.send_message_async(sender_id, response, user_msg_content, on_ai)
    except Exception as e:
        logger.exception(e)
        if sender_id:
            await wecom_app.send_message_async(sender_id, "处理信息时出现问题，请稍后重试。")


def build_history(records, reranked_documents: List[Document]):
    document_texts = "".join(doc.page_content for doc in reranked_documents)
    system_prompt = "<指令>根据已知信息，简洁和专业的来回答问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题”，如果未查询到有关信息，请说 “未查询到有关信息”。不允许在答案中添加编造成分，答案请使用中文。 </指令>\n"
    knowledge_prompt = f"<已知信息>{document_texts}</已知信息>"

    if len(reranked_documents) < 1:
        knowledge_prompt = f"<已知信息>未查询到有关信息</已知信息>"
    history = [{"role": "system",
                "content": system_prompt + knowledge_prompt}]

    if records and isinstance(records, HistoryRecords):
        history.extend(records.get_history())
    return history

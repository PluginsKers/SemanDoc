from typing import Optional, List, Dict, Any

from src.config import Config as cfg
from src import get_vector_store, get_reranker, get_llm_model
from src.modules.document import Document, Metadata


async def find_and_optimize_documents(query: str, dep_name: str = None,  intent_type: str = None) -> List[Document]:
    """
    Finds and optimizes documents based on the query text and department name.
    Allows specification of document type for more targeted searches.

    Args:
    dep_name (str): The department name to use as a search context.
    query (str): The text query to search for relevant documents.
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
    metadata.tags.add_tag('通用')

    if dep_name is not None:
        metadata.tags.add_tag(dep_name)

    if intent_type is not None:
        metadata.tags.add_tag(intent_type)

    found_documents = []
    current_attempt = 0
    score_threshold = initial_score_threshold

    # Dynamically adjust score threshold to find at least the minimum required documents
    while current_attempt < attempt_limit and len(found_documents) < min_documents_required:
        found_documents = await get_vector_store().query(query=query, filter=metadata, k=10, score_threshold=score_threshold, use_powerset=True if intent_type is None else False)
        score_threshold = min(
            score_threshold + score_adjustment_step, max_score_threshold)
        current_attempt += 1

    # Rerank the found documents based on additional criteria, if needed
    optimized_documents = get_reranker().rerank_documents(found_documents, query)

    return optimized_documents


async def get_documents(
    query_str: str, k: int = 5, metadata: Optional[Dict[str, Any]] = None, score_threshold: Optional[float] = 1
) -> List[dict]:
    """
    Searches for documents based on the provided query.

    Args:
        query_str (str): The search query.
        k (int, optional): The number of results to retrieve. Defaults to 5.
        metadata (Optional[Dict[str, Any]], optional): Additional metadata for
        filtering. Defaults to None.

    Returns:
        List[dict]: A list of dictionaries representing the search results.
    """
    if score_threshold:
        pass

    # Perform the document search using the global document store
    initial_documents = await get_vector_store().query(query=query_str, k=k, filter=Metadata(**metadata), score_threshold=score_threshold, use_powerset=True)

    reranker = get_reranker()
    reranked_documents = reranker.rerank_documents(
        initial_documents, query_str)

    # Convert the search results to a list of dictionaries
    return [v.to_dict() for v in reranked_documents]


async def chat_with_kb(message: str, dep_name: str = None) -> str:
    _documents = await find_and_optimize_documents(message, dep_name=dep_name)

    _model = get_llm_model()
    history = build_history(_documents)
    response = _model.get_response(message, history)
    return response


def build_history(reranked_documents: List[Document]):
    document_texts = "".join(doc.page_content for doc in reranked_documents)
    system_prompt = cfg.LLM_SYSTEM_PROMPT.format(document_texts)

    if len(reranked_documents) < 1:
        cfg.LLM_SYSTEM_PROMPT.format(cfg.LLM_SYSTEM_PROMPT_FILLNON)
    _history = [{"role": "system", "content": system_prompt}]

    return _history

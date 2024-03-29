from typing import List

from src import app_manager
from src.modules.document import (
    Document,
    Metadata
)


def find_and_optimize_documents(query_text: str, dep_name: str = None,  intent_type: str = None) -> List[Document]:
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
    if app_manager.DEFAULT_TAGS:
        for tag in app_manager.DEFAULT_TAGS:
            metadata.tags.add_tag(tag)

    if dep_name is not None:
        metadata.tags.add_tag(dep_name)

    if intent_type is not None:
        metadata.tags.add_tag(intent_type)

    found_documents = []
    current_attempt = 0
    score_threshold = initial_score_threshold

    # Dynamically adjust score threshold to find at least the minimum required documents
    while current_attempt < attempt_limit and len(found_documents) < min_documents_required:
        found_documents = app_manager.get_vector_store().search(
            query_text=query_text,
            filter=metadata,
            k=10,
            score_threshold=score_threshold,
            powerset=True if intent_type is None else False
        )

        score_threshold = min(
            score_threshold + score_adjustment_step, max_score_threshold)
        current_attempt += 1

    # Rerank the found documents based on additional criteria, if needed
    optimized_documents = app_manager.get_reranker(
    ).rerank_documents(found_documents, query_text)

    return optimized_documents

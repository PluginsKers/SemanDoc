from typing import Optional, List, Dict, Any
from src import get_vector_store, get_reranker
from src.modules.document import Metadata


async def query_documents(
    query: str, k: int = 5, metadata: Optional[Dict[str, Any]] = None, score_threshold: Optional[float] = 1
) -> List[dict]:
    """
    Searches for documents based on the provided query.

    Args:
        query (str): The search query.
        k (int, optional): The number of results to retrieve. Defaults to 5.
        metadata (Optional[Dict[str, Any]], optional): Additional metadata for
        filtering. Defaults to None.

    Returns:
        List[dict]: A list of dictionaries representing the search results.
    """
    if score_threshold:
        pass

    # Perform the document search using the global document store
    initial_documents = await get_vector_store().query(query=query, k=k, filter=Metadata(**metadata), score_threshold=score_threshold, use_powerset=True)

    reranker = get_reranker()
    reranked_documents = reranker.rerank_documents(initial_documents, query)

    # Convert the search results to a list of dictionaries
    return [v.to_dict() for v in reranked_documents]

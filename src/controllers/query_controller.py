from typing import Optional, List, Dict, Any
from src import get_docstore


async def query_documents(
    query: str, k: int = 5, metadata: Optional[Dict[str, Any]] = None
) -> List[Dict]:
    """
    Searches for documents based on the provided query.

    Args:
        query (str): The search query.
        k (int, optional): The number of results to retrieve. Defaults to 5.
        metadata (Optional[Dict[str, Any]], optional): Additional metadata for
        filtering. Defaults to None.

    Returns:
        List[Dict]: A list of dictionaries representing the search results.
    """
    # Perform the document search using the global document store
    query_result = await get_docstore().search(query=query, k=k, metadata=metadata)

    # Convert the search results to a list of dictionaries
    return [v.to_dict() for v in query_result]

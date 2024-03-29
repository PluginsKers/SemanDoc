from typing import (
    Optional,
    List,
    Dict,
    Any
)

from src import app_manager
from src.controllers import find_and_optimize_documents
from src.modules.document import (
    Document,
    Metadata
)


def get_documents(
    query_text: str, k: int = 6, filter: Optional[Dict[str, Any]] = None, **kwargs
) -> List[dict]:
    """
    Searches for documents based on the provided query string, applying optional filters and additional parameters.

    This function communicates with a document store to retrieve documents that match the given query. It supports
    additional filtering and configuration via keyword arguments.

    Args:
        query (str): The search query to match documents.
        k (int, optional): The maximum number of search results to return. Defaults to 6.
        filter (Optional[Dict[str, Any]], optional): A dictionary of filtering criteria to apply to the search.
            These criteria are dependent on the document store's capabilities.
        **kwargs: Arbitrary keyword arguments for additional search configuration. Common parameters include:
            - score_threshold (Optional[float]): A minimum score threshold for documents to be considered a match.
            - powerset (Optional[bool]): A flag indicating whether to use powerset for generating query permutations.
              This can be useful in certain types of searches where all possible subsets of the query terms should be considered.

    Returns:
        List[dict]: A list of dictionaries, each representing a document matching the search criteria. Each dictionary
            contains details of the document, such as its content and metadata.

    Example usage:
        # Basic search with no additional parameters
        documents = await get_documents(query="example search")

        # Search with a score threshold and custom filter
        documents = await get_documents(query="advanced search", score_threshold=0.5, filter={"tags": "news"})
    """

    if filter is not None:
        # Assuming Metadata is a class or method that processes the filter dict
        filter = Metadata(**filter)

    docs = app_manager.get_vector_store().search(
        query_text=query_text,
        k=k,
        filter=filter,
        **kwargs  # Additional search configuration passed directly to the query method
    )

    # Optional re-ranking of documents based on custom logic
    reranker = app_manager.get_reranker()
    reranked_docs = reranker.rerank_documents(
        docs, query_text
    )

    # Converting search results to a list of dictionaries for the response
    return [doc.to_dict() for doc in reranked_docs]


def chat_with_kb(message: str, dep_name: str = None) -> str:
    if not app_manager.LLM_MODEL_PATH:
        return app_manager.RESPONSE_LLM_MODEL_PATH_NOT_FOUND

    docs = find_and_optimize_documents(message, dep_name=dep_name)

    model = app_manager.get_llm_model()
    history = build_history(docs)
    response = model.get_response(
        message,
        app_manager.LLM_CHAT_PROMPT,
        history
    )
    return response


def build_history(reranked_documents: List[Document]):
    document_texts = "".join(doc.page_content for doc in reranked_documents)
    system_prompt = app_manager.LLM_SYSTEM_PROMPT.format(document_texts)

    if len(reranked_documents) < 1:
        app_manager.LLM_SYSTEM_PROMPT.format(
            app_manager.LLM_SYSTEM_PROMPT_FILLNON)
    _history = [{"role": "system", "content": system_prompt}]

    return _history

import logging
from typing import Any, Dict, List, Tuple, Optional, Union

import numpy as np

from src import app_manager
from src.modules.document import (
    Document,
    Metadata
)
from src.modules.document.vectorstore import VectorStoreError
from src.modules.database import Document as Docdb
from src.modules.database.user import User, Role


logger = logging.getLogger(__name__)


user_db = User(app_manager.get_database_instance())
doc_db = Docdb(app_manager.get_database_instance())
role_db = Role(app_manager.get_database_instance())


def find_and_optimize_documents(query: str, tags: Optional[List[str]] = None) -> List[Document]:
    """
    Finds and optimizes documents based on the query text and department name.
    Allows specification of document type for more targeted searches.

    Args:
        query (str): The text query to search for relevant documents.
        tags (Optional[List[str]]): Additional tags for further refining the search. Default is None.

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

    if tags:
        for tag in tags:
            metadata.tags.add_tag(tag)

    found_documents = []
    current_attempt = 0
    score_threshold = initial_score_threshold

    # Dynamically adjust score threshold to find at least the minimum required documents
    while current_attempt < attempt_limit and len(found_documents) < min_documents_required:
        found_documents = app_manager.get_vector_store().search(
            query=query,
            filter=metadata,
            k=10,
            score_threshold=score_threshold,
            powerset=False
        )

        score_threshold = min(
            score_threshold + score_adjustment_step, max_score_threshold)
        current_attempt += 1

    # Rerank the found documents based on additional criteria, if needed
    optimized_documents = app_manager.get_reranker(
    ).rerank_documents(found_documents, query)

    return optimized_documents


def get_documents(
    query: str, k: int = 6, filter: Optional[Dict[str, Any]] = None, **kwargs
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
        query=query,
        k=k,
        filter=filter,
        **kwargs  # Additional search configuration passed directly to the query method
    )

    # Optional re-ranking of documents based on custom logic
    reranker = app_manager.get_reranker()
    reranked_docs = reranker.rerank_documents(
        docs, query
    )

    # Converting search results to a list of dictionaries for the response
    return [doc.to_dict() for doc in reranked_docs]


def add_document(
    data: str,
    metadata: Dict[str, Any],
    **kwargs
) -> List[Document]:
    return _add_documents_helper([Document(page_content=data, metadata=metadata)], **kwargs)


def add_documents(
    documents: List[Document],
    **kwargs
) -> List[Document]:
    return _add_documents_helper(documents, **kwargs)


def _add_documents_helper(
    documents: List[Document],
    **kwargs
) -> List[Document]:
    user_id = kwargs.get('user_id')
    if user_id is None:
        raise ValueError("User ID is required for adding a document.")

    user_info = user_db.get_user_by_id(user_id)
    if user_info is None:
        raise ValueError("User does not exist.")

    if not role_db.check_permission(user_info['role_id'], 'DOCUMENTS_CONTROL'):
        raise ValueError("User does not have permission to add documents.")

    new_documents = []
    for new_doc in documents:
        if len(new_doc.metadata.tags.get_tags()) < 1:
            raise ValueError(
                "Each document must have at least one tag in its metadata.")
        new_documents.append(new_doc)

    try:
        store = app_manager.get_vector_store()
        added_documents = store.add_documents(new_documents)
        if len(added_documents) <= 0:
            raise VectorStoreError(
                "Failed to add documents to the VectorStore.")

        store.save_index()

        for added_document in added_documents:
            doc_db.add_document(
                added_document.page_content,
                str(added_document.metadata.to_dict()),
                user_id
            )

        logger.info("Documents added successfully.")
        return added_documents
    except Exception as e:
        logger.error("An error occurred while adding documents: %s", str(e))
        return []


def delete_documents_by_ids(
    ids_to_delete: List[str],
    **kwargs
) -> Union[Tuple[int, int], str]:
    user_id = kwargs.get('user_id')
    if user_id is None:
        raise ValueError("User ID is required for deleting a document.")

    user_info = user_db.get_user_by_id(user_id)
    if user_info is None:
        raise ValueError("User does not exist.")

    if not role_db.check_permission(user_info['role_id'], 'DOCUMENTS_CONTROL'):
        raise ValueError("User does not have permission to delete documents.")

    try:
        store = app_manager.get_vector_store()

        ret = store.delete_documents_by_ids(ids_to_delete)

        store.save_index()

        logger.info("Document removed successfully.")

        return ret
    except Exception as e:
        logger.error("An error occurred while deleting a document: %s", str(e))
        raise  # Rethrowing the exception after logging


def update_document(
    ids: str,
    data: dict[str, Any],
    **kwargs
) -> Optional[Document]:
    user_id = kwargs.get('user_id')
    if user_id is None:
        raise ValueError("User ID is required for updating a document.")

    user_info = user_db.get_user_by_id(user_id)
    if user_info is None:
        raise ValueError("User does not exist.")

    if not role_db.check_permission(user_info['role_id'], 'DOCUMENTS_CONTROL'):
        raise ValueError("User does not have permission to update documents.")

    try:
        store = app_manager.get_vector_store()
        ret = store.delete_documents_by_ids([ids])
        if isinstance(ret, tuple):
            n_removed, _ = ret
            if n_removed == 0:
                raise ValueError(
                    f"No document found with ID: {ids}. Unable to update.")

            if "metadata" not in data or "data" not in data:
                raise ValueError(
                    "Invalid data provided for document modification.")

            metadata = data['metadata']
            page_content = data['data']
            new_documents = Document(page_content, metadata)
            results = store.add_documents([new_documents])
            if len(results) <= 0:
                raise VectorStoreError(
                    "Failed to add document to the database.")

            for new_doc in results:
                doc_db.add_document(
                    new_doc.page_content,
                    str(new_doc.metadata.to_dict()),
                    kwargs.get('user_id'),
                    'Document updated.'
                )
            store.save_index()

            logger.info("Document modified successfully.")

            return results[0]
    except Exception as e:
        logger.error("An error occurred while updating a document: %s", str(e))
        raise  # Rethrowing the exception after logging


def chat_with_kb(query: str, dep_name: str = None) -> str:
    if not app_manager.LLM_MODEL_PATH:
        return app_manager.RESPONSE_LLM_MODEL_PATH_NOT_FOUND

    def build_history(reranked_documents: List[Document]) -> List[Dict[str, str]]:
        if reranked_documents:
            document_texts = "".join(
                doc.page_content for doc in reranked_documents)
            system_prompt = app_manager.LLM_SYSTEM_PROMPT.format(
                document_texts)
        else:
            system_prompt = app_manager.LLM_SYSTEM_PROMPT.format(
                app_manager.LLM_SYSTEM_PROMPT_FILLNON)

        _history = [{"role": "system", "content": system_prompt}]

        return _history

    docs = find_and_optimize_documents(query, [dep_name])
    if len(docs) > 0:
        history = build_history(docs)
        model = app_manager.get_llm_model()
        response = model.get_response(
            query,
            app_manager.LLM_CHAT_PROMPT,
            history
        )
        return response

    return '暂未找到任何相关信息！'

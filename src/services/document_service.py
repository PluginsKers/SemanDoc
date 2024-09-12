import logging
import re
from typing import Any, Dict, List, Optional

from src import app_manager
from src.modules.document import (
    Document,
    Metadata
)
from src.modules.database import Document as DocumentDatabase
from src.modules.database.user import User, Role
from src.services.auth_service import check_permissions


logger = logging.getLogger(__name__)


userDB = User(app_manager.get_database_instance())
docDB = DocumentDatabase(app_manager.get_database_instance())
roleDB = Role(app_manager.get_database_instance())


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
    initial_score_threshold = 0.2
    score_adjustment_step = 0.08
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

    while current_attempt < attempt_limit and len(found_documents) < min_documents_required:
        found_documents = app_manager.get_vector_store().search(
            query=query,
            filter=metadata,
            k=10,
            score_threshold=score_threshold,
            powerset=True
        )

        score_threshold = min(
            score_threshold + score_adjustment_step, max_score_threshold)
        current_attempt += 1

    optimized_documents = app_manager.get_reranker(
    ).rerank_documents(found_documents, query)

    return optimized_documents


def get_documents(
    query: str, k: int = 6, filter: Optional[Dict[str, Any]] = None, **kwargs
) -> List[Document]:
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
        query,
        k,
        filter,
        **kwargs
    )

    # Optional re-ranking of documents based on custom logic
    reranker = app_manager.get_reranker()
    reranked_docs = reranker.rerank_documents(
        docs, query
    )

    return reranked_docs


@check_permissions(['DOCUMENTS_CONTROL'])
def add_document(
    data: str,
    metadata: Dict[str, Any],
    **kwargs
) -> List[Document]:
    return _add_documents_helper([Document(page_content=data, metadata=metadata)], **kwargs)


@check_permissions(['DOCUMENTS_CONTROL'])
def add_documents(
    documents: List[Document],
    **kwargs
) -> List[Document]:
    return _add_documents_helper(documents, True, **kwargs)


def _add_documents_helper(
    documents: List[Document],
    bundle_errors: bool = False,
    **kwargs
) -> List[Document]:
    user_id = kwargs.get('user_id')
    new_documents = []
    errors = []
    for new_doc in documents:
        if len(new_doc.metadata.tags.get_tags()) < 1:
            if not bundle_errors:
                raise ValueError(
                    "Each document must have at least one tag in its metadata.")
            else:
                errors.append(new_doc)
                continue

        seq_len = len(re.findall(r'[\u4e00-\u9fff]', new_doc.page_content))

        if seq_len <= 16:
            if not bundle_errors:
                raise ValueError(
                    "At least 16 characters are required.")
            else:
                errors.append(new_doc)
                continue

        new_documents.append(new_doc)

    try:
        store = app_manager.get_vector_store()

        added_documents = store.add_documents(new_documents)

        if len(added_documents) <= 0:
            raise RuntimeError(
                "Failed to add documents to the VectorStore.")

        store.save_index()

        for added_document in added_documents:
            docDB.add_document(
                added_document.metadata.ids,
                added_document.page_content,
                str(added_document.metadata.to_dict()),
                user_id,
                "添加文档"
            )

        logger.info("Documents added successfully.")
        return added_documents
    except Exception as e:
        logger.error("An error occurred while adding documents: %s", str(e))
        return []


@check_permissions(['DOCUMENTS_CONTROL'])
def delete_documents_by_ids(
    ids_to_delete: List[str],
    **kwargs
) -> List[Document]:
    user_id = kwargs.get('user_id')
    try:
        store = app_manager.get_vector_store()

        results = store.delete_documents_by_ids(ids_to_delete)

        store.save_index()

        for removal_document in results:
            docDB.delete_document_by_ids(
                removal_document.metadata.ids,
                kwargs.get('user_id'),
                "删除文档"
            )

        logger.info("Document removed successfully.")

        return [d.to_dict() for d in results]
    except Exception as e:
        logger.error("An error occurred while deleting a document: %s", str(e))
        raise  # Rethrowing the exception after logging


@check_permissions(['DOCUMENTS_CONTROL'])
def update_document_by_ids(
    ids: str,
    data: dict[str, Any],
    **kwargs
) -> Optional[Document]:
    user_id = kwargs.get('user_id')
    try:
        store = app_manager.get_vector_store()
        d_ret = store.delete_documents_by_ids([ids])
        if isinstance(d_ret, list):
            if len(d_ret) == 0:
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
                raise RuntimeError(
                    "Failed to add document to the database.")

            for new_document in results:
                docDB.add_document(
                    new_document.metadata.ids,
                    new_document.page_content,
                    str(new_document.metadata.to_dict()),
                    kwargs.get('user_id'),
                    "更新文档"
                )
            store.save_index()

            logger.info("Document modified successfully.")

            return results[0]
    except Exception as e:
        logger.error("An error occurred while updating a document: %s", str(e))
        raise  # Rethrowing the exception after logging


@check_permissions(['DOCUMENTS_CONTROL'])
def get_documents_records(**kwargs) -> list:
    user_id = kwargs.get('user_id')
    if user_id is None:
        raise ValueError(
            "User ID is required for getting the document records.")

    docs_records = docDB.get_documents_records()

    for j in docs_records:
        j['document'] = docDB.get_document_by_id(j['document_id'])
        j['editor'] = userDB.get_user_by_id(j['editor_id'])

    return docs_records


def evaluate_text_relevance(text1: str, text2: str) -> bool:
    """
    Evaluates the relevance between two texts using the vector store's embedding model.

    Args:
        text1 (str): The first text to compare.
        text2 (str): The second text to compare.

    Returns:
        bool: True if the texts are relevant, False if they are not relevant.
    """
    store = app_manager.get_vector_store()
    relevance_score = store.evaluate_text_relevance(text1, text2)
    
    # Define a threshold for relevance
    RELEVANCE_THRESHOLD = 0.5  # This value can be adjusted based on your needs
    
    return relevance_score >= RELEVANCE_THRESHOLD

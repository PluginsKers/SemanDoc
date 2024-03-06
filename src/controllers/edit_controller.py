from src.modules.document.vecstore import VectorStoreEditError
from src import get_vector_store
from typing import Union, Optional, List, Tuple
from src.modules.document import Document


import logging
logger = logging.getLogger(__name__)


async def add_document(
    data: dict, comment: Optional[str] = None
) -> Union[Tuple[List[Document]], str]:
    if comment:
        logger.info(comment)  # Using logging instead of print

    try:
        metadata = data.get("metadata")
        if not metadata or "page_content" not in data:
            raise ValueError("Invalid data provided for document addition.")

        add_result = await get_vector_store().add_documents(
            [Document(page_content=data["page_content"], metadata=metadata)]
        )
        if len(add_result) <= 0:
            raise VectorStoreEditError(
                "Failed to add document to the database.")

        return tuple([add_result])
    except Exception as e:
        logger.error("An error occurred while adding a document: %s", str(e))
        raise  # Rethrowing the exception after logging


def delete_documents_by_ids(
    ids_to_delete: List[int], comment: Optional[str] = None
) -> Union[Tuple[int, int], str]:
    if comment:
        print(comment)

    removal_result = get_vector_store().remove_documents_by_ids(ids_to_delete)

    return removal_result


def delete_documents_by_id(
    id_to_delete: List[str], comment: Optional[str] = None
) -> Union[Tuple[int, int], str]:
    if comment:
        print(comment)

    removal_result = get_vector_store().remove_documents_by_id(id_to_delete)

    return removal_result


def delete_documents_by_tags(
    tags_to_delete: List[str], comment: Optional[str] = None
) -> Union[Tuple[int, int], str]:
    if comment:
        print(comment)

    removal_result = get_vector_store().remove_documents_by_tags(tags_to_delete)

    return removal_result

from src.modules.document.vecstore import VectorStoreEditError
from src import get_vector_store
from typing import Union, Optional, List, Tuple
from src.modules.document import Document


import logging
logger = logging.getLogger(__name__)


async def add_document(
    data: dict
) -> Union[Tuple[List[Document]], str]:
    try:
        store = get_vector_store()
        metadata = data.get("metadata")
        if not metadata or "page_content" not in data:
            raise ValueError("Invalid data provided for document addition.")

        add_result = await store.add_documents(
            [Document(page_content=data["page_content"], metadata=metadata)]
        )
        if len(add_result) <= 0:
            raise VectorStoreEditError(
                "Failed to add document to the database.")

        await store.save_index()

        return tuple([add_result])
    except Exception as e:
        logger.error("An error occurred while adding a document: %s", str(e))
        raise  # Rethrowing the exception after logging


async def modify_documents_by_ids(
    ids: int,
    data: dict
) -> Union[Tuple[List[Document]], str]:
    try:
        store = get_vector_store()

        removal_result = store.remove_documents_by_ids([ids])
        if isinstance(removal_result, tuple):
            n_removed, n_total = removal_result
            if n_removed == 0:
                return []

            metadata = data.get("metadata")
            if not metadata or "page_content" not in data:
                raise ValueError("Invalid data provided for document modify.")

            add_result = await get_vector_store().add_documents(
                [Document(page_content=data["page_content"], metadata=metadata)]
            )

            if len(add_result) <= 0:
                raise VectorStoreEditError(
                    "Failed to modify document from the database.")

            await store.save_index()

            return tuple([add_result])
    except Exception as e:
        logger.error("An error occurred while modify a document: %s", str(e))
        raise  # Rethrowing the exception after logging


async def delete_documents_by_ids(
    ids_to_delete: List[int]
) -> Union[Tuple[int, int], str]:

    store = get_vector_store()

    removal_result = store.remove_documents_by_ids(ids_to_delete)

    await store.save_index()

    return removal_result


async def delete_documents_by_id(
    id_to_delete: List[str]
) -> Union[Tuple[int, int], str]:

    store = get_vector_store()

    removal_result = store.remove_documents_by_id(id_to_delete)

    await store.save_index()

    return removal_result


async def delete_documents_by_tags(
    tags_to_delete: List[str]
) -> Union[Tuple[int, int], str]:

    store = get_vector_store()

    removal_result = store.remove_documents_by_tags(tags_to_delete)

    await store.save_index()

    return removal_result

from typing import (
    Any,
    Union,
    List,
    Tuple
)

from src import app_manager
from src.modules.document import Document
from src.modules.document.vectorstore import VectorStoreError
from src.modules.database import Document as Docdb


import logging

logger = logging.getLogger(__name__)


def add_document(
    data: dict[str, Any]
) -> List[Document]:
    try:
        store = app_manager.get_vector_store()
        doc_db = Docdb(app_manager.get_database_instance())
        if "metadata" not in data or "page_content" not in data:
            raise ValueError(
                "Invalid data provided for document modification.")

        metadata = data['metadata']
        page_content = data['page_content']
        new_doc = Document(page_content, metadata)

        if len(new_doc.metadata.tags.get_tags()) < 1:
            raise ValueError(
                "The document must have at least one tag in its metadata.")

        docs = store.add_documents([new_doc])
        if len(docs) <= 0:
            raise VectorStoreError(
                "Failed to add document to the VectorStore.")

        doc_db.add_document(
            new_doc.page_content,
            str(new_doc.metadata)
        )
        store.save_index()

        logger.info("Document added successfully.")

        return docs
    except Exception as e:
        logger.error("An error occurred while adding a document: %s", str(e))
        raise  # Rethrowing the exception after logging


def delete_documents_by_ids(
    ids_to_delete: List[str]
) -> Union[Tuple[int, int], str]:
    try:
        store = app_manager.get_vector_store()

        ret = store.delete_documents_by_ids(ids_to_delete)

        store.save_index()

        logger.info("Document removed successfully.")

        return ret
    except Exception as e:
        logger.error("An error occurred while deleting a document: %s", str(e))
        raise  # Rethrowing the exception after logging


def update_document_by_ids(
    ids: str,
    data: dict[str, Any]
) -> Document:
    try:
        store = app_manager.get_vector_store()
        doc_db = Docdb(app_manager.get_database_instance())
        ret = store.delete_documents_by_ids([ids])
        if isinstance(ret, tuple):
            n_removed, _ = ret
            if n_removed == 0:
                return []

            if "metadata" not in data or "page_content" not in data:
                raise ValueError(
                    "Invalid data provided for document modification.")

            metadata = data['metadata']
            page_content = data['page_content']
            new_doc = Document(page_content, metadata)
            results = store.add_documents([new_doc])
            if len(results) <= 0:
                raise VectorStoreError(
                    "Failed to add document to the database.")

            doc_db.add_document(
                new_doc.page_content,
                str(new_doc.metadata)
            )
            store.save_index()

            logger.info("Document modified successfully.")

            return results[0]
    except Exception as e:
        logger.error("An error occurred while updating a document: %s", str(e))
        raise  # Rethrowing the exception after logging

import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
from typing import Optional, Tuple, List, Dict, Any
import numpy as np

from langchain.vectorstores.faiss import FAISS
from langchain.embeddings import HuggingFaceBgeEmbeddings

from src.modules.logging import logger
from src.modules.document import Document


def validate_metadata(target: dict, metadata: dict) -> bool:
    """
    Filter metadata based on a target and filter dictionary.

    Args:
    - target (dict): Target metadata dictionary to filter.
    - metadata (dict): Filter metadata dictionary.

    Returns:
    - bool: True if the target metadata passes the filter, False otherwise.
    """
    for key, value in metadata.items():
        if key not in target:
            return False

        target_value = target[key]

        if isinstance(value, list):
            if not any(item in target_value for item in value):
                return False

        elif isinstance(value, dict):
            if not validate_metadata(target_value, value):
                return False

        elif target_value != value:
            return False

    return True


class DocumentStore:
    """
    Manages a document store for efficient retrieval based on document content and metadata.
    """

    def __init__(self, index_dir: str, embedding_model_name: str):
        """
        Initializes the document store with the specified index path and embedding model.

        Args:
            index_dir (str): Path to the directory where the FAISS index will be stored.
            embedding_model_name (str): Name of the Hugging Face model to use for text embeddings.
        """
        self.index_dir = index_dir
        self.embedding = HuggingFaceBgeEmbeddings(
            model_name=embedding_model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
            query_instruction="Generate representation for this sentence for retrieval:",
        )
        self.index: Optional[FAISS] = self._load_or_create_index()

    async def save_index(self):
        """
        Saves the FAISS index to the specified directory.
        """
        index_path = os.path.join(self.index_dir, "store")
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(executor, self.index.save_local, index_path)
            logger.info("Index successfully saved to %s", index_path)

        except Exception as e:
            logger.error("Error saving index: %s", e)

    def _load_or_create_index(self) -> FAISS:
        """
        Loads an existing FAISS index from the index path or creates a new one if not found.

        Returns:
            FAISS: The loaded or newly created FAISS index.
        """
        index_path = os.path.join(self.index_dir, "store")
        if not os.path.exists(index_path):
            logger.info("Local database not found, creating a new one.")
            os.makedirs(self.index_dir, exist_ok=True)
            index = FAISS.from_documents(
                [
                    Document(
                        page_content="I am a vector retrieval system, the brain of Xiaoning!",
                        metadata={"ids": 0, "tags": ["__init__"]},
                    )
                ],
                self.embedding,
            )
        else:
            logger.info("Loaded index from %s", index_path)
            index = FAISS.load_local(index_path, self.embedding)
        return index

    def _get_next_ids(self) -> int:
        """
        Get the next available document ID.

        Returns:
        - int: The next available document ID.
        """
        all_ids = [
            int(doc.metadata["ids"]) for _id, doc in self.index.docstore._dict.items()
        ]
        max_ids = max(all_ids) if all_ids else 0
        return max_ids + 1

    def _is_document_currently_valid(self, document: Document) -> bool:
        """
        Check if a document is currently valid based on its metadata.

        Args:
        - document (Document): Document to check for validity.

        Returns:
        - bool: True if the document is currently valid, False otherwise.
        """
        current_time = time.time()
        valid_time = document.metadata.get("valid_time")
        start_time = document.metadata.get("start_time")

        if valid_time == -1:
            return True

        if valid_time is None or start_time is None:
            return True

        valid_time = float(valid_time)
        start_time = float(start_time)

        return (start_time + valid_time) >= current_time

    async def add_documents(self, documents: List[Document]) -> List[Document]:
        """
        Adds a list of documents to the document store.

        Args:
            documents (List[Document]): List of documents to add.

        Returns:
            List[Document]: The list of added documents.
        """
        next_id = self._get_next_ids()
        added_documents = []
        for doc in documents:
            doc.metadata["ids"] = next_id
            next_id += 1
            added_documents.append(doc)
        try:
            await self.index.aadd_documents(added_documents)
            await self.save_index()
        except Exception as e:
            logger.error("Failed to add documents: %s", e)
        return added_documents

    def remove_documents_by_id(
        self, target_id_list: Optional[List[str]]
    ) -> Tuple[int, int]:
        """
        Remove documents from the index based on their IDs.

        Args:
        - target_id_list (Optional[List[str]]): List of document IDs to remove.
        If None, clears the index.

        Returns:
        - Tuple[int, int]: Count of removed docs and total count after removal.
        """
        if target_id_list is None:
            self.index.docstore = {}
            self.index.index_to_docstore_id = {}
            n_removed = self.index.index.ntotal
            n_total = self.index.index.ntotal
            self.index.index.reset()
            return n_removed, n_total
        set_ids = set(target_id_list)
        if len(set_ids) != len(target_id_list):
            raise ValueError("Duplicate ids in the list of ids to remove.")
        index_ids = [
            i_id
            for i_id, d_id in self.index.index_to_docstore_id.items()
            if d_id in target_id_list
        ]
        n_removed = len(index_ids)
        n_total = self.index.index.ntotal
        self.index.index.remove_ids(np.array(index_ids, dtype=np.int64))
        for i_id, d_id in zip(index_ids, target_id_list):
            del self.index.docstore._dict[d_id]
            del self.index.index_to_docstore_id[i_id]
        self.index.index_to_docstore_id = {
            i: d_id for i, d_id in enumerate(self.index.index_to_docstore_id.values())
        }
        asyncio.run(self.save_index())
        return n_removed, n_total

    def remove_documents_by_ids(self, target_ids: List[int]) -> Tuple[int, int]:
        """
        Remove documents from the index based on their IDs.

        Args:
        - target_ids (List[int]): List of document IDs to remove.

        Returns:
        - Tuple[int, int]: Count of removed and total documents after removal.
        """
        if target_ids is None or len(target_ids) < 1:
            raise ValueError("Parameter target_ids cannot be empty.")

        id_to_remove = []
        for _id, doc in self.index.docstore._dict.items():
            to_remove = False
            if doc.metadata["ids"] in target_ids:
                to_remove = True
            if to_remove:
                id_to_remove.append(_id)
        return self.remove_documents_by_id(id_to_remove)

    def remove_documents_by_tags(self, target_tags: List[str]) -> Tuple[int, int]:
        """
        Remove documents from the index based on their tags.

        Args:
        - target_tags (List[str]): Tags to filter documents for removal.

        Returns:
        - Tuple[int, int]: Count of removed and total documents after removal.
        """
        if target_tags is None or len(target_tags) < 1:
            raise ValueError("Parameter target_tags cannot be empty.")

        id_to_remove = []
        for _id, doc in self.index.docstore._dict.items():
            to_remove = False
            if doc.metadata["tags"] == target_tags:
                to_remove = True
            if to_remove:
                id_to_remove.append(_id)
        return self.remove_documents_by_id(id_to_remove)

    async def search(
        self,
        query: str,
        k: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
        fetch_k: int = 20,
        **kwargs: Any
    ) -> List[Document]:
        """
        Perform a similarity search and retrieve documents.

        Args:
        - query (str): Query string for similarity search.
        - k (int): Number of documents to retrieve.
        - metadata (Optional[Dict[str, Any]]): Metadata filter for document
        retrieval.
        - fetch_k (int): Number of documents to fetch initially.

        Returns:
        - List[Document]: List of retrieved documents.
        """
        docs_and_scores = await self.index.asimilarity_search_with_score(
            query, k=fetch_k, fetch_k=fetch_k, **kwargs
        )

        docs = [Document(doc.page_content, doc.metadata)
                for doc, _ in docs_and_scores]

        if metadata is not None:
            valid_docs = [
                doc for doc in docs if validate_metadata(doc.metadata, metadata)
            ]
        else:
            valid_docs = [
                doc for doc in docs if self._is_document_currently_valid(doc)]

        return valid_docs[:k]

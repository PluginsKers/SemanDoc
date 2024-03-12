import os
import asyncio
import threading
import logging
import time
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from langchain.vectorstores.faiss import FAISS
from langchain.embeddings import HuggingFaceBgeEmbeddings

from src.modules.document import Document

logger = logging.getLogger(__name__)


class VecstoreError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def filter_by_metadata(target: dict, metadata: dict) -> bool:
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
            if not filter_by_metadata(target_value, value):
                return False

        elif target_value != value:
            return False

    return True


class VectorStore:
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
        self.faiss_dir = index_dir
        self.embedding = HuggingFaceBgeEmbeddings(
            model_name=embedding_model_name,
            model_kwargs={"device": "cuda:0"},
            encode_kwargs={"normalize_embeddings": True},
            query_instruction="为这个句子生成表示以用于检索相关文章：",
        )
        self.faiss: Optional[FAISS] = self._load_or_create_index()

    async def save_index(self):
        """
        Saves the FAISS index to the specified directory.
        """

        def run_rebuild_index():
            asyncio.run(self.rebuild_index())

        # 启动新线程运行rebuild_index
        rebuild_thread = threading.Thread(target=run_rebuild_index)
        rebuild_thread.start()

        index_path = os.path.join(self.faiss_dir, "store")
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(executor, self.faiss.save_local, index_path)
            logger.info("Index successfully saved to %s", index_path)

        except Exception as e:
            logger.error("Error saving index: %s", e)

    def _load_or_create_index(self) -> FAISS:
        """
        Loads an existing FAISS index from the index path or creates a new one if not found.

        Returns:
            FAISS: The loaded or newly created FAISS index.
        """
        index_path = os.path.join(self.faiss_dir, "store")
        if not os.path.exists(index_path):
            logger.info("Local database not found, creating a new one.")
            os.makedirs(self.faiss_dir, exist_ok=True)
            index = FAISS.from_documents(
                [
                    Document(
                        page_content="我是小宁，一个知识库管理助手！",
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
            int(doc.metadata["ids"]) for _id, doc in self.faiss.docstore._dict.items()
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
            await self.faiss.aadd_documents(added_documents)
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
            self.faiss.docstore = {}
            self.faiss.index_to_docstore_id = {}
            n_removed = self.faiss.index.ntotal
            n_total = self.faiss.index.ntotal
            self.faiss.index.reset()
            return n_removed, n_total
        set_ids = set(target_id_list)
        if len(set_ids) != len(target_id_list):
            raise ValueError("Duplicate ids in the list of ids to remove.")
        index_ids = [
            i_id
            for i_id, d_id in self.faiss.index_to_docstore_id.items()
            if d_id in target_id_list
        ]
        n_removed = len(index_ids)
        n_total = self.faiss.index.ntotal
        self.faiss.index.remove_ids(np.array(index_ids, dtype=np.int64))
        for i_id, d_id in zip(index_ids, target_id_list):
            del self.faiss.docstore._dict[d_id]
            del self.faiss.index_to_docstore_id[i_id]
        self.faiss.index_to_docstore_id = {
            i: d_id for i, d_id in enumerate(self.faiss.index_to_docstore_id.values())
        }
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
        for _id, doc in self.faiss.docstore._dict.items():
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
        for _id, doc in self.faiss.docstore._dict.items():
            to_remove = False
            if doc.metadata["tags"] == target_tags:
                to_remove = True
            if to_remove:
                id_to_remove.append(_id)
        return self.remove_documents_by_id(id_to_remove)

    async def rebuild_index(self):
        """
        Asynchronously rebuilds the FAISS index from the current documents in the document store,
        optionally performing optimizations such as deduplication.
        """
        loop = asyncio.get_event_loop()

        # Define the rebuild work as a separate function for ThreadPoolExecutor
        def do_rebuild():
            valid_documents = []
            seen_contents = set()

            # Collect valid and unique documents
            for doc_id, document in self.faiss.docstore._dict.items():
                if self._is_document_currently_valid(document):
                    # Optional: Deduplication based on content
                    content_hash = hash(document.page_content)
                    if content_hash not in seen_contents:
                        valid_documents.append(document)
                        seen_contents.add(content_hash)

            logger.info(
                f"Rebuilding index with {len(valid_documents)} valid documents.")

            # Create a new index with collected documents
            new_index = FAISS.from_documents(valid_documents, self.embedding)

            # Replace the old index with the new one
            self.faiss = new_index

            logger.info("Index successfully rebuilt.")

        # Run the rebuild work in a ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(executor, do_rebuild)

    async def query(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        fetch_k: int = 20,
        **kwargs: Any
    ) -> List[Document]:
        """
        Perform a similarity search and retrieve documents.

        Args:
        - query (str): Query string for similarity search.
        - k (int): Number of documents to retrieve.
        - filter (Optional[Dict[str, Any]]): Metadata filter for document
        retrieval.
        - fetch_k (int): Number of documents to fetch initially.

        Returns:
        - List[Document]: List of retrieved documents.
        """

        if filter is None:
            filter = {}

        def powerset(tags: List[str]) -> List[List[str]]:
            result = [[]]
            for i in range(len(tags)):
                tag = tags[i]
                new_subsets = [subset + [tag] for subset in result]
                result.extend(new_subsets)

            return result

        if "tags" in filter and isinstance(filter["tags"], list):
            tags = filter.pop("tags")  # Extract and remove original tags
            permutations_of_tags = powerset(tags)  # Generate permutations
            filter.update({"tags": permutations_of_tags})

        score_threshold = kwargs.get("score_threshold")
        if score_threshold is not None:
            kwargs.update({"score_threshold": score_threshold + 0.18})
        docs_and_scores = await self.faiss.asimilarity_search_with_score(
            query, filter=filter, k=fetch_k, fetch_k=fetch_k*2, **kwargs
        )

        docs = [Document(doc.page_content, doc.metadata)
                for doc, _ in docs_and_scores]

        valided_documents = [
            doc for doc in docs if self._is_document_currently_valid(doc)]

        return valided_documents[:k]

import os
import time
from typing import Optional, Tuple, List, Dict, Any
import numpy as np

from langchain.vectorstores.faiss import FAISS
from langchain.embeddings import HuggingFaceBgeEmbeddings

from src.modules.logging import logger
from src.modules.document import Document


def meta_filter(target: dict, metadata: dict) -> bool:
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
            if not meta_filter(target_value, value):
                return False

        elif target_value != value:
            return False

    return True


class DocStore:
    def __init__(
        self,
        index_dir_path: str,
        embedding_model_name_or_path: str
    ):
        """
        Initialize the DocStore with the specified index directory and
        embedding model.

        Args:
        - index_dir_path (str): Path to the directory containing the index.
        - embedding_model_name_or_path (str): Name or path of the embedding
        model.
        """
        self.embedding_model_name_or_path = embedding_model_name_or_path
        self.embedding_model_kwargs = {'device': 'cpu'}
        self.embedding_encode_kwargs = {'normalize_embeddings': True}
        self.embedding = HuggingFaceBgeEmbeddings(
            model_name=self.embedding_model_name_or_path,
            model_kwargs=self.embedding_model_kwargs,
            encode_kwargs=self.embedding_encode_kwargs,
            query_instruction="Generate representation for this sentence for retrieval:"
        )

        self.index_dir_path = index_dir_path
        self.index: Optional[FAISS] = self.get_faiss_index(self.index_dir_path)

    def get_faiss_index(self, index_dir_path: str) -> FAISS:
        """
        Get or create a FAISS index.

        Args:
        - index_dir_path (str): Path to the directory containing the index.

        Returns:
        - FAISS: The FAISS index.
        """
        index_path: str = os.path.join(index_dir_path, 'index.faiss')
        if os.path.exists(index_path):
            logger.info('Loaded: %s', index_path)
            index = FAISS.load_local(index_path, self.embedding)
        else:
            logger.info('Local Database not found.')
            index = FAISS.from_documents(
                [
                    Document(
                        page_content='I am a vector retrieval system, the brain of Xiaoning!',
                        metadata={'ids': 0, 'tags': ['init_addition']},
                    )
                ],
                self.embedding
            )
            index.save_local(index_path)
            logger.info('Saved to the database.')
        return index

    def get_next_ids(self) -> int:
        """
        Get the next available document ID.

        Returns:
        - int: The next available document ID.
        """
        all_ids = [
            int(doc.metadata['ids'])
            for _id, doc in self.index.docstore._dict.items()
        ]
        max_ids = max(all_ids) if all_ids else 0
        return max_ids + 1

    def is_document_currently_valid(self, document: Document) -> bool:
        """
        Check if a document is currently valid based on its metadata.

        Args:
        - document (Document): Document to check for validity.

        Returns:
        - bool: True if the document is currently valid, False otherwise.
        """
        current_time = time.time()
        valid_time = document.metadata.get('valid_time')
        start_time = document.metadata.get('start_time')

        if valid_time == -1:
            return True

        if valid_time is None or start_time is None:
            return True

        valid_time = float(valid_time)
        start_time = float(start_time)

        return (start_time + valid_time) >= current_time

    async def add_documents(self, documents: List[Document]) -> List[Document]:
        """
        Add a list of documents to the index.

        Args:
        - documents (List[Document]): Documents to be added to the index.

        Returns:
        - List[Document]: Added documents.
        """
        next_ids = self.get_next_ids()
        added_list = []
        for doc in documents:
            doc.metadata['ids'] = int(next_ids)
            next_ids += 1
        try:
            await self.index.aadd_documents(documents)
            added_list = documents
            self.index.save_local(self.index_dir_path)
        except Exception as e:
            logger.error('Failed to add documents: %s', e)

        return added_list

    def remove_documents_by_id(
        self,
        target_id_list: Optional[List[str]]
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
            i: d_id
            for i, d_id in enumerate(self.index.index_to_docstore_id.values())
        }
        self.index.save_local(self.index_dir_path)
        return n_removed, n_total

    def remove_documents_by_ids(
        self,
        target_ids: List[int]
    ) -> Tuple[int, int]:
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
            if doc.metadata['ids'] in target_ids:
                to_remove = True
            if to_remove:
                id_to_remove.append(_id)
        return self.remove_documents_by_id(id_to_remove)

    def remove_documents_by_tags(
        self,
        target_tags: List[str]
    ) -> Tuple[int, int]:
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
            if doc.metadata['tags'] == target_tags:
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
            query,
            k=fetch_k,
            fetch_k=fetch_k,
            **kwargs
        )

        docs = [
            Document(doc.page_content, doc.metadata)
            for doc, _ in docs_and_scores
        ]

        if metadata is not None:
            valid_docs = [
                doc
                for doc in docs
                if meta_filter(doc.metadata, metadata)
            ]
        else:
            valid_docs = [
                doc
                for doc in docs
                if self.is_document_currently_valid(doc)
            ]

        return valid_docs[:k]

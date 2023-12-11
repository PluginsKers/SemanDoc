import os
import time
from typing import Optional, Tuple, List, Dict, Any
import numpy as np

from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceBgeEmbeddings

from src.modules.logging import logger

from src.modules.document import Document


class DataBase:
    def __init__(
        self,
        index_dir_path: str,
        embedding_model_name_or_path: str
    ):
        self.embedding_model_name_or_path = embedding_model_name_or_path
        self.embedding_model_kwargs = {'device': 'cpu'}
        self.embedding_encode_kwargs = {'normalize_embeddings': True}
        self.embedding = HuggingFaceBgeEmbeddings(
            model_name=self.embedding_model_name_or_path,
            model_kwargs=self.embedding_model_kwargs,
            encode_kwargs=self.embedding_encode_kwargs,
            query_instruction="为这个句子生成表示以用于检索相关文章："
        )

        self.index_dir_path = index_dir_path
        self.index: Optional[FAISS] = None
        self.load_index(self.index_dir_path)

    def load_index(self, index_dir_path: str):
        """Loads the index from the specified directory path.

        Args:
        - index_dir_path (str):
            The directory path where the index file is located.

        If the index file exists in the specified path,
            it loads the index using FAISS.
        If the index file doesn't exist, it initializes the index.
        """
        index_path: str = os.path.join(index_dir_path, 'index.faiss')
        if os.path.exists(index_path):
            logger.info('Loaded: %s', index_path)
            self.index = FAISS.load_local(index_path, self.embedding)
        else:
            logger.info('Local Database not found.')
            self.init_index()

    async def save_index(self, index_dir_path: str):
        """Saves the index to the specified directory path.

        Args:
        - index_dir_path (str):
            The directory path where the index will be saved.

        Saves the index to the specified path using the `save_local` method.

        If an error occurs during the saving process, it logs the exception.
        """
        try:
            index_path: str = os.path.join(index_dir_path, 'index.faiss')
            self.index.save_local(index_path)
            logger.info('Saved to the database.')
        except Exception as e:
            logger.error('Failed to save database: %s', e)

    def init_index(self):
        """Initializes the index with a default document.

        Initializes the index using FAISS by creating a document with default
        content and metadata.

        Saves the initialized index to the specified directory path
        using `save_index`.
        """
        self.index = FAISS.from_documents(
            [
                Document(
                    page_content='我是一个向量检索系统，是小宁的大脑！',
                    metadata={'ids': 0, 'tags': ['init_addition']},
                )
            ],
            self.embedding
        )

        # Save the initialized index
        self.save_index(self.index_dir_path)

    def get_next_ids(self) -> int:
        all_ids = [
            int(doc.metadata['ids'])
            for _id, doc in self.index.docstore._dict.items()
        ]
        max_ids = max(all_ids) if all_ids else 0
        return max_ids + 1

    async def add_documents(self, documents: List[Document]) -> List[Document]:
        """Adds a list of documents to the index.

        Args:
        - documents (List[Document]): Documents to be added to the index.

        Returns:
        - List[Document]: Added documents.

        Assigns unique IDs to the documents and adds them to the index
        using `aadd_documents`.

        Saves the updated index to the specified directory path
        using `save_index`.
        """

        next_ids = self.get_next_ids()
        added_list = []
        for doc in documents:
            doc.metadata['ids'] = int(next_ids)
            next_ids += 1
        try:
            await self.index.aadd_documents(documents)
            added_list = documents

            # Save the initialized index
            self.save_index(self.index_dir_path)
        except Exception as e:
            logger.error('Failed to add documents: %s', e)

        return added_list

    def remove_documents_by_id(
        self,
        target_id_list: Optional[List[str]]
    ):
        """Removes documents from the index based on their IDs.

        Args:
        - target_id_list (Optional[List[str]]): List of document IDs to remove.
        If None, clears the index.

        Returns:
        - Tuple[int, int]: Count of removed docs and total count after removal.

        Removes docs based on provided IDs. If list is None, clears the index.

        Saves updated index to specified directory path using `save_index`.
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
            raise ValueError("Duplicate ids in list of ids to remove.")
        index_ids = [
            i_id
            for i_id, d_id in self.index.index_to_docstore_id.items()
            if d_id in target_id_list
        ]
        n_removed = len(index_ids)
        n_total = self.index.index.ntotal
        self.index.index.remove_ids(np.array(index_ids, dtype=np.int64))
        for i_id, d_id in zip(index_ids, target_id_list):
            del self.index.docstore._dict[
                d_id
            ]

            del self.index.index_to_docstore_id[
                i_id
            ]
        self.index.index_to_docstore_id = {
            i: d_id
            for i, d_id in enumerate(self.index.index_to_docstore_id.values())
        }
        # Save the initialized index
        self.save_index(self.index_dir_path)
        return n_removed, n_total

    def remove_documents_by_ids(
        self,
        target_ids: List[int]
    ):
        """Removes documents from the index based on their IDs.

        Args:
        - target_ids (List[int]): List of document IDs to remove.

        Returns:
        - Tuple[int, int]: Count of removed and total documents after removal.

        Removes docs based on provided IDs.

        Raises a ValueError if 'target_ids' list is empty or None.

        Delegates removal to the `remove_documents_by_id` method.
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
    ):
        """Removes documents from the index based on their tags.

        Args:
        - target_tags (List[str]): Tags to filter documents for removal.

        Returns:
        - Tuple[int, int]: Count of removed and total documents after removal.

        Removes docs based on provided tags.

        Raises a ValueError if 'target_tags' list is empty or None.

        Delegates removal to the `remove_documents_by_id` method.
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

    def is_document_currently_valid(self, document: Document) -> bool:
        """Checks if a document is currently valid based on its metadata.

        Args:
        - document (Document): Document to check for validity.

        Returns:
        - bool: True if the document is currently valid, False otherwise.

        Determines document's current validity based on metadata.

        If 'valid_time' is -1, document is considered valid indefinitely.

        If 'valid_time' or 'start_time' metadata is missing,
        document is considered valid without limitations.

        Compares document's time validity range with current time in seconds.

        Returns True if document is currently within its valid time range,
        else False.
        """

        current_time = time.time()
        valid_time = document.metadata.get('valid_time')
        start_time = document.metadata.get('start_time')

        # If 'valid_time' in metadata is -1, document is valid indefinitely
        if valid_time == -1:
            return True

        # If 'valid_time' or 'start_time' metadata is missing, document is considered valid without limitations
        if valid_time is None or start_time is None:
            return True

        # Assuming timestamps are in seconds
        valid_time = float(valid_time)
        start_time = float(start_time)

        # Check if the document is within its validity time range
        return (start_time + valid_time) >= current_time

    async def search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        fetch_k: int = 20,
        **kwargs: Any
    ) -> List[Document]:
        """Searches for documents based on a query.

        Args:
        - query (str): The query string for the search.
        - k (int): The number of top results to retrieve. Default is 5.
        - filter (Optional[Dict[str, Any]]): Filters for the search. Default is None.
        - fetch_k (int): The number of documents to fetch initially. Default is 20.
        - **kwargs (Any): Additional keyword arguments.

        Returns:
        - List[Document]: A list of retrieved documents based
        on the search query.

        Searches for documents based on the provided query
        using similarity search.

        Retrieves top 'k' results and filters based
        on provided 'filter' criteria.

        Fetches 'fetch_k' documents initially and converts them to
        Document objects, ensuring current validity.

        Returns a list of valid documents up to 'k' in number.
        """
        docs_and_scores: List[Tuple[Document, float]] = await self.index.asimilarity_search_with_score(
            query,
            k=fetch_k,
            filter=filter,
            fetch_k=fetch_k,
            **kwargs
        )

        # 苟史langchain包的太严实了，这里要定制Document基本上都得转一下
        docs = [
            Document(doc.page_content, doc.metadata)
            for doc, _ in docs_and_scores
            if self.is_document_currently_valid(doc)
        ]

        return docs[:k]

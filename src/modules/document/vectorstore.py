import operator
import os
import shutil
import pickle
import logging
import uuid
import faiss  # type: ignore
import numpy as np
import torch
from pathlib import Path
from typing import List, Dict, Any, Optional, Sized, Tuple
from src.modules.document.typing import Document, Metadata
from src.modules.document.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class VectorStoreError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def dependable_faiss_import(no_avx2: Optional[bool] = None) -> faiss:
    """
    Import faiss if available, otherwise raise error.
    If FAISS_NO_AVX2 environment variable is set, it will be considered
    to load FAISS with no AVX2 optimization.

    Args:
        no_avx2: Load FAISS strictly with no AVX2 optimization
        so that the vectorstore is portable and compatible with other devices.
    """
    if no_avx2 is None and "FAISS_NO_AVX2" in os.environ:
        no_avx2 = bool(os.getenv("FAISS_NO_AVX2"))

    try:
        if no_avx2:
            from faiss import swigfaiss as faiss  # type: ignore
        else:
            import faiss  # type: ignore
    except ImportError:
        raise ImportError(
            "Could not import faiss python package. "
            "Please install it with `pip install faiss-gpu` (for CUDA supported GPU) "
            "or `pip install faiss-cpu` (depending on Python version)."
        )

    # Adding an attribute to mark CPU or CUDA
    faiss.device = torch.device("cpu")
    return faiss


def _len_check_if_sized(x: Any, y: Any, x_name: str, y_name: str) -> None:
    if isinstance(x, Sized) and isinstance(y, Sized) and len(x) != len(y):
        raise ValueError(
            f"{x_name} and {y_name} expected to be equal length but "
            f"len({x_name})={len(x)} and len({y_name})={len(y)}"
        )


class VectorStore:
    def __init__(self, folder_path: str, embedding_model_name: str, query_instruction: str, device: str):
        self.logger = logger

        self._faiss_cuda = False

        # Check if FAISS is CUDA or CPU
        try:
            res = faiss.StandardGpuResources()  # this will succeed if CUDA is available
            self._faiss_cuda = True
            self.logger.info("FAISS is using CUDA.")
        except AttributeError:
            self._faiss_cuda = False
            self.logger.info("FAISS is using CPU.")

        self.device = torch.device(
            'cuda' if torch.cuda.is_available() and self._faiss_cuda else 'cpu')

        self.cpu_index = None  # Cache for CPU index
        self.cuda_index = None  # Cache for CUDA index

        self.embedding = HuggingFaceEmbeddings(
            model_name=embedding_model_name,
            device=device,
            query_instruction=query_instruction
        )

        self.folder_path = folder_path

        self.docstore: Dict[str, Document] = {}
        self.index_to_docstore_id = {}
        self.gpu_resources = None
        self.index = self._load_or_create_index()

    def evaluate_text_relevance(self, text1: str, text2: str) -> float:
        """
        Evaluates the relevance between two texts using the vector store's embedding model.

        Args:
            text1 (str): The first text to compare.
            text2 (str): The second text to compare.

        Returns:
            float: A relevance score between 0 and 1, where 1 indicates high relevance and 0 indicates low relevance.
        """
        # Generate embeddings for both texts
        embedding1 = self.embedding._embed_texts([text1])[0]
        embedding2 = self.embedding._embed_texts([text2])[0]

        # Calculate cosine similarity
        similarity = self._cosine_similarity(embedding1, embedding2)

        return similarity

    def _load_or_create_index(self, index_name: str = "index"):
        path = Path(self.folder_path)
        faiss = dependable_faiss_import()

        _faiss_index_path = str(path / f"{index_name}.faiss")
        _index_path = str(path / f"{index_name}.pkl")

        if os.path.exists(_faiss_index_path) and os.path.exists(_index_path):
            index_cpu = faiss.read_index(_faiss_index_path)
            with open(_index_path, "rb") as f:
                self.docstore, self.index_to_docstore_id = pickle.load(f)
        else:
            d = self.embedding.model.get_sentence_embedding_dimension()
            index_cpu = faiss.IndexFlatL2(d)
            self.docstore = {}
            self.index_to_docstore_id = {}

        self.cpu_index = index_cpu
        # Ensure the initial device is marked as CPU
        faiss.device = torch.device("cpu")

        if self.device == "cuda":
            self.gpu_resources = faiss.StandardGpuResources()
            self.logger.info("Loaded index to CUDA.")
            self.cuda_index = faiss.index_cpu_to_gpu(
                self.gpu_resources, 0, self.cpu_index)
            faiss.device = torch.device("cuda")
            return self.cuda_index
        else:
            return self.cpu_index

    def _move_to_gpu_if_needed(self):
        if self.device == "cuda" and faiss.device == "cpu":
            self.logger.info(
                "Transferring index from CPU to CUDA for computation.")
            self.cuda_index = faiss.index_cpu_to_gpu(
                self.gpu_resources, 0, self.cpu_index)
            faiss.device = torch.device("cuda")

    def _move_to_cpu_if_needed(self):
        if self.device == "cuda" and faiss.device == "cuda":
            self.logger.info(
                "Transferring index from CUDA to CPU for computation.")
            self.cpu_index = faiss.index_gpu_to_cpu(self.cuda_index)
            faiss.device = torch.device("cpu")

    def save_index(self, index_name: str = "index"):
        self.logger.info(f"Saving index {index_name}.")
        path = Path(self.folder_path)
        path.mkdir(exist_ok=True, parents=True)

        backup_faiss_path = path / f"{index_name}_backup.faiss"
        backup_pkl_path = path / f"{index_name}_backup.pkl"
        original_faiss_path = path / f"{index_name}.faiss"
        original_pkl_path = path / f"{index_name}.pkl"

        try:
            if original_faiss_path.exists():
                shutil.copyfile(original_faiss_path, backup_faiss_path)
            if original_pkl_path.exists():
                shutil.copyfile(original_pkl_path, backup_pkl_path)

            index_to_save = self.index
            if self.device == "cuda":
                self.logger.info(
                    "Transferring index from CUDA to CPU for saving.")
                index_to_save = faiss.index_gpu_to_cpu(self.index)
                torch.cuda.synchronize()  # Ensure all CUDA operations are complete

            faiss.write_index(index_to_save, str(original_faiss_path))
            with open(original_pkl_path, "wb") as f:
                pickle.dump((self.docstore, self.index_to_docstore_id), f)
        except Exception as e:
            self.logger.error(
                f"Save operation failed: {e}, attempting to restore from backup.")
            if backup_faiss_path.exists():
                shutil.copyfile(backup_faiss_path, original_faiss_path)
            if backup_pkl_path.exists():
                shutil.copyfile(backup_pkl_path, original_pkl_path)
            self.logger.info("Restored data from backup.")
            raise
        finally:
            if backup_faiss_path.exists():
                backup_faiss_path.unlink()
            if backup_pkl_path.exists():
                backup_pkl_path.unlink()

        self.logger.info(
            f"Save operation for {index_name} completed successfully.")

    def remove_documents_by_id(self, target_id_list: Optional[List[str]]) -> List[Document]:
        if target_id_list is None:
            self.docstore = {}
            self.index_to_docstore_id = {}
            n_removed = self.index.ntotal
            self.index.reset()
            return n_removed, n_removed

        set_ids = set(target_id_list)
        if len(set_ids) != len(target_id_list):
            raise VectorStoreError(
                "Duplicate ids in the list of ids to remove.")

        index_ids = [
            i_id
            for i_id, d_id in self.index_to_docstore_id.items()
            if d_id in target_id_list
        ]
        n_removed = len(index_ids)
        removed_documents = [self.docstore[d_id]
                             for d_id in target_id_list if d_id in self.docstore]

        if self.device == "cuda":
            index_cpu = faiss.index_gpu_to_cpu(self.index)
            index_cpu.remove_ids(np.array(index_ids, dtype=np.int64))
            self.index = faiss.index_cpu_to_gpu(
                self.gpu_resources, 0, index_cpu)
            torch.cuda.synchronize()
        else:
            self.index.remove_ids(np.array(index_ids, dtype=np.int64))

        for i_id, d_id in zip(index_ids, target_id_list):
            del self.docstore[d_id]
            del self.index_to_docstore_id[i_id]

        # Rebuild the index_to_docstore_id mapping
        self.index_to_docstore_id = {
            i: doc_id for i, doc_id in enumerate(self.index_to_docstore_id.values())
        }

        self.rebuild_index()  # Trigger rebuild after deletion
        return removed_documents

    def rebuild_index(self):
        try:
            faiss = dependable_faiss_import()
            d = self.embedding.model.get_sentence_embedding_dimension()
            new_index_cpu = faiss.IndexFlatL2(d)

            all_docs = list(self.docstore.values())
            all_ids = list(self.docstore.keys())

            self.logger.info(
                f"Starting to rebuild index with {len(all_docs)} documents.")

            new_docstore = {}
            new_index_to_docstore_id = {}

            for i, doc in enumerate(all_docs):
                embeddings = self.embedding._embed_texts([doc.page_content])
                embeddings = np.array(embeddings, dtype=np.float32)

                new_index_cpu.add(embeddings)
                new_docstore[all_ids[i]] = doc
                new_index_to_docstore_id[i] = all_ids[i]

                if i % 100 == 0:
                    self.logger.info(
                        f"Processed {i}/{len(all_docs)} documents.")

            self.docstore = new_docstore
            self.index_to_docstore_id = new_index_to_docstore_id

            if self.device == "cuda":
                if not self.gpu_resources:
                    self.gpu_resources = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(
                    self.gpu_resources, 0, new_index_cpu)
                torch.cuda.synchronize()
            else:
                self.index = new_index_cpu

            self.logger.info(
                "Index has been successfully rebuilt and reloaded.")
        except Exception as e:
            self.logger.error(f"Error during index rebuild: {e}")
            raise

    def delete_documents_by_ids(self, target_ids: List[int]) -> List[Document]:
        if target_ids is None or len(target_ids) < 1:
            raise ValueError("Parameter target_ids cannot be empty.")

        id_to_remove = []
        for _id, doc in self.docstore.items():
            to_remove = False
            if doc.metadata.get_ids() in target_ids:
                to_remove = True
            if to_remove:
                id_to_remove.append(_id)
        return self.remove_documents_by_id(id_to_remove)

    def _cosine_similarity(self, doc1_embedding: np.ndarray, doc2_embedding: np.ndarray) -> float:
        return np.dot(doc1_embedding, doc2_embedding) / (np.linalg.norm(doc1_embedding) * np.linalg.norm(doc2_embedding))

    def add_documents(
        self,
        docs: List[Document],
        ids: Optional[List[str]] = None,
        similarity_threshold: float = 0.9
    ) -> List[Document]:
        embeds = self.embedding._embed_texts(
            [doc.page_content for doc in docs]
        )

        embeds = np.asarray(embeds, dtype=np.float32)
        ids = ids or [str(uuid.uuid4()) for _ in docs]

        _len_check_if_sized(embeds, docs, 'embeds', 'docs')
        _len_check_if_sized(ids, docs, 'ids', 'docs')

        added_docs = []

        for i, doc in enumerate(docs):
            embed = embeds[i]

            similar_docs = self.similarity_search_with_score_by_vector(
                embedding=embed,
                k=2
            )

            is_duplicate = False
            for similar_doc, score in similar_docs:
                similar_embed = self.embedding._embed_texts(
                    [similar_doc.page_content])[0]
                cosine_similarity = self._cosine_similarity(
                    embed, similar_embed)
                if cosine_similarity > similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                self._move_to_gpu_if_needed()
                self.index.add(np.array([embed], dtype=np.float32))

                doc_id = ids[i]
                self.docstore[doc_id] = doc
                self.index_to_docstore_id[len(
                    self.index_to_docstore_id)] = doc_id
                added_docs.append(doc)

        return added_docs

    def similarity_search_with_score_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        fetch_k: int = 20,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:

        vector = np.array([embedding], dtype=np.float32)
        scores, indices = self.index.search(
            vector, k if filter is None else fetch_k)
        docs = []
        for j, i in enumerate(indices[0]):
            if i == -1:  # This happens when not enough docs are returned.
                continue
            _id = self.index_to_docstore_id[i]
            doc = self.docstore.get(_id)
            if not isinstance(doc, Document):
                raise VectorStoreError(
                    f"Could not find document for id {_id}, got {doc}")
            if filter is not None:
                filter = {
                    key: [value] if not isinstance(value, list) else value
                    for key, value in filter.items()
                }
                if all(doc.metadata.to_dict().get(key) in value for key, value in filter.items()):
                    docs.append((doc, scores[0][j]))
            else:
                docs.append((doc, scores[0][j]))

        score_threshold = kwargs.get("score_threshold")
        if score_threshold is not None:
            cmp = (operator.le)
            docs = [
                (doc, similarity)
                for doc, similarity in docs
                if cmp(similarity, score_threshold)
            ]
        return docs[:k]

    def search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Metadata] = None,
        fetch_k: int = 20,
        **kwargs: Any
    ) -> List[Document]:

        if filter is not None:
            powerset = kwargs.get("powerset", True)
            filter = filter.to_filter(powerset)

        score_threshold = kwargs.get("score_threshold")
        threshold_offset = 0.01
        if score_threshold is not None:
            kwargs.update(
                {"score_threshold": score_threshold + threshold_offset})

        embeddings = self.embedding._embed_texts([query])
        docs_and_scores = self.similarity_search_with_score_by_vector(
            embeddings[0],
            k,
            filter=filter,
            fetch_k=fetch_k,
            **kwargs,
        )

        vd_docs = [doc for doc, _ in docs_and_scores if doc.is_valid()]

        return vd_docs[:k]

    def get_all_documents(self) -> List[Document]:
        """
            Returns a list of all Document instances stored in the VectorStore.
        """
        return list(self.docstore.values())

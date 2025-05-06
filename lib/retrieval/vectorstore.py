import operator
import torch
import os
import shutil
import pickle
import queue
import threading
import logging
import uuid
import faiss
import numpy as np
import torch.nn.functional as F
from pathlib import Path
from typing import List, Dict, Any, Optional, Sized, Tuple
from concurrent.futures import ThreadPoolExecutor


from lib.retrieval.schemas import Document, MetadataFilter
from lib.retrieval.embeddings import HuggingFaceEmbeddings

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
            from faiss import swigfaiss as faiss
        else:
            import faiss
    except ImportError:
        raise ImportError(
            "Could not import faiss python package. "
            "Please install it with `pip install faiss-gpu` (for CUDA supported GPU) "
            "or `pip install faiss-cpu` (depending on Python version)."
        )
    return faiss


def _len_check_if_sized(x: Any, y: Any, x_name: str, y_name: str) -> None:
    if isinstance(x, Sized) and isinstance(y, Sized) and len(x) != len(y):
        raise ValueError(
            f"{x_name} and {y_name} expected to be equal length but "
            f"len({x_name})={len(x)} and len({y_name})={len(y)}"
        )
    return


class VectorStore:
    def __init__(
        self,
        folder_path: str,
        model_name: str = "moka-ai/m3e-base",
        query_instruction: str = "为这个句子生成表示以用于检索相关文章：",
        device: str = "cpu",
    ):
        """
        Initializes the VectorStore with the specified folder path for saving indices,
        the name of the embedding model, and the computing device.

        Args:
            folder_path: Path to save/load index files
            model_name: Name of the embedding model to use
            query_instruction: Instruction for embedding model when processing queries
            device: Computing device (cpu or cuda)
        """
        self.device = device
        self.embedding = HuggingFaceEmbeddings(
            model_name=model_name,
            device=self.device,
            query_instruction=query_instruction,
        )

        self.folder_path = folder_path

        # Initialize a thread-safe queue for save tasks and a lock to ensure exclusive access.
        self.save_tasks = queue.Queue()
        self.save_thread = threading.Thread(target=self._save_worker)
        self.save_thread.daemon = True
        self.save_thread.start()

        # Initialize docstore and index to document ID mapping.
        self.docstore: Dict[str, Document] = {}
        self.index_to_docstore_id = {}
        self.gpu_resources = None
        self._lock = threading.Lock()
        self.index = self._load_or_create_index()

    def _load_or_create_index(self, index_name: str = "index"):
        path = Path(self.folder_path)
        faiss = dependable_faiss_import()

        _faiss_index_path = str(path / f"{index_name}.faiss")
        _index_path = str(path / f"{index_name}.pkl")

        with self._lock:
            if os.path.exists(_faiss_index_path) and os.path.exists(_index_path):
                index_cpu = faiss.read_index(_faiss_index_path)
                with open(_index_path, "rb") as f:
                    self.docstore, self.index_to_docstore_id = pickle.load(f)
            else:
                d = self.embedding.model.get_sentence_embedding_dimension()
                index_cpu = faiss.IndexFlatL2(d)
                self.docstore = {}
                self.index_to_docstore_id = {}

            if self.device == "cuda":
                self.gpu_resources = faiss.StandardGpuResources()
                logger.info("Loaded index to GPU.")
                return faiss.index_cpu_to_gpu(self.gpu_resources, 0, index_cpu)
            else:
                return index_cpu

    def _save_worker(self):
        """
        Worker thread that processes save tasks from the queue. It runs indefinitely
        and processes each task by calling the _perform_save method.
        """
        while True:
            task = self.save_tasks.get()
            if task is None:  # Use None as a signal to stop the worker.
                break
            self._perform_save(task)
            self.save_tasks.task_done()

    def _perform_save(self, index_name: str):
        """
        Performs the actual save operation for the index and docstore.
        This method is called by the worker thread.
        If the index is on GPU, it transfers it to CPU before saving.
        Before saving, creates backups of existing data. If the save fails,
        restores from the backups.
        """
        logger.info(f"Performing save operation for {index_name}.")
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

            self.rebuild_index()

            index_to_save = self.index
            if self.device == "cuda":
                logger.info("Transferring index from GPU to CPU for saving.")
                index_to_save = faiss.index_gpu_to_cpu(self.index)
                torch.cuda.synchronize()  # Ensure all CUDA operations are complete

            faiss.write_index(index_to_save, str(original_faiss_path))
            with open(original_pkl_path, "wb") as f:
                pickle.dump((self.docstore, self.index_to_docstore_id), f)
        except Exception as e:
            logger.error(
                f"Save operation failed: {e}, attempting to restore from backup."
            )
            if backup_faiss_path.exists():
                shutil.copyfile(backup_faiss_path, original_faiss_path)
            if backup_pkl_path.exists():
                shutil.copyfile(backup_pkl_path, original_pkl_path)
            logger.info("Restored data from backup.")
            raise
        finally:
            if backup_faiss_path.exists():
                backup_faiss_path.unlink()
            if backup_pkl_path.exists():
                backup_pkl_path.unlink()

        logger.info(f"Save operation for {index_name} completed successfully.")

    def save_index(self, index_name: str = "index"):
        """
        Queues a save task for the specified index. If a save operation is already in progress,
        the task will wait in the queue until it's processed by the worker thread.
        """
        logger.info(f"Queueing save operation for {index_name}.")
        self.save_tasks.put(index_name)

    def rebuild_index(self):
        """
        Rebuilds the FAISS index based on the current state of the docstore. This is useful if the
        embedding model has changed or if the index has become corrupted or out-of-sync with the docstore.
        """
        self._lock.acquire()
        try:
            faiss = dependable_faiss_import()
            d = self.embedding.model.get_sentence_embedding_dimension()
            new_index_cpu = faiss.IndexFlatL2(d)

            all_docs = list(self.docstore.values())
            all_ids = list(self.docstore.keys())

            if not all_docs:
                self.index = new_index_cpu
                self.index_to_docstore_id = {}
                self._lock.release()
                return

            def embed_docs(docs: list[Document]):
                return np.array(
                    self.embedding._embed_texts([doc.content for doc in docs]),
                    dtype=np.float32,
                )

            num_threads = 12
            chunk_size = max(1, len(all_docs) // num_threads)
            chunks = [
                all_docs[i : i + chunk_size]
                for i in range(0, len(all_docs), chunk_size)
            ]
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                results = executor.map(embed_docs, chunks)
            embeddings = np.concatenate(list(results))

            def rebuild():
                try:
                    new_index_cpu.add(embeddings)
                    self.index_to_docstore_id = {
                        i: doc_id for i, doc_id in enumerate(all_ids)
                    }

                    if self.device == "cuda":
                        if not self.gpu_resources:
                            self.gpu_resources = faiss.StandardGpuResources()
                        self.index = faiss.index_cpu_to_gpu(
                            self.gpu_resources, 0, new_index_cpu
                        )
                        torch.cuda.synchronize()
                    else:
                        self.index = new_index_cpu

                    logger.info("Index has been successfully rebuilt and reloaded.")
                except Exception as e:
                    logger.error(f"Error during index rebuild: {e}")
                    raise
                finally:
                    self._lock.release()

            threading.Thread(target=rebuild).start()
        except Exception as e:
            self._lock.release()
            logger.error(f"Error initiating index rebuild: {e}")
            raise

    def remove_documents_by_id(
        self, target_id_list: Optional[List[str]]
    ) -> List[Document]:
        if target_id_list is None:
            self.docstore = {}
            self.index_to_docstore_id = {}
            n_removed = self.index.ntotal
            n_total = self.index.ntotal
            self.index.reset()
            return n_removed, n_total
        set_ids = set(target_id_list)
        if len(set_ids) != len(target_id_list):
            raise VectorStoreError("Duplicate ids in the list of ids to remove.")
        index_ids = [
            i_id
            for i_id, d_id in self.index_to_docstore_id.items()
            if d_id in target_id_list
        ]
        n_removed = len(index_ids)
        n_total = self.index.ntotal
        removed_documents = [
            self.docstore[d_id] for d_id in target_id_list if d_id in self.docstore
        ]

        if self.device == "cuda":
            index_cpu = faiss.index_gpu_to_cpu(self.index)
            index_cpu.remove_ids(np.array(index_ids, dtype=np.int64))
            self.index = faiss.index_cpu_to_gpu(self.gpu_resources, 0, index_cpu)
            torch.cuda.synchronize()
        else:
            self.index.remove_ids(np.array(index_ids, dtype=np.int64))

        for i_id, d_id in zip(index_ids, target_id_list):
            del self.docstore[d_id]
            del self.index_to_docstore_id[i_id]
        self.index_to_docstore_id = {
            i: d_id for i, d_id in enumerate(self.index_to_docstore_id.values())
        }
        return removed_documents

    def delete_documents_by_id(self, target_id: List[int]) -> List[Document]:
        if target_id is None or len(target_id) < 1:
            raise ValueError("Parameter target_ids cannot be empty.")

        id_to_remove = []
        for _id, doc in self.docstore.items():
            to_remove = False
            if doc.metadata.id in target_id:
                to_remove = True
            if to_remove:
                id_to_remove.append(_id)
        return self.remove_documents_by_id(id_to_remove)

    def _cosine_similarity(
        self, doc1_embedding: np.ndarray, doc2_embedding: np.ndarray
    ) -> float:
        doc1_embedding = torch.tensor(doc1_embedding, dtype=torch.float32)
        doc2_embedding = torch.tensor(doc2_embedding, dtype=torch.float32)
        cos_sim = F.cosine_similarity(
            doc1_embedding.unsqueeze(0), doc2_embedding.unsqueeze(0)
        )
        return cos_sim.item()

    def add_documents(
        self,
        docs: List[Document],
        id: Optional[List[str]] = None,
        similarity_threshold: float = 0.9,
    ) -> List[Document]:
        embeds = self.embedding._embed_texts([doc.content for doc in docs])

        embeds = np.asarray(embeds, dtype=np.float32)
        id = id or [str(uuid.uuid4()) for _ in docs]

        _len_check_if_sized(embeds, docs, "embeds", "docs")
        _len_check_if_sized(id, docs, "id", "docs")

        added_docs = []

        for i, doc in enumerate(docs):
            embed = embeds[i]

            similar_docs = self.similarity_search_with_score_by_vector(
                embedding=embed, k=2
            )

            is_duplicate = False
            for similar_doc, score in similar_docs:
                similar_embed = self.embedding._embed_texts([similar_doc.content])[0]
                cosine_similarity = self._cosine_similarity(embed, similar_embed)
                if cosine_similarity > similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                with self._lock:
                    if self.device == "cuda":
                        index_cpu = faiss.index_gpu_to_cpu(self.index)
                        index_cpu.add(np.array([embed], dtype=np.float32))
                        self.index = faiss.index_cpu_to_gpu(
                            self.gpu_resources, 0, index_cpu
                        )
                        torch.cuda.synchronize()
                    else:
                        self.index.add(np.array([embed], dtype=np.float32))

                    doc_id = id[i]
                    self.docstore[doc_id] = doc
                    self.index_to_docstore_id[len(self.index_to_docstore_id)] = doc_id
                    added_docs.append(doc)

        return added_docs

    def similarity_search_with_score_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        vector = np.array([embedding], dtype=np.float32)
        scores, indices = self.index.search(vector, k)
        docs = []

        for j, i in enumerate(indices[0]):
            if i == -1:
                # This happens when not enough docs are returned.
                continue
            _id = self.index_to_docstore_id[i]
            doc = self.docstore.get(_id)
            if not isinstance(doc, Document):
                raise VectorStoreError(
                    f"Could not find document for id {_id}, got {doc}"
                )
            docs.append((doc, scores[0][j]))

        score_threshold = kwargs.get("score_threshold")
        if score_threshold is not None:
            cmp = operator.le
            docs = [
                (doc, similarity)
                for doc, similarity in docs
                if cmp(similarity, score_threshold)
            ]
        return docs[:k]

    def search(
        self, query, k=5, metadata_filter: Optional[MetadataFilter] = None, **kwargs
    ) -> List[Document]:
        """
        Search for documents similar to the query.

        Args:
            query: The search query.
            k: Number of results to return.
            metadata_filter: Optional filter to apply to document metadata.
            **kwargs: Additional arguments.
                score_threshold: Optional float. If provided, only return documents with a similarity score
                                less than or equal to this threshold (lower is better for L2 distance).

        Returns:
            List[Document]: List of documents matching the query.
        """
        if self.index.ntotal == 0:
            return []

        embeddings = self.embedding._embed_texts([query])

        fetch_k = k * 4 if metadata_filter else k
        fetch_k = min(fetch_k, self.index.ntotal, 100)
        if fetch_k <= 0:
            return []

        docs_and_scores = self.similarity_search_with_score_by_vector(
            embeddings[0],
            fetch_k,
            **kwargs,
        )

        vd_docs = [doc for doc, _ in docs_and_scores if doc.is_valid]

        if metadata_filter:
            logger.info(f"Applying metadata filter to {len(vd_docs)} valid documents")
            filtered_docs = [
                doc for doc in vd_docs if metadata_filter.match(doc.metadata)
            ]
            logger.info(
                f"Found {len(filtered_docs)} documents matching filter criteria"
            )
            return filtered_docs[:k]

        return vd_docs[:k]

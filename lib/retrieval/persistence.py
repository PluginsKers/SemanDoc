import threading
import time
import logging
from typing import Optional

from lib.retrieval.vectorstore import VectorStore

logger = logging.getLogger(__name__)

class PersistenceManager:
    
    def __init__(
        self, 
        vector_store: VectorStore, 
        save_interval: int = 300,
        index_name: str = "index"
    ):
        self.vector_store = vector_store
        self.save_interval = save_interval
        self.index_name = index_name
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_save_time = time.time()
        
    def _persistence_worker(self):
        logger.info(f"Persistence worker started with interval: {self.save_interval}s")
        
        while not self._stop_event.is_set():
            current_time = time.time()
            time_since_last_save = current_time - self._last_save_time
            
            if time_since_last_save >= self.save_interval:
                try:
                    logger.info(f"Auto-saving vector store (interval: {self.save_interval}s)")
                    self.vector_store.save_index(self.index_name)
                    self._last_save_time = current_time
                    logger.info("Auto-save completed")
                except Exception as e:
                    logger.error(f"Error during auto-save: {e}")
            
            wait_time = min(60, self.save_interval / 10)
            self._stop_event.wait(wait_time)
    
    def start(self):
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Persistence worker is already running")
            return
            
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._persistence_worker, 
            name="VectorStorePersistenceThread",
            daemon=True
        )
        self._thread.start()
        logger.info("Started vector store persistence manager")
        
    def stop(self):
        if self._thread is None or not self._thread.is_alive():
            logger.warning("Persistence worker is not running")
            return
            
        logger.info("Stopping persistence worker...")
        self._stop_event.set()
        self._thread.join(timeout=30)
        
        if self._thread.is_alive():
            logger.warning("Persistence worker did not stop gracefully")
        else:
            logger.info("Persistence worker stopped")
            self._thread = None
    
    def force_save(self):
        try:
            logger.info("Forcing immediate save of vector store")
            self.vector_store.save_index(self.index_name)
            self._last_save_time = time.time()
            logger.info("Forced save completed")
        except Exception as e:
            logger.error(f"Error during forced save: {e}")
            raise 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import argparse
from typing import Optional
from contextlib import asynccontextmanager

from lib.retrieval.vectorstore import VectorStore
from lib.retrieval.persistence import PersistenceManager
from lib.api.document_routes import init_routes

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

persistence_manager: Optional[PersistenceManager] = None
save_interval: int = 300

vector_store = VectorStore(
    folder_path="./tmp", model_name="./models/embedders/m3e-base", device="cpu"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global persistence_manager
    logger.info("Starting up SemanDoc API")

    logger.info(
        f"Starting vector store persistence manager with interval: {save_interval}s"
    )
    persistence_manager = PersistenceManager(
        vector_store=vector_store, save_interval=save_interval, index_name="index"
    )
    persistence_manager.start()
    logger.info("Vector store persistence manager started")

    yield

    # Shutdown
    logger.info("Shutting down SemanDoc API")

    if persistence_manager:
        try:
            logger.info("Saving vector store before shutdown")
            persistence_manager.force_save()
            logger.info("Stopping vector store persistence manager")
            persistence_manager.stop()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    else:
        logger.warning("Persistence manager was not initialized")


app = FastAPI(
    title="SemanDoc",
    description="Document retrieval and search API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

document_router = init_routes(vector_store)
app.include_router(document_router)


@app.get("/")
async def root():
    return {"message": "SemanDoc API service is running successfully!"}


def parse_args():
    global save_interval

    parser = argparse.ArgumentParser(description="SemanDoc API")
    parser.add_argument(
        "--save-interval",
        type=int,
        default=300,
        help="Vector store auto-save interval in seconds, default 300s",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Server host address, default 0.0.0.0",
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Server port, default 8000"
    )

    args = parser.parse_args()
    save_interval = args.save_interval
    return args


if __name__ == "__main__":
    args = parse_args()
    logger.info(f"Starting SemanDoc API server on {args.host}:{args.port}")
    logger.info(f"Vector store auto-save interval: {save_interval}s")
    uvicorn.run(app, host=args.host, port=args.port)

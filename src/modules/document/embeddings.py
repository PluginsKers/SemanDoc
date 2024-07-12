import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class HuggingFaceEmbeddings:
    def __init__(
        self,
        query_instruction: str,
        model_name: str = "sentence-transformers/all-mpnet-base-v2",
        device: str = "cpu",
        normalize_embeddings: bool = True
    ):
        self.device = device
        self.model = SentenceTransformer(model_name, device=device)
        self.normalize_embeddings = normalize_embeddings
        self.query_instruction = query_instruction
        logger.info(f"Embedding model initialized on device {self.device}")

    def _embed_texts(self, texts):
        embeddings = self.model.encode(
            [self.query_instruction + text for text in texts],
            convert_to_tensor=True
        )
        if self.normalize_embeddings:
            embeddings = embeddings / embeddings.norm(dim=1, keepdim=True)
        return embeddings.cpu().numpy()

from sentence_transformers import SentenceTransformer


class HuggingFaceEmbeddings:
    def __init__(
        self,
        query_instruction: str,
        model_name: str,
        device: str,
        normalize_embeddings: bool = True,
    ):
        self.model = SentenceTransformer(model_name, device=device)
        self.normalize_embeddings = normalize_embeddings
        self.query_instruction = query_instruction

    def _embed_texts(self, texts):
        embeddings = self.model.encode(
            [self.query_instruction + text for text in texts], convert_to_tensor=True
        )
        if self.normalize_embeddings:
            embeddings = embeddings / embeddings.norm(dim=1, keepdim=True)
        return embeddings.cpu().numpy()

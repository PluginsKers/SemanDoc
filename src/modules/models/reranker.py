import torch
from typing import (
    List,
    Tuple
)
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification
)

from src.modules.document import Document


class Reranker:
    def __init__(self, reranker_model_path: str, device: str = "cpu") -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(
            reranker_model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            reranker_model_path, is_decoder=True)
        self.device = device
        self.model.to(self.device)
        self.model.eval()

    def rerank_documents(self, documents: List[Document], query: str) -> List[Document]:
        if len(documents) < 2:
            return documents

        pairs: List[Tuple[str, Document]] = [[query, doc] for doc in documents]
        with torch.no_grad():
            inputs = self.tokenizer(
                [[x[0], x[1].page_content] for x in pairs], padding=True, truncation=True, return_tensors='pt', max_length=1024).to(self.device)
            scores = self.model(**inputs, return_dict=True).logits.squeeze()

        scored_pairs = [(pair, score.item())
                        for pair, score in zip(pairs, scores)]

        scored_pairs.sort(key=lambda x: x[1], reverse=True)
        return [pair[1] for pair, _ in scored_pairs]

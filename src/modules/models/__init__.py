import torch
import asyncio

from typing import List, Tuple, Union
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSequenceClassification

from src.config import BaseConfig as cfg
from src.modules.document import Document


class LLMModel:
    def __init__(self, model_name: str = "THUDM/chatglm3-6b", device: str = "cpu"):
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, trust_remote_code=True)
        self.model.to(self.device)
        self.model.eval()

    async def generate_async(self, prompt: str, history: list = []) -> str:
        loop = asyncio.get_event_loop()
        response, history = await loop.run_in_executor(None, self.chat, prompt, history)
        return response

    def chat(self, prompt: str, history: list = []) -> str:
        response, history = self.model.chat(
            self.tokenizer, prompt, history=history)
        return response

    def get_response_by_tools(self, message: str) -> Union[str, dict]:
        tools = cfg.GLM_TOOLS
        system_info = {
            "role": "system", "content": cfg.GLM_TOOLS_PROMPT, "tools": tools}
        history = [system_info]
        response = self.chat(message, history)
        return response

    def get_response(self, message: str, history: list = []):
        prompt = cfg.LLM_CHAT_PROMPT.format(message)
        return self.chat(prompt, history)


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
                [[x[0], x[1].page_content] for x in pairs], padding=True, truncation=True, return_tensors='pt', max_length=512).to(self.device)
            scores = self.model(**inputs, return_dict=True).logits.squeeze()

        scored_pairs = [(pair, score.item())
                        for pair, score in zip(pairs, scores)]

        scored_pairs.sort(key=lambda x: x[1], reverse=True)
        return [pair[1] for pair, _ in scored_pairs]

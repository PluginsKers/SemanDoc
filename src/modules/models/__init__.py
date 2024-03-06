import torch
import asyncio

from typing import List, Tuple
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSequenceClassification

from src.modules.document import Document

from .prompt_manager import PromptManager


class LLMModel:
    def __init__(self, model_name: str = "THUDM/chatglm3-6b", device: str = "cpu"):
        self.session_meta = {'user_info': '我是小明，是一个男性，是一位有特点的大学生，经常会使用一些网络词语和小宁交流，虽然助手小宁有时不懂其含义，但是还是会尽力为我解答。',
                             'bot_info': '小宁，一个大学知识库的管理助手，勤奋敬业。对于自己不知道答案的问题不会轻易解答，但凡有一点错误都会很自责，所以深受同学和教职工们的爱戴。',
                             'bot_name': '小宁',
                             'user_name': '小明'
                             }
        self.device = device
        self.prompt_manager = PromptManager()
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, trust_remote_code=True)
        self.model.to(self.device)
        self.model.eval()

    async def generate_async(self, prompt, history=[]) -> str:
        loop = asyncio.get_event_loop()
        response, history = await loop.run_in_executor(None, self.generate, prompt, history)
        return response

    def generate(self, prompt, history=[]) -> str:
        response, history = self.model.chat(
            self.tokenizer, prompt, history=history)
        return response


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
        if len(documents) == 0:
            return []

        pairs: List[Tuple[str, Document]] = [[query, doc] for doc in documents]
        with torch.no_grad():
            inputs = self.tokenizer(
                [[x[0], x[1].page_content] for x in pairs], padding=True, truncation=True, return_tensors='pt', max_length=512).to(self.device)
            scores = self.model(**inputs, return_dict=True).logits.squeeze()

        scored_pairs = [(pair, score.item())
                        for pair, score in zip(pairs, scores)]

        scored_pairs.sort(key=lambda x: x[1], reverse=True)
        return [pair[1] for pair, _ in scored_pairs]

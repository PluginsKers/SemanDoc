from typing import List
from transformers import AutoTokenizer, AutoModelForCausalLM
import asyncio

from .prompt_manager import PromptManager


class LLMModel:
    def __init__(self, model_name: str = "THUDM/chatglm3-6b", device: str = "cpu"):
        self.device = device
        self.prompt_manager = PromptManager()
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, trust_remote_code=True)
        self.model.to(self.device)
        self.model.eval()

    async def generate_async(self, prompt, history=[]):
        loop = asyncio.get_event_loop()
        response, history = await loop.run_in_executor(None, self.generate, prompt, history)
        return response, history

    def generate(self, prompt, history=[]) -> str:
        response, history = self.model.chat(
            self.tokenizer, prompt, history=history)
        return response

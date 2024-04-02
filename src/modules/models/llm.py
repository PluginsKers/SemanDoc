import asyncio
import json
from typing import Dict, Optional, Union
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM
)


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

    def get_response_by_tools(self, query: str, prompt: str, tools: dict) -> Union[str, dict]:
        if tools is None and prompt is None:
            raise ValueError("Tools or prompt for GLM tools is not provided.")

        system_info = {
            "role": "system", "content": prompt, "tools": tools}
        history = [system_info]
        response = self.chat(query, history)
        return response

    def get_response(self, message: str, prompt: str, history: list = []):
        prompt = prompt.format(message)
        return self.chat(prompt, history)

    def predict_intent(self, query: str, prompt: str, tools: dict) -> Optional[str]:
        response = self.get_response_by_tools(query, prompt, tools)
        if isinstance(response, dict):
            if response.get("name") == "predict_intent" and "parameters" in response:
                # Extract the classification symbol if present
                if isinstance(response["parameters"], dict) and "symbol" in response["parameters"]:
                    classification = response["parameters"].get("symbol")
                    return classification

        return None

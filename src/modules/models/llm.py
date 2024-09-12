import asyncio
import json
from typing import Annotated, Dict, Optional, Union
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM
)

from src.modules.models.tools_manager import ToolsManager


class LLM:
    def __init__(self, model_name: str, device: str = "cpu"):
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

    def get_response(self, message: str, prompt: str, history: list = []):
        prompt = prompt.format(message)
        return self.chat(prompt, history)

    def get_response_by_tools(self, query: str, prompt: str) -> Union[str, dict]:
        system_info = {
            "role": "system", "content": prompt, "tools": self.tools_manager.get_tools()}
        history = [system_info]
        response = self.chat(query, history)
        return response

    # 注意：此方法已弃用
    def predict_intent(self, query: str, prompt: str) -> Optional[str]:
        # 此方法已不再使用，保留此代码仅供参考
        response = self.get_response_by_tools(query, prompt)
        if isinstance(response, dict):
            tool_observation = self.tools_manager.dispatch_tool(
                response.get("name"), response.get("parameters"))
            return tool_observation[0].text

        return None

import numpy as np
import torch
from torch import cosine_similarity
from src.modules.document.embeddings import HuggingFaceEmbeddings


class IntentClassifier:
    def __init__(
        self,
        query_instruction: str,
        model_name: str,
        device: str
    ):
        self.embedding = HuggingFaceEmbeddings(
            model_name=model_name,
            device=device,
            query_instruction=query_instruction
        )
        self.intents = {
            "位置信息": "与位置或地点相关的问题，例如询问地址、城市的信息。",
            "联系方式": "涉及联系方式的提问，例如电话号码、电子邮件地址等。"
        }
        self.intent_embeddings = self.embedding._embed_texts(
            list(self.intents.values()))

    def classify_intent(self, user_input):
        user_embedding = self.embedding._embed_texts([user_input])[0]
        user_embedding_tensor = torch.tensor(user_embedding).unsqueeze(0)
        intent_embeddings_tensor = torch.tensor(self.intent_embeddings)
        
        # 确保计算结果是一个向量
        similarities = cosine_similarity(
            user_embedding_tensor, intent_embeddings_tensor, dim=1).squeeze()
        
        # 如果只有一个意图，similarities 将是一个标量，我们需要特殊处理
        if similarities.dim() == 0:
            best_intent_index = 0
            best_similarity = similarities.item()
        else:
            sorted_similarities, sorted_indices = torch.sort(similarities, descending=True)
            best_intent_index = sorted_indices[0].item()
            best_similarity = sorted_similarities[0].item()
            
            # 检查最高相似度是否超过第二高相似度的80%
            if len(sorted_similarities) > 1:
                second_best_similarity = sorted_similarities[1].item()
                if best_similarity < second_best_similarity * 1.8:
                    return None, 0  # 没有明显优势的分类
        
        best_intent = list(self.intents.keys())[best_intent_index]
        return best_intent, best_similarity

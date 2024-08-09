import numpy as np
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
        intents = {
            "位置信息": "与位置或地点相关的问题，例如询问地址、城市的信息。",
            "联系方式": "涉及联系方式的提问，例如电话号码、电子邮件地址等。",
            "其他": "与其他类别不符的各种问题或信息请求。",
        }
        self.intent_embeddings = self.embedding._embed_texts(
            list(intents.values()))

    def classify_intent(self, user_input):
        user_embedding = self.embedding._embed_texts([user_input])[0]
        similarities = cosine_similarity(
            [user_embedding], self.intent_embeddings)[0]
        best_intent_index = np.argmax(similarities)
        best_intent = list(self.intents.keys())[best_intent_index]
        return best_intent, similarities[best_intent_index]

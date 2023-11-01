import logging
from transformers import AutoModel, AutoTokenizer
import torch


class EmbeddingModelManager:
    def __init__(self, pretrained_model_name_or_path: str):
        self.model = AutoModel.from_pretrained(pretrained_model_name_or_path)
        self.tokenizer = AutoTokenizer.from_pretrained(
            pretrained_model_name_or_path
        )
        self.model.eval()
        self.logger = self.setup_logger()

    def setup_logger(self):
        """
        Sets up the logging configuration.
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def get_embedding(self, text):
        input_ids = self.tokenizer(text, return_tensors="pt")["input_ids"]
        with torch.no_grad():
            outputs = self.model(input_ids)
        return outputs[0][0][0].numpy()

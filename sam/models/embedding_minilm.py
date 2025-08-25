from .embedding_adapter import EmbeddingAdapter
from transformers import AutoTokenizer, AutoModel
import torch


class MiniLMAdapter(EmbeddingAdapter):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str | None = None):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device).eval()

    @torch.no_grad()
    def embed(self, texts: list[str]) -> list[list[float]]:
        inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt").to(self.device)
        model_out = self.model(**inputs)
        # mean pooling
        token_embeddings = model_out.last_hidden_state
        attention_mask = inputs["attention_mask"].unsqueeze(-1)
        masked = token_embeddings * attention_mask
        sum_emb = masked.sum(dim=1)
        lengths = attention_mask.sum(dim=1).clamp(min=1)
        embs = (sum_emb / lengths).cpu().float().tolist()
        return embs

    @property
    def dimension(self) -> int:
        return 384
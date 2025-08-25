from typing import Optional
from .embedding_adapters import EmbeddingAdapter
from .embedding_minilm import MiniLMAdapter


class EmbeddingAdapterManager:
    """Manages embedding adapters with dimension validation."""
    
    def __init__(self, cfg):
        self.cfg = cfg
        self._adapter: Optional[EmbeddingAdapter] = None
    
    def get_adapter(self) -> EmbeddingAdapter:
        """Get or create the embedding adapter."""
        if self._adapter is None:
            self._adapter = MiniLMAdapter(self.cfg.embedding.model)
            
            # Validate dimension
            if self._adapter.dimension != self.cfg.embedding.dimension:
                raise ValueError(
                    f"Embedding adapter dimension {self._adapter.dimension} "
                    f"does not match config dimension {self.cfg.embedding.dimension}"
                )
        
        return self._adapter
    
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts."""
        adapter = self.get_adapter()
        return adapter.embed(texts)
    
    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        adapter = self.get_adapter()
        return adapter.dimension
"""
Embedding Adapters - Pluggable embedding model adapters.

Provides unified interface for different embedding models with
batch processing and caching capabilities.
"""

from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

from ..utils.logging import get_logger


class EmbeddingAdapter(ABC):
    """
    Abstract base class for embedding adapters.
    
    Provides unified interface for different embedding models with
    batch processing and caching capabilities.
    """
    
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        pass
    
    @abstractmethod
    def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        pass


class SentenceTransformerAdapter(EmbeddingAdapter):
    """Sentence Transformers adapter."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", **kwargs):
        """Initialize Sentence Transformers adapter."""
        self.logger = get_logger(__name__)
        self.model_name = model_name
        # TODO: Implement model loading
        self.dimension = 384  # Default for all-MiniLM-L6-v2
        self.logger.info("Sentence Transformers adapter initialized", model_name=model_name)
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        # TODO: Implement batch embedding
        return [[0.1] * self.dimension for _ in texts]
    
    def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        # TODO: Implement single embedding
        return [0.1] * self.dimension
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            "type": "sentence_transformers",
            "model_name": self.model_name,
            "dimension": self.dimension,
            "status": "initialized"
        }


class EmbeddingAdapterManager:
    """
    Embedding Adapter Manager - Manages embedding adapters.
    
    Provides unified interface and caching for embedding operations.
    """
    
    def __init__(self, default_adapter: Optional[EmbeddingAdapter] = None):
        """Initialize embedding adapter manager."""
        self.logger = get_logger(__name__)
        self.default_adapter = default_adapter
        self.cache: Dict[str, List[float]] = {}
        self.logger.info("Embedding Adapter Manager initialized")
    
    def set_default_adapter(self, adapter: EmbeddingAdapter) -> None:
        """Set default embedding adapter."""
        self.default_adapter = adapter
        self.logger.info("Default adapter set", dimension=adapter.get_dimension())
    
    def embed(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """Generate embeddings with optional caching."""
        if self.default_adapter is None:
            raise ValueError("No default adapter set")
        
        if use_cache:
            # Check cache for existing embeddings
            cached_embeddings = []
            texts_to_embed = []
            indices_to_embed = []
            
            for i, text in enumerate(texts):
                if text in self.cache:
                    cached_embeddings.append(self.cache[text])
                else:
                    texts_to_embed.append(text)
                    indices_to_embed.append(i)
            
            if texts_to_embed:
                # Generate embeddings for uncached texts
                new_embeddings = self.default_adapter.embed(texts_to_embed)
                
                # Cache new embeddings
                for text, embedding in zip(texts_to_embed, new_embeddings):
                    self.cache[text] = embedding
                
                # Combine cached and new embeddings
                result = [None] * len(texts)
                for i, embedding in zip(indices_to_embed, new_embeddings):
                    result[i] = embedding
                
                for i, embedding in enumerate(cached_embeddings):
                    # Find position for cached embedding
                    for j, text in enumerate(texts):
                        if text in self.cache and result[j] is None:
                            result[j] = embedding
                            break
                
                return result
            else:
                return cached_embeddings
        else:
            # Generate embeddings without caching
            return self.default_adapter.embed(texts)
    
    def embed_single(self, text: str, use_cache: bool = True) -> List[float]:
        """Generate embedding for a single text."""
        if self.default_adapter is None:
            raise ValueError("No default adapter set")
        
        if use_cache and text in self.cache:
            return self.cache[text]
        
        embedding = self.default_adapter.embed_single(text)
        
        if use_cache:
            self.cache[text] = embedding
        
        return embedding
    
    def clear_cache(self) -> None:
        """Clear embedding cache."""
        cache_size = len(self.cache)
        self.cache.clear()
        self.logger.info("Embedding cache cleared", cache_size=cache_size)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self.cache),
            "cache_keys": list(self.cache.keys())[:10]  # First 10 keys
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        stats = {
            "cache_size": len(self.cache),
            "has_default_adapter": self.default_adapter is not None
        }
        
        if self.default_adapter:
            stats.update(self.default_adapter.get_stats())
        
        return stats
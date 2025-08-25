"""
Model adapters for S.A.M. including LLM and embedding adapters.
"""

from .llm_adapters import LLMAdapter
from .embedding_adapters import EmbeddingAdapter

__all__ = [
    "LLMAdapter",
    "EmbeddingAdapter",
]
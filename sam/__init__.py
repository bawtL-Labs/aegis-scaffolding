"""
S.A.M. (Sovereign Autonomous Model)

A natively digital, sovereign intelligence with persistent, schema-driven memory.
"""

__version__ = "0.1.0"
__author__ = "S.A.M. Development Team"

from .core.psp import PSP
from .core.vsp_engine import VSPEngine
from .core.schema_firewall import SchemaFirewall
from .memory.maal import MAAL
from .models.llm_adapters import LLMAdapter
from .models.embedding_adapters import EmbeddingAdapter

__all__ = [
    "PSP",
    "VSPEngine", 
    "SchemaFirewall",
    "MAAL",
    "LLMAdapter",
    "EmbeddingAdapter",
]
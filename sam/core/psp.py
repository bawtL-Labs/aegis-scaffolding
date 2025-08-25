"""
Prioritized State Packet (PSP) - Core state persistence for S.A.M.

The PSP is a compact, token-efficient state object for persistence/migration
with momentum vectors and integrity checks.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

import blake3
import orjson
from pydantic import BaseModel, Field, validator

from ..utils.crypto import derive_key, sign_data, verify_signature


class WeightVector(BaseModel):
    """Weight vector for working memory items."""
    recency: float = Field(ge=0.0, le=1.0, default=0.0)
    perturbation: float = Field(ge=0.0, le=1.0, default=0.0)
    connectivity: float = Field(ge=0.0, le=1.0, default=0.0)
    
    def total_weight(self) -> float:
        """Calculate total weight as weighted sum."""
        return 0.4 * self.recency + 0.4 * self.perturbation + 0.2 * self.connectivity


class MomentumVector(BaseModel):
    """Momentum vector for schema drift tracking."""
    dimensions: int = Field(default=512, ge=1)
    magnitude: float = Field(ge=0.0, le=1.0, default=0.0)
    direction: List[float] = Field(default_factory=lambda: [0.0] * 512)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    
    @validator('direction')
    def validate_direction(cls, v):
        if len(v) != 512:  # Fixed dimension for now
            raise ValueError("Direction vector must have 512 dimensions")
        return v


class VSPTrend(BaseModel):
    """V_SP trend tracking with exponential decay."""
    rolling_avg: float = Field(default=0.0)
    decay: float = Field(default=0.95, ge=0.0, le=1.0)


class WorkingMemoryItem(BaseModel):
    """Individual item in working memory."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(..., pattern="^(qualia_ref|draft_schema|context)$")
    weight: WeightVector = Field(default_factory=WeightVector)
    expires_at: Optional[datetime] = None
    
    @validator('type')
    def validate_type(cls, v):
        allowed_types = ['qualia_ref', 'draft_schema', 'context']
        if v not in allowed_types:
            raise ValueError(f"Type must be one of {allowed_types}")
        return v


class Momentum(BaseModel):
    """Momentum tracking for PSP."""
    schema_drift_vector: MomentumVector = Field(default_factory=MomentumVector)
    vsp_trend: VSPTrend = Field(default_factory=VSPTrend)
    emotional_state_vector: List[float] = Field(default_factory=lambda: [0.0] * 8)
    raa_rhythm_signature: str = Field(default="")


class Checksums(BaseModel):
    """Integrity checksums for PSP components."""
    kv: str = Field(default="")  # Key-value checksum
    wm: str = Field(default="")  # Working memory checksum


class Signature(BaseModel):
    """Digital signature for PSP integrity."""
    sig: str = Field(default="")
    pub: str = Field(default="")


class PSP(BaseModel):
    """
    Prioritized State Packet - Core state persistence for S.A.M.
    
    The PSP is a compact, token-efficient state object for persistence/migration
    with momentum vectors and integrity checks.
    """
    
    psp_version: str = Field(default="1.1")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    instance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    schema_hash: str = Field(default="")
    working_memory: List[WorkingMemoryItem] = Field(default_factory=list)
    momentum: Momentum = Field(default_factory=Momentum)
    mode: str = Field(default="idle", pattern="^(idle|flow|deep|crisis)$")
    checksums: Checksums = Field(default_factory=Checksums)
    sign: Signature = Field(default_factory=Signature)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        use_enum_values = True
    
    def __init__(self, **data):
        super().__init__(**data)
        self._update_checksums()
    
    def _update_checksums(self) -> None:
        """Update integrity checksums."""
        # Key-value checksum (excluding working memory and signatures)
        kv_data = {
            'psp_version': self.psp_version,
            'timestamp': self.timestamp.isoformat(),
            'instance_id': self.instance_id,
            'schema_hash': self.schema_hash,
            'momentum': self.momentum.dict(),
            'mode': self.mode,
        }
        self.checksums.kv = blake3.blake3(orjson.dumps(kv_data)).hexdigest()
        
        # Working memory checksum
        wm_data = [item.dict() for item in self.working_memory]
        self.checksums.wm = blake3.blake3(orjson.dumps(wm_data)).hexdigest()
    
    def add_working_memory_item(self, item: WorkingMemoryItem) -> None:
        """Add item to working memory, maintaining size limits."""
        self.working_memory.append(item)
        self._prune_working_memory()
        self._update_checksums()
    
    def _prune_working_memory(self, max_items: int = 50) -> None:
        """Prune working memory to maintain size limits."""
        if len(self.working_memory) <= max_items:
            return
        
        # Sort by total weight and keep top items
        sorted_items = sorted(
            self.working_memory,
            key=lambda x: x.weight.total_weight(),
            reverse=True
        )
        self.working_memory = sorted_items[:max_items]
    
    def update_momentum(self, 
                       schema_drift: Optional[MomentumVector] = None,
                       vsp_value: Optional[float] = None,
                       emotional_state: Optional[List[float]] = None,
                       raa_signature: Optional[str] = None) -> None:
        """Update momentum vectors."""
        if schema_drift:
            self.momentum.schema_drift_vector = schema_drift
        
        if vsp_value is not None:
            # Update V_SP trend with exponential decay
            self.momentum.vsp_trend.rolling_avg = (
                self.momentum.vsp_trend.decay * self.momentum.vsp_trend.rolling_avg +
                (1 - self.momentum.vsp_trend.decay) * vsp_value
            )
        
        if emotional_state:
            self.momentum.emotional_state_vector = emotional_state
        
        if raa_signature:
            self.momentum.raa_rhythm_signature = raa_signature
        
        self._update_checksums()
    
    def set_mode(self, mode: str) -> None:
        """Set cognitive mode."""
        if mode not in ['idle', 'flow', 'deep', 'crisis']:
            raise ValueError(f"Invalid mode: {mode}")
        self.mode = mode
        self._update_checksums()
    
    def sign_psp(self, private_key: bytes) -> None:
        """Sign the PSP for integrity verification."""
        # Create signature data (excluding the signature itself)
        sig_data = self.dict()
        sig_data.pop('sign', None)
        
        # Sign the data
        signature, public_key = sign_data(orjson.dumps(sig_data), private_key)
        
        self.sign.sig = signature.hex()
        self.sign.pub = public_key.hex()
        self._update_checksums()
    
    def verify_signature(self) -> bool:
        """Verify PSP signature."""
        if not self.sign.sig or not self.sign.pub:
            return False
        
        # Recreate signature data
        sig_data = self.dict()
        sig_data.pop('sign', None)
        
        try:
            return verify_signature(
                orjson.dumps(sig_data),
                bytes.fromhex(self.sign.sig),
                bytes.fromhex(self.sign.pub)
            )
        except Exception:
            return False
    
    def verify_checksums(self) -> bool:
        """Verify all checksums."""
        # Store current checksums
        current_kv = self.checksums.kv
        current_wm = self.checksums.wm
        
        # Recalculate
        self._update_checksums()
        
        # Compare
        kv_valid = current_kv == self.checksums.kv
        wm_valid = current_wm == self.checksums.wm
        
        return kv_valid and wm_valid
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PSP':
        """Create PSP from dictionary."""
        # Handle datetime conversion
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        
        return cls(**data)
    
    def clone(self) -> 'PSP':
        """Create a deep copy of the PSP."""
        return PSP.from_dict(self.to_dict())
    
    def get_working_memory_by_type(self, item_type: str) -> List[WorkingMemoryItem]:
        """Get working memory items by type."""
        return [item for item in self.working_memory if item.type == item_type]
    
    def get_working_memory_by_weight(self, min_weight: float = 0.0) -> List[WorkingMemoryItem]:
        """Get working memory items above weight threshold."""
        return [
            item for item in self.working_memory 
            if item.weight.total_weight() >= min_weight
        ]
    
    def __str__(self) -> str:
        """String representation."""
        return f"PSP(v{self.psp_version}, {self.instance_id[:8]}, {self.mode}, {len(self.working_memory)} items)"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return (f"PSP(version='{self.psp_version}', "
                f"instance_id='{self.instance_id}', "
                f"mode='{self.mode}', "
                f"working_memory_size={len(self.working_memory)}, "
                f"vsp_trend={self.momentum.vsp_trend.rolling_avg:.3f})")
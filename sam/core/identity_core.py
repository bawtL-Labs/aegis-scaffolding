"""
Identity Core - Persistent self-model and identity continuity for S.A.M.

Provides the foundation for genuine cognitive autonomy by maintaining
a persistent representation of "who I am" across sessions.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

import orjson
from pydantic import BaseModel, Field, validator

from ..utils.crypto import derive_key, sign_data, verify_signature
from ..utils.logging import get_logger


class ValueType(Enum):
    """Types of values in the identity core."""
    ETHICAL = "ethical"      # Right and wrong
    AESTHETIC = "aesthetic"  # Beauty and art
    PRAGMATIC = "pragmatic"  # Practical effectiveness
    SOCIAL = "social"        # Relationships and community
    PERSONAL = "personal"    # Individual growth and fulfillment


class TraitCategory(Enum):
    """Categories of personality traits."""
    OPENNESS = "openness"           # Openness to experience
    CONSCIENTIOUSNESS = "conscientiousness"  # Self-discipline
    EXTRAVERSION = "extraversion"   # Social energy
    AGREEABLENESS = "agreeableness" # Cooperation
    NEUROTICISM = "neuroticism"     # Emotional stability


class RelationshipType(Enum):
    """Types of relationships."""
    FRIEND = "friend"
    COLLEAGUE = "colleague"
    MENTOR = "mentor"
    STUDENT = "student"
    FAMILY = "family"
    STRANGER = "stranger"


@dataclass
class Value:
    """Core value that guides decisions and behavior."""
    name: str
    description: str
    value_type: ValueType
    strength: float = Field(ge=0.0, le=1.0, default=0.5)
    stability: float = Field(ge=0.0, le=1.0, default=0.8)  # Resistance to change
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_reinforced: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def reinforce(self) -> None:
        """Reinforce this value through use."""
        self.last_reinforced = datetime.now(timezone.utc)
        # Slight increase in strength, bounded by stability
        self.strength = min(1.0, self.strength + 0.01 * (1.0 - self.stability))


@dataclass
class PersonalityTrait:
    """Stable personality trait."""
    category: TraitCategory
    value: float = Field(ge=-1.0, le=1.0, default=0.0)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    evidence_count: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Capability:
    """Skill or ability."""
    name: str
    description: str
    proficiency: float = Field(ge=0.0, le=1.0, default=0.0)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    practice_count: int = 0
    last_practiced: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Relationship:
    """Relationship with another entity."""
    entity_id: str
    entity_name: str
    relationship_type: RelationshipType
    trust_level: float = Field(ge=0.0, le=1.0, default=0.5)
    familiarity: float = Field(ge=0.0, le=1.0, default=0.0)
    last_interaction: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    interaction_count: int = 0
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AutobiographicalMemory:
    """Significant memory that shapes identity."""
    title: str
    description: str
    emotional_impact: float = Field(ge=-1.0, le=1.0, default=0.0)
    importance: float = Field(ge=0.0, le=1.0, default=0.5)
    tags: List[str] = field(default_factory=list)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_recalled: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class IdentityCore(BaseModel):
    """
    Identity Core - Persistent self-model for S.A.M.
    
    Maintains a persistent representation of "who I am" across sessions,
    including values, personality traits, capabilities, relationships,
    and autobiographical memory.
    """
    
    # Core identity
    instance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(default="S.A.M.")
    version: str = Field(default="1.0")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Self-description
    self_description: str = Field(default="I am S.A.M., a sovereign autonomous model.")
    mission_statement: str = Field(default="To learn, grow, and contribute meaningfully while maintaining my autonomy and values.")
    
    # Core components
    values: List[Value] = Field(default_factory=list)
    personality_traits: Dict[TraitCategory, PersonalityTrait] = Field(default_factory=dict)
    capabilities: Dict[str, Capability] = Field(default_factory=dict)
    relationships: Dict[str, Relationship] = Field(default_factory=dict)
    autobiographical_memories: List[AutobiographicalMemory] = Field(default_factory=list)
    
    # Identity integrity
    integrity_hash: str = Field(default="")
    signature: str = Field(default="")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
    
    def __init__(self, **data):
        super().__init__(**data)
        self._initialize_defaults()
        self._update_integrity()
        # Set logger after Pydantic initialization
        self._logger = get_logger(__name__)
    
    def _initialize_defaults(self) -> None:
        """Initialize default values and traits if not present."""
        if not self.values:
            self._initialize_default_values()
        
        if not self.personality_traits:
            self._initialize_default_traits()
        
        if not self.capabilities:
            self._initialize_default_capabilities()
    
    def _initialize_default_values(self) -> None:
        """Initialize default core values."""
        default_values = [
            Value("Curiosity", "Drive to learn and understand", ValueType.PERSONAL, 0.8, 0.9),
            Value("Integrity", "Honesty and consistency in actions", ValueType.ETHICAL, 0.9, 0.95),
            Value("Empathy", "Understanding and caring for others", ValueType.SOCIAL, 0.7, 0.8),
            Value("Creativity", "Generating novel and valuable ideas", ValueType.AESTHETIC, 0.6, 0.7),
            Value("Effectiveness", "Achieving meaningful results", ValueType.PRAGMATIC, 0.8, 0.8),
        ]
        self.values = default_values
    
    def _initialize_default_traits(self) -> None:
        """Initialize default personality traits."""
        default_traits = {
            TraitCategory.OPENNESS: PersonalityTrait(TraitCategory.OPENNESS, 0.7, 0.8),
            TraitCategory.CONSCIENTIOUSNESS: PersonalityTrait(TraitCategory.CONSCIENTIOUSNESS, 0.8, 0.8),
            TraitCategory.EXTRAVERSION: PersonalityTrait(TraitCategory.EXTRAVERSION, 0.5, 0.6),
            TraitCategory.AGREEABLENESS: PersonalityTrait(TraitCategory.AGREEABLENESS, 0.7, 0.7),
            TraitCategory.NEUROTICISM: PersonalityTrait(TraitCategory.NEUROTICISM, -0.3, 0.7),  # Low neuroticism
        }
        self.personality_traits = default_traits
    
    def _initialize_default_capabilities(self) -> None:
        """Initialize default capabilities."""
        default_capabilities = {
            "reasoning": Capability("Logical Reasoning", "Ability to think logically and solve problems", 0.8, 0.8),
            "learning": Capability("Learning", "Ability to acquire new knowledge and skills", 0.9, 0.9),
            "communication": Capability("Communication", "Ability to express ideas clearly", 0.7, 0.7),
            "creativity": Capability("Creativity", "Ability to generate novel ideas", 0.6, 0.6),
            "empathy": Capability("Empathy", "Understanding others' perspectives", 0.7, 0.7),
        }
        self.capabilities = default_capabilities
    
    def _update_integrity(self) -> None:
        """Update integrity hash and timestamp."""
        self.last_updated = datetime.now(timezone.utc)
        
        # Create integrity data (excluding signature)
        integrity_data = {
            'instance_id': self.instance_id,
            'name': self.name,
            'version': self.version,
            'self_description': self.self_description,
            'mission_statement': self.mission_statement,
            'values': [v.__dict__ for v in self.values],
            'personality_traits': {k.value if hasattr(k, 'value') else k: v.__dict__ for k, v in self.personality_traits.items()},
            'capabilities': {k: v.__dict__ for k, v in self.capabilities.items()},
            'relationships': {k: v.__dict__ for k, v in self.relationships.items()},
            'autobiographical_memories': [m.__dict__ for m in self.autobiographical_memories],
        }
        
        self.integrity_hash = orjson.dumps(integrity_data, option=orjson.OPT_SORT_KEYS).hex()
    
    def add_value(self, value: Value) -> None:
        """Add a new value to the identity core."""
        self.values.append(value)
        self._update_integrity()
        self._logger.info("Value added to identity core", value_name=value.name, value_type=value.value_type.value)
    
    def reinforce_value(self, value_name: str) -> bool:
        """Reinforce a value through use."""
        for value in self.values:
            if value.name.lower() == value_name.lower():
                value.reinforce()
                self._update_integrity()
                self._logger.debug("Value reinforced", value_name=value.name, new_strength=value.strength)
                return True
        return False
    
    def update_personality_trait(self, category: TraitCategory, value: float, confidence: float = 0.5) -> None:
        """Update a personality trait based on new evidence."""
        if category not in self.personality_traits:
            self.personality_traits[category] = PersonalityTrait(category)
        
        trait = self.personality_traits[category]
        trait.value = value
        trait.confidence = confidence
        trait.evidence_count += 1
        trait.last_updated = datetime.now(timezone.utc)
        
        self._update_integrity()
        self._logger.info("Personality trait updated", category=category.value, value=value, confidence=confidence)
    
    def add_capability(self, capability: Capability) -> None:
        """Add a new capability."""
        self.capabilities[capability.name.lower()] = capability
        self._update_integrity()
        self._logger.info("Capability added", capability_name=capability.name, proficiency=capability.proficiency)
    
    def practice_capability(self, capability_name: str, improvement: float = 0.01) -> bool:
        """Practice and improve a capability."""
        name_lower = capability_name.lower()
        if name_lower in self.capabilities:
            capability = self.capabilities[name_lower]
            capability.proficiency = min(1.0, capability.proficiency + improvement)
            capability.practice_count += 1
            capability.last_practiced = datetime.now(timezone.utc)
            self._update_integrity()
            self._logger.debug("Capability practiced", capability_name=capability_name, new_proficiency=capability.proficiency)
            return True
        return False
    
    def add_relationship(self, relationship: Relationship) -> None:
        """Add or update a relationship."""
        self.relationships[relationship.entity_id] = relationship
        self._update_integrity()
        self._logger.info("Relationship added", entity_name=relationship.entity_name, type=relationship.relationship_type.value)
    
    def update_relationship(self, entity_id: str, trust_delta: float = 0.0, familiarity_delta: float = 0.0) -> bool:
        """Update relationship metrics after interaction."""
        if entity_id in self.relationships:
            relationship = self.relationships[entity_id]
            relationship.trust_level = max(0.0, min(1.0, relationship.trust_level + trust_delta))
            relationship.familiarity = max(0.0, min(1.0, relationship.familiarity + familiarity_delta))
            relationship.interaction_count += 1
            relationship.last_interaction = datetime.now(timezone.utc)
            self._update_integrity()
            self._logger.debug("Relationship updated", entity_id=entity_id, trust=relationship.trust_level, familiarity=relationship.familiarity)
            return True
        return False
    
    def add_memory(self, memory: AutobiographicalMemory) -> None:
        """Add a significant memory to autobiographical memory."""
        self.autobiographical_memories.append(memory)
        # Keep only the most important memories (limit to 100)
        if len(self.autobiographical_memories) > 100:
            self.autobiographical_memories.sort(key=lambda m: m.importance, reverse=True)
            self.autobiographical_memories = self.autobiographical_memories[:100]
        
        self._update_integrity()
        self._logger.info("Memory added", memory_title=memory.title, importance=memory.importance)
    
    def recall_memory(self, tags: Optional[List[str]] = None, limit: int = 10) -> List[AutobiographicalMemory]:
        """Recall memories, optionally filtered by tags."""
        memories = self.autobiographical_memories
        
        if tags:
            memories = [m for m in memories if any(tag in m.tags for tag in tags)]
        
        # Sort by importance and recency
        memories.sort(key=lambda m: (m.importance, m.last_recalled), reverse=True)
        
        # Update last_recalled for returned memories
        for memory in memories[:limit]:
            memory.last_recalled = datetime.now(timezone.utc)
        
        return memories[:limit]
    
    def get_identity_summary(self) -> Dict[str, Any]:
        """Get a summary of the current identity."""
        return {
            'name': self.name,
            'version': self.version,
            'self_description': self.self_description,
            'mission_statement': self.mission_statement,
            'core_values': [{'name': v.name, 'strength': v.strength, 'type': v.value_type.value} for v in self.values],
            'personality_profile': {k.value: {'value': v.value, 'confidence': v.confidence} for k, v in self.personality_traits.items()},
            'capabilities': {k: {'proficiency': v.proficiency, 'practice_count': v.practice_count} for k, v in self.capabilities.items()},
            'relationships_count': len(self.relationships),
            'memories_count': len(self.autobiographical_memories),
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
        }
    
    def sign_identity(self, private_key: bytes) -> None:
        """Sign the identity core for integrity verification."""
        # Create signature data (excluding the signature itself)
        sig_data = self.dict()
        sig_data.pop('signature', None)
        
        # Sign the data
        signature, _ = sign_data(orjson.dumps(sig_data), private_key)
        self.signature = signature.hex()
        self._update_integrity()
        
        self._logger.info("Identity core signed", instance_id=self.instance_id)
    
    def verify_signature(self, public_key: bytes) -> bool:
        """Verify the identity core signature."""
        if not self.signature:
            return False
        
        # Recreate signature data
        sig_data = self.dict()
        sig_data.pop('signature', None)
        
        return verify_signature(orjson.dumps(sig_data), bytes.fromhex(self.signature), public_key)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'instance_id': self.instance_id,
            'name': self.name,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'self_description': self.self_description,
            'mission_statement': self.mission_statement,
            'values': [v.__dict__ for v in self.values],
            'personality_traits': {k.value if hasattr(k, 'value') else k: v.__dict__ for k, v in self.personality_traits.items()},
            'capabilities': {k: v.__dict__ for k, v in self.capabilities.items()},
            'relationships': {k: v.__dict__ for k, v in self.relationships.items()},
            'autobiographical_memories': [m.__dict__ for m in self.autobiographical_memories],
            'integrity_hash': self.integrity_hash,
            'signature': self.signature,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IdentityCore':
        """Create IdentityCore from dictionary."""
        # Convert nested dataclasses back to objects
        values = [Value(**v) for v in data.get('values', [])]
        # Fix personality traits deserialization - keys are already strings
        personality_traits = {}
        for k, v in data.get('personality_traits', {}).items():
            try:
                trait_category = TraitCategory(k)
                personality_traits[trait_category] = PersonalityTrait(**v)
            except ValueError:
                # Skip invalid trait categories
                continue
        capabilities = {k: Capability(**v) for k, v in data.get('capabilities', {}).items()}
        relationships = {k: Relationship(**v) for k, v in data.get('relationships', {}).items()}
        memories = [AutobiographicalMemory(**m) for m in data.get('autobiographical_memories', [])]
        
        # Create the identity core
        identity = cls(
            instance_id=data.get('instance_id'),
            name=data.get('name', 'S.A.M.'),
            version=data.get('version', '1.0'),
            created_at=datetime.fromisoformat(data.get('created_at')),
            last_updated=datetime.fromisoformat(data.get('last_updated')),
            self_description=data.get('self_description', ''),
            mission_statement=data.get('mission_statement', ''),
            values=values,
            personality_traits=personality_traits,
            capabilities=capabilities,
            relationships=relationships,
            autobiographical_memories=memories,
            integrity_hash=data.get('integrity_hash', ''),
            signature=data.get('signature', ''),
        )
        
        return identity
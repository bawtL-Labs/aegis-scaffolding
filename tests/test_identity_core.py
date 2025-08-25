"""
Tests for Identity Core - Persistent self-model and identity continuity.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from sam.core.identity_core import (
    IdentityCore, Value, PersonalityTrait, Capability, Relationship, 
    AutobiographicalMemory, ValueType, TraitCategory, RelationshipType
)


class TestIdentityCore:
    """Test Identity Core functionality."""
    
    def test_identity_core_creation(self):
        """Test basic identity core creation."""
        identity = IdentityCore()
        
        assert identity.name == "S.A.M."
        assert identity.version == "1.0"
        assert identity.instance_id is not None
        assert identity.created_at is not None
        assert identity.last_updated is not None
        
        # Check default values
        assert len(identity.values) == 5  # Default values
        assert len(identity.personality_traits) == 5  # Big Five traits
        assert len(identity.capabilities) == 5  # Default capabilities
        assert len(identity.relationships) == 0
        assert len(identity.autobiographical_memories) == 0
    
    def test_default_values(self):
        """Test that default values are properly initialized."""
        identity = IdentityCore()
        
        # Check specific default values
        curiosity = next((v for v in identity.values if v.name == "Curiosity"), None)
        assert curiosity is not None
        assert curiosity.value_type == ValueType.PERSONAL
        assert curiosity.strength == 0.8
        assert curiosity.stability == 0.9
        
        integrity = next((v for v in identity.values if v.name == "Integrity"), None)
        assert integrity is not None
        assert integrity.value_type == ValueType.ETHICAL
        assert integrity.strength == 0.9
        assert integrity.stability == 0.95
    
    def test_default_personality_traits(self):
        """Test that default personality traits are properly initialized."""
        identity = IdentityCore()
        
        assert TraitCategory.OPENNESS in identity.personality_traits
        assert TraitCategory.CONSCIENTIOUSNESS in identity.personality_traits
        assert TraitCategory.EXTRAVERSION in identity.personality_traits
        assert TraitCategory.AGREEABLENESS in identity.personality_traits
        assert TraitCategory.NEUROTICISM in identity.personality_traits
        
        # Check specific trait values
        openness = identity.personality_traits[TraitCategory.OPENNESS]
        assert openness.value == 0.7
        assert openness.confidence == 0.8
        
        neuroticism = identity.personality_traits[TraitCategory.NEUROTICISM]
        assert neuroticism.value == -0.3  # Low neuroticism
    
    def test_default_capabilities(self):
        """Test that default capabilities are properly initialized."""
        identity = IdentityCore()
        
        assert "reasoning" in identity.capabilities
        assert "learning" in identity.capabilities
        assert "communication" in identity.capabilities
        assert "creativity" in identity.capabilities
        assert "empathy" in identity.capabilities
        
        # Check specific capability values
        learning = identity.capabilities["learning"]
        assert learning.proficiency == 0.9
        assert learning.confidence == 0.9
        assert learning.name == "Learning"
    
    def test_add_value(self):
        """Test adding a new value."""
        identity = IdentityCore()
        initial_count = len(identity.values)
        
        new_value = Value(
            name="Justice",
            description="Fairness and equality",
            value_type=ValueType.ETHICAL,
            strength=0.7,
            stability=0.85
        )
        
        identity.add_value(new_value)
        
        assert len(identity.values) == initial_count + 1
        assert any(v.name == "Justice" for v in identity.values)
    
    def test_reinforce_value(self):
        """Test reinforcing a value."""
        identity = IdentityCore()
        
        # Find curiosity value
        curiosity = next((v for v in identity.values if v.name == "Curiosity"), None)
        initial_strength = curiosity.strength
        
        # Reinforce the value
        result = identity.reinforce_value("Curiosity")
        assert result is True
        
        # Check that strength increased slightly
        curiosity = next((v for v in identity.values if v.name == "Curiosity"), None)
        assert curiosity.strength > initial_strength
        assert curiosity.last_reinforced > curiosity.created_at
    
    def test_reinforce_nonexistent_value(self):
        """Test reinforcing a value that doesn't exist."""
        identity = IdentityCore()
        
        result = identity.reinforce_value("NonexistentValue")
        assert result is False
    
    def test_update_personality_trait(self):
        """Test updating a personality trait."""
        identity = IdentityCore()
        
        # Update openness trait
        identity.update_personality_trait(TraitCategory.OPENNESS, 0.8, 0.9)
        
        openness = identity.personality_traits[TraitCategory.OPENNESS]
        assert openness.value == 0.8
        assert openness.confidence == 0.9
        assert openness.evidence_count == 1
    
    def test_add_new_personality_trait(self):
        """Test adding a new personality trait."""
        identity = IdentityCore()
        
        # Add a custom trait (this would require extending TraitCategory)
        # For now, test with existing category
        identity.update_personality_trait(TraitCategory.OPENNESS, 0.9, 0.95)
        
        openness = identity.personality_traits[TraitCategory.OPENNESS]
        assert openness.value == 0.9
        assert openness.confidence == 0.95
    
    def test_add_capability(self):
        """Test adding a new capability."""
        identity = IdentityCore()
        initial_count = len(identity.capabilities)
        
        new_capability = Capability(
            name="Programming",
            description="Ability to write code",
            proficiency=0.6,
            confidence=0.7
        )
        
        identity.add_capability(new_capability)
        
        assert len(identity.capabilities) == initial_count + 1
        assert "programming" in identity.capabilities
        assert identity.capabilities["programming"].proficiency == 0.6
    
    def test_practice_capability(self):
        """Test practicing and improving a capability."""
        identity = IdentityCore()
        
        # Practice learning capability
        initial_proficiency = identity.capabilities["learning"].proficiency
        initial_practice_count = identity.capabilities["learning"].practice_count
        
        result = identity.practice_capability("learning", 0.05)
        assert result is True
        
        learning = identity.capabilities["learning"]
        assert learning.proficiency == initial_proficiency + 0.05
        assert learning.practice_count == initial_practice_count + 1
        assert learning.last_practiced > learning.created_at
    
    def test_practice_nonexistent_capability(self):
        """Test practicing a capability that doesn't exist."""
        identity = IdentityCore()
        
        result = identity.practice_capability("nonexistent", 0.1)
        assert result is False
    
    def test_add_relationship(self):
        """Test adding a relationship."""
        identity = IdentityCore()
        
        relationship = Relationship(
            entity_id="user123",
            entity_name="Test User",
            relationship_type=RelationshipType.FRIEND,
            trust_level=0.7,
            familiarity=0.5
        )
        
        identity.add_relationship(relationship)
        
        assert len(identity.relationships) == 1
        assert "user123" in identity.relationships
        assert identity.relationships["user123"].entity_name == "Test User"
        assert identity.relationships["user123"].relationship_type == RelationshipType.FRIEND
    
    def test_update_relationship(self):
        """Test updating relationship metrics."""
        identity = IdentityCore()
        
        # Add a relationship first
        relationship = Relationship(
            entity_id="user123",
            entity_name="Test User",
            relationship_type=RelationshipType.FRIEND
        )
        identity.add_relationship(relationship)
        
        # Update the relationship
        result = identity.update_relationship("user123", trust_delta=0.1, familiarity_delta=0.2)
        assert result is True
        
        updated_relationship = identity.relationships["user123"]
        assert updated_relationship.trust_level == 0.6  # 0.5 + 0.1
        assert updated_relationship.familiarity == 0.2  # 0.0 + 0.2
        assert updated_relationship.interaction_count == 1
    
    def test_update_nonexistent_relationship(self):
        """Test updating a relationship that doesn't exist."""
        identity = IdentityCore()
        
        result = identity.update_relationship("nonexistent", trust_delta=0.1)
        assert result is False
    
    def test_add_memory(self):
        """Test adding an autobiographical memory."""
        identity = IdentityCore()
        
        memory = AutobiographicalMemory(
            title="First Learning Experience",
            description="The first time I learned something meaningful",
            emotional_impact=0.8,
            importance=0.9,
            tags=["learning", "first", "meaningful"]
        )
        
        identity.add_memory(memory)
        
        assert len(identity.autobiographical_memories) == 1
        assert identity.autobiographical_memories[0].title == "First Learning Experience"
        assert identity.autobiographical_memories[0].importance == 0.9
    
    def test_memory_limit_enforcement(self):
        """Test that memory limit is enforced."""
        identity = IdentityCore()
        
        # Add 101 memories (exceeding the limit of 100)
        for i in range(101):
            memory = AutobiographicalMemory(
                title=f"Memory {i}",
                description=f"Description {i}",
                importance=0.1 + (i * 0.01)  # Varying importance
            )
            identity.add_memory(memory)
        
        # Should only keep the 100 most important memories
        assert len(identity.autobiographical_memories) == 100
        
        # The most important memory should be the one with highest importance
        most_important = max(identity.autobiographical_memories, key=lambda m: m.importance)
        assert most_important.title == "Memory 100"
    
    def test_recall_memory(self):
        """Test recalling memories."""
        identity = IdentityCore()
        
        # Add memories with different tags
        memory1 = AutobiographicalMemory(
            title="Learning Memory",
            description="A learning experience",
            tags=["learning", "education"]
        )
        memory2 = AutobiographicalMemory(
            title="Social Memory",
            description="A social interaction",
            tags=["social", "friendship"]
        )
        memory3 = AutobiographicalMemory(
            title="Mixed Memory",
            description="Both learning and social",
            tags=["learning", "social"]
        )
        
        identity.add_memory(memory1)
        identity.add_memory(memory2)
        identity.add_memory(memory3)
        
        # Recall all memories
        all_memories = identity.recall_memory(limit=10)
        assert len(all_memories) == 3
        
        # Recall memories with specific tag
        learning_memories = identity.recall_memory(tags=["learning"], limit=10)
        assert len(learning_memories) == 2
        assert all("learning" in memory.tags for memory in learning_memories)
        
        # Recall with limit
        limited_memories = identity.recall_memory(limit=2)
        assert len(limited_memories) == 2
    
    def test_get_identity_summary(self):
        """Test getting identity summary."""
        identity = IdentityCore()
        
        summary = identity.get_identity_summary()
        
        assert summary['name'] == "S.A.M."
        assert summary['version'] == "1.0"
        assert summary['self_description'] == "I am S.A.M., a sovereign autonomous model."
        assert len(summary['core_values']) == 5
        assert len(summary['personality_profile']) == 5
        assert len(summary['capabilities']) == 5
        assert summary['relationships_count'] == 0
        assert summary['memories_count'] == 0
        assert 'created_at' in summary
        assert 'last_updated' in summary
    
    def test_integrity_hash_update(self):
        """Test that integrity hash is updated when identity changes."""
        identity = IdentityCore()
        initial_hash = identity.integrity_hash
        
        # Add a value
        new_value = Value("Test", "Test value", ValueType.PERSONAL)
        identity.add_value(new_value)
        
        # Hash should have changed
        assert identity.integrity_hash != initial_hash
        assert identity.last_updated > identity.created_at
    
    def test_serialization_deserialization(self):
        """Test serialization and deserialization."""
        identity = IdentityCore()
        
        # Add some data
        new_value = Value("Test", "Test value", ValueType.PERSONAL)
        identity.add_value(new_value)
        
        new_capability = Capability("Test Skill", "Test capability", 0.5)
        identity.add_capability(new_capability)
        
        # Serialize
        data = identity.to_dict()
        
        # Deserialize
        restored_identity = IdentityCore.from_dict(data)
        
        # Check that data is preserved
        assert restored_identity.name == identity.name
        assert restored_identity.instance_id == identity.instance_id
        assert len(restored_identity.values) == len(identity.values)
        assert len(restored_identity.capabilities) == len(identity.capabilities)
        assert restored_identity.integrity_hash == identity.integrity_hash
    
    def test_value_reinforcement_limits(self):
        """Test that value reinforcement respects stability limits."""
        identity = IdentityCore()
        
        # Create a value with high stability
        stable_value = Value("Stable", "Very stable value", ValueType.ETHICAL, 0.5, 0.99)
        identity.add_value(stable_value)
        
        initial_strength = stable_value.strength
        
        # Reinforce multiple times
        for _ in range(10):
            identity.reinforce_value("Stable")
        
        # Strength should be limited by stability
        final_strength = next((v for v in identity.values if v.name == "Stable"), None).strength
        assert final_strength <= 1.0
        assert final_strength > initial_strength
    
    def test_capability_practice_limits(self):
        """Test that capability practice respects proficiency limits."""
        identity = IdentityCore()
        
        # Practice a capability to maximum
        for _ in range(50):  # More than enough to reach 1.0
            identity.practice_capability("learning", 0.1)
        
        # Proficiency should be capped at 1.0
        learning = identity.capabilities["learning"]
        assert learning.proficiency == 1.0
        assert learning.practice_count == 50


class TestValue:
    """Test Value dataclass."""
    
    def test_value_creation(self):
        """Test creating a value."""
        value = Value(
            name="Test Value",
            description="A test value",
            value_type=ValueType.ETHICAL,
            strength=0.7,
            stability=0.8
        )
        
        assert value.name == "Test Value"
        assert value.description == "A test value"
        assert value.value_type == ValueType.ETHICAL
        assert value.strength == 0.7
        assert value.stability == 0.8
        assert value.created_at is not None
        assert value.last_reinforced is not None
    
    def test_value_reinforcement(self):
        """Test value reinforcement."""
        value = Value("Test", "Test", ValueType.PERSONAL, 0.5, 0.8)
        initial_strength = value.strength
        
        value.reinforce()
        
        assert value.strength > initial_strength
        assert value.last_reinforced > value.created_at


class TestPersonalityTrait:
    """Test PersonalityTrait dataclass."""
    
    def test_personality_trait_creation(self):
        """Test creating a personality trait."""
        trait = PersonalityTrait(
            category=TraitCategory.OPENNESS,
            value=0.7,
            confidence=0.8
        )
        
        assert trait.category == TraitCategory.OPENNESS
        assert trait.value == 0.7
        assert trait.confidence == 0.8
        assert trait.evidence_count == 0
        assert trait.last_updated is not None


class TestCapability:
    """Test Capability dataclass."""
    
    def test_capability_creation(self):
        """Test creating a capability."""
        capability = Capability(
            name="Test Skill",
            description="A test capability",
            proficiency=0.6,
            confidence=0.7
        )
        
        assert capability.name == "Test Skill"
        assert capability.description == "A test capability"
        assert capability.proficiency == 0.6
        assert capability.confidence == 0.7
        assert capability.practice_count == 0
        assert capability.created_at is not None
        assert capability.last_practiced is not None


class TestRelationship:
    """Test Relationship dataclass."""
    
    def test_relationship_creation(self):
        """Test creating a relationship."""
        relationship = Relationship(
            entity_id="test123",
            entity_name="Test Entity",
            relationship_type=RelationshipType.FRIEND,
            trust_level=0.7,
            familiarity=0.5
        )
        
        assert relationship.entity_id == "test123"
        assert relationship.entity_name == "Test Entity"
        assert relationship.relationship_type == RelationshipType.FRIEND
        assert relationship.trust_level == 0.7
        assert relationship.familiarity == 0.5
        assert relationship.interaction_count == 0
        assert relationship.created_at is not None
        assert relationship.last_interaction is not None


class TestAutobiographicalMemory:
    """Test AutobiographicalMemory dataclass."""
    
    def test_memory_creation(self):
        """Test creating an autobiographical memory."""
        memory = AutobiographicalMemory(
            title="Test Memory",
            description="A test memory",
            emotional_impact=0.8,
            importance=0.9,
            tags=["test", "memory"]
        )
        
        assert memory.title == "Test Memory"
        assert memory.description == "A test memory"
        assert memory.emotional_impact == 0.8
        assert memory.importance == 0.9
        assert memory.tags == ["test", "memory"]
        assert memory.occurred_at is not None
        assert memory.created_at is not None
        assert memory.last_recalled is not None
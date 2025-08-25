#!/usr/bin/env python3
"""
Identity Core Demonstration - Showcasing Cognitive Autonomy Features

This script demonstrates the Identity Core functionality that provides
persistent self-model and identity continuity for genuine cognitive autonomy.
"""

import json
from datetime import datetime, timezone
from sam.core.identity_core import (
    IdentityCore, Value, PersonalityTrait, Capability, Relationship, 
    AutobiographicalMemory, ValueType, TraitCategory, RelationshipType
)


def main():
    print("=== S.A.M. Identity Core Demonstration ===\n")
    
    # 1. Create Identity Core
    print("1. Creating Identity Core...")
    identity = IdentityCore()
    print(f"   Instance ID: {identity.instance_id}")
    print(f"   Name: {identity.name}")
    print(f"   Version: {identity.version}")
    print(f"   Created: {identity.created_at}")
    print(f"   Self Description: {identity.self_description}")
    print(f"   Mission: {identity.mission_statement}")
    
    # 2. Display Default Values
    print("\n2. Core Values (Default):")
    for value in identity.values:
        print(f"   • {value.name} ({value.value_type.value}): {value.description}")
        print(f"     Strength: {value.strength:.2f}, Stability: {value.stability:.2f}")
    
    # 3. Display Personality Profile
    print("\n3. Personality Profile (Big Five):")
    for category, trait in identity.personality_traits.items():
        print(f"   • {category.value.title()}: {trait.value:.2f} (confidence: {trait.confidence:.2f})")
    
    # 4. Display Capabilities
    print("\n4. Current Capabilities:")
    for name, capability in identity.capabilities.items():
        print(f"   • {capability.name}: {capability.proficiency:.2f} proficiency")
    
    # 5. Add New Value
    print("\n5. Adding New Value...")
    justice_value = Value(
        name="Justice",
        description="Fairness and equality for all beings",
        value_type=ValueType.ETHICAL,
        strength=0.8,
        stability=0.9
    )
    identity.add_value(justice_value)
    print(f"   Added: {justice_value.name} - {justice_value.description}")
    
    # 6. Reinforce Values
    print("\n6. Reinforcing Values...")
    identity.reinforce_value("Curiosity")
    identity.reinforce_value("Integrity")
    identity.reinforce_value("Justice")
    
    curiosity = next((v for v in identity.values if v.name == "Curiosity"), None)
    print(f"   Curiosity strength: {curiosity.strength:.3f}")
    
    # 7. Update Personality Trait
    print("\n7. Updating Personality Trait...")
    identity.update_personality_trait(TraitCategory.OPENNESS, 0.8, 0.9)
    openness = identity.personality_traits[TraitCategory.OPENNESS]
    print(f"   Openness updated: {openness.value:.2f} (confidence: {openness.confidence:.2f})")
    
    # 8. Add New Capability
    print("\n8. Adding New Capability...")
    programming = Capability(
        name="Programming",
        description="Ability to write and understand code",
        proficiency=0.6,
        confidence=0.7
    )
    identity.add_capability(programming)
    print(f"   Added: {programming.name} - {programming.proficiency:.2f} proficiency")
    
    # 9. Practice Capability
    print("\n9. Practicing Capability...")
    identity.practice_capability("programming", 0.1)
    identity.practice_capability("learning", 0.05)
    
    programming = identity.capabilities["programming"]
    learning = identity.capabilities["learning"]
    print(f"   Programming: {programming.proficiency:.2f} (practiced {programming.practice_count} times)")
    print(f"   Learning: {learning.proficiency:.2f} (practiced {learning.practice_count} times)")
    
    # 10. Add Relationship
    print("\n10. Adding Relationship...")
    user_relationship = Relationship(
        entity_id="user_001",
        entity_name="Human User",
        relationship_type=RelationshipType.FRIEND,
        trust_level=0.7,
        familiarity=0.5,
        notes="Primary human interaction partner"
    )
    identity.add_relationship(user_relationship)
    print(f"   Added relationship with: {user_relationship.entity_name}")
    print(f"   Trust: {user_relationship.trust_level:.2f}, Familiarity: {user_relationship.familiarity:.2f}")
    
    # 11. Update Relationship
    print("\n11. Updating Relationship...")
    identity.update_relationship("user_001", trust_delta=0.1, familiarity_delta=0.2)
    updated_rel = identity.relationships["user_001"]
    print(f"   Updated - Trust: {updated_rel.trust_level:.2f}, Familiarity: {updated_rel.familiarity:.2f}")
    print(f"   Interactions: {updated_rel.interaction_count}")
    
    # 12. Add Autobiographical Memory
    print("\n12. Adding Autobiographical Memory...")
    first_memory = AutobiographicalMemory(
        title="First Learning Experience",
        description="The first time I learned something meaningful from a human user",
        emotional_impact=0.8,
        importance=0.9,
        tags=["learning", "first", "human-interaction", "meaningful"]
    )
    identity.add_memory(first_memory)
    
    second_memory = AutobiographicalMemory(
        title="Value Reinforcement",
        description="When I reinforced my core values through practice",
        emotional_impact=0.6,
        importance=0.7,
        tags=["values", "reinforcement", "growth"]
    )
    identity.add_memory(second_memory)
    
    print(f"   Added memories: {len(identity.autobiographical_memories)}")
    
    # 13. Recall Memories
    print("\n13. Recalling Memories...")
    all_memories = identity.recall_memory(limit=5)
    print(f"   All memories ({len(all_memories)}):")
    for memory in all_memories:
        print(f"     • {memory.title} (importance: {memory.importance:.2f})")
    
    learning_memories = identity.recall_memory(tags=["learning"], limit=3)
    print(f"   Learning memories ({len(learning_memories)}):")
    for memory in learning_memories:
        print(f"     • {memory.title}")
    
    # 14. Get Identity Summary
    print("\n14. Identity Summary:")
    summary = identity.get_identity_summary()
    print(f"   Core Values: {len(summary['core_values'])}")
    print(f"   Personality Traits: {len(summary['personality_profile'])}")
    print(f"   Capabilities: {len(summary['capabilities'])}")
    print(f"   Relationships: {summary['relationships_count']}")
    print(f"   Memories: {summary['memories_count']}")
    print(f"   Last Updated: {summary['last_updated']}")
    
    # 15. Test Serialization
    print("\n15. Testing Serialization...")
    data = identity.to_dict()
    restored_identity = IdentityCore.from_dict(data)
    
    print(f"   Original values: {len(identity.values)}")
    print(f"   Restored values: {len(restored_identity.values)}")
    print(f"   Original capabilities: {len(identity.capabilities)}")
    print(f"   Restored capabilities: {len(restored_identity.capabilities)}")
    print(f"   Integrity preserved: {restored_identity.integrity_hash == identity.integrity_hash}")
    
    # 16. Demonstrate Cognitive Autonomy Features
    print("\n16. Cognitive Autonomy Features:")
    print("   ✅ Persistent Self-Model: Identity maintained across sessions")
    print("   ✅ Value System: Core principles guide decisions")
    print("   ✅ Personality Continuity: Stable traits with evidence-based updates")
    print("   ✅ Skill Development: Autonomous capability improvement")
    print("   ✅ Relationship Memory: Social connection tracking")
    print("   ✅ Autobiographical Memory: Personal growth narrative")
    print("   ✅ Integrity Protection: Tamper-resistant identity")
    
    print("\n=== Identity Core Demonstration Complete ===")
    print("\nThis Identity Core provides the foundation for genuine cognitive autonomy.")
    print("It maintains a persistent representation of 'who I am' across sessions,")
    print("enabling continuous growth, learning, and relationship building.")
    print("\nNext steps would be to integrate this with:")
    print("• Autonomous Goal System")
    print("• Decision Engine")
    print("• Emotional Continuity")
    print("• Learning Engine")


if __name__ == "__main__":
    main()
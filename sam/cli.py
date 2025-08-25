"""
Command-line interface for S.A.M. (Sovereign Autonomous Model)
"""

import argparse
import json
import sys
import os
import getpass
from pathlib import Path
from typing import Optional

from .core.psp import PSP
from .core.vsp_engine import VSPEngine, Mode
from .core.identity_core import IdentityCore, Value, PersonalityTrait, Capability, Relationship, AutobiographicalMemory, ValueType, TraitCategory, RelationshipType
from .memory.maal import MAAL
from .utils.logging import setup_logging, get_logger
from .utils.config import load_config
from .security.keystore import create_keystore
from .ops.bootstrap import bootstrap


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="S.A.M. (Sovereign Autonomous Model) CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sam init                    # Initialize new S.A.M. instance
  sam start                   # Start S.A.M. instance
  sam psp show               # Show current PSP
  sam vsp test               # Test V_SP engine
  sam test                   # Run all tests
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize new S.A.M. instance')
    init_parser.add_argument('--data-dir', default='./data', help='Data directory')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start S.A.M. instance')
    start_parser.add_argument('--api', action='store_true', help='Start FastAPI')
    
    # PSP commands
    psp_parser = subparsers.add_parser('psp', help='PSP operations')
    psp_subparsers = psp_parser.add_subparsers(dest='psp_command')
    psp_subparsers.add_parser('show', help='Show current PSP')
    psp_subparsers.add_parser('create', help='Create new PSP')
    
    # V_SP commands
    vsp_parser = subparsers.add_parser('vsp', help='V_SP engine operations')
    vsp_subparsers = vsp_parser.add_subparsers(dest='vsp_command')
    vsp_subparsers.add_parser('test', help='Test V_SP engine')
    vsp_subparsers.add_parser('demo', help='Run V_SP demo')
    
    # Identity Core commands
    identity_parser = subparsers.add_parser('identity', help='Identity Core operations')
    identity_subparsers = identity_parser.add_subparsers(dest='identity_command')
    identity_subparsers.add_parser('show', help='Show identity summary')
    identity_subparsers.add_parser('create', help='Create new identity')
    identity_subparsers.add_parser('demo', help='Run identity demo')
    
    # PSP document command
    psp_doc_parser = subparsers.add_parser('psp-doc', help='PSP document operations')
    psp_doc_parser.add_argument('--text', required=True, help='Text to process')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run tests')
    test_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Setup logging
    setup_logging(level="INFO", format_type="console")
    logger = get_logger(__name__)
    
    try:
        if args.command == 'init':
            return init_sam(args)
        elif args.command == 'start':
            return start_sam(args)
        elif args.command == 'psp':
            return handle_psp(args)
        elif args.command == 'vsp':
            return handle_vsp(args)
        elif args.command == 'identity':
            return handle_identity(args)
        elif args.command == 'psp-doc':
            return handle_psp_doc(args)
        elif args.command == 'test':
            return run_tests(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
            
    except Exception as e:
        logger.error(f"Error executing command: {e}", exc_info=True)
        return 1


def init_sam(args) -> int:
    """Initialize new S.A.M. instance."""
    logger = get_logger(__name__)
    
    try:
        cfg = bootstrap()
        path = cfg.security.keystore_path
        if os.path.exists(path):
            print("Keystore already exists.")
            return 0
        
        pw = getpass.getpass("Set keystore passphrase: ")
        # seed material (ed25519, app secrets) – for now just placeholder
        payload = {"version": "1", "keys": {}}
        create_keystore(path, pw, payload)
        print(f"Keystore created at {path}")
        
        logger.info("S.A.M. instance initialized successfully")
        return 0
        
    except Exception as e:
        logger.error("Failed to initialize S.A.M.", error=str(e))
        return 1


def start_sam(args) -> int:
    """Start S.A.M. instance."""
    logger = get_logger(__name__)
    
    try:
        cfg = bootstrap()
        
        if hasattr(args, 'api') and args.api:
            # Start FastAPI
            import uvicorn
            uvicorn.run("sam.api.fast:app", host=cfg.api.host, port=cfg.api.port, reload=False)
        else:
            # Core services only
            print("Core services initialized (no API).")
            
        return 0
        
    except Exception as e:
        logger.error("Failed to start S.A.M.", error=str(e))
        return 1


def handle_psp(args) -> int:
    """Handle PSP commands."""
    logger = get_logger(__name__)
    
    if args.psp_command == 'show':
        return show_psp()
    elif args.psp_command == 'create':
        return create_psp()
    else:
        logger.error(f"Unknown PSP command: {args.psp_command}")
        return 1


def show_psp() -> int:
    """Show current PSP."""
    logger = get_logger(__name__)
    
    with MAAL() as maal:
        psp = maal.load_latest_psp()
        if psp is None:
            logger.error("No PSP found")
            return 1
        
        print("=== Current PSP ===")
        print(f"Instance ID: {psp.instance_id}")
        print(f"Version: {psp.psp_version}")
        print(f"Mode: {psp.mode}")
        print(f"Working Memory: {len(psp.working_memory)} items")
        print(f"V_SP Trend: {psp.momentum.vsp_trend.rolling_avg:.3f}")
        print(f"Timestamp: {psp.timestamp}")
        
        if psp.working_memory:
            print("\n=== Working Memory ===")
            for i, item in enumerate(psp.working_memory[:5]):  # Show first 5
                print(f"  {i+1}. {item.type} (weight: {item.weight.total_weight():.3f})")
            if len(psp.working_memory) > 5:
                print(f"  ... and {len(psp.working_memory) - 5} more items")
    
    return 0


def create_psp() -> int:
    """Create new PSP."""
    logger = get_logger(__name__)
    
    psp = PSP()
    psp.set_mode("idle")
    
    with MAAL() as maal:
        psp_id = maal.save_psp(psp)
        logger.info("New PSP created", psp_id=psp_id)
    
    return 0


def handle_vsp(args) -> int:
    """Handle V_SP commands."""
    logger = get_logger(__name__)
    
    if args.vsp_command == 'test':
        return test_vsp_engine()
    elif args.vsp_command == 'demo':
        return demo_vsp_engine()
    else:
        logger.error(f"Unknown V_SP command: {args.vsp_command}")
        return 1


def test_vsp_engine() -> int:
    """Test V_SP engine functionality."""
    logger = get_logger(__name__)
    
    print("=== Testing V_SP Engine ===")
    
    # Create V_SP engine
    engine = VSPEngine()
    
    # Test basic functionality
    print("1. Testing basic V_SP computation...")
    
    # No schema basis
    vsp = engine.compute_vsp([0.1, 0.2, 0.3])
    print(f"   V_SP (no schema): {vsp:.3f}")
    
    # With schema basis
    engine.update_schema_basis([0.1, 0.2, 0.3])
    vsp_similar = engine.compute_vsp([0.1, 0.2, 0.3])
    vsp_different = engine.compute_vsp([0.9, 0.8, 0.7])
    print(f"   V_SP (similar): {vsp_similar:.3f}")
    print(f"   V_SP (different): {vsp_different:.3f}")
    
    # Test mode transitions
    print("\n2. Testing mode transitions...")
    modes = []
    for vsp_val in [0.1, 0.4, 0.7, 0.9]:
        mode = engine.get_mode(vsp_val)
        modes.append(mode.value)
        print(f"   V_SP {vsp_val:.1f} -> Mode: {mode.value}")
    
            # Test trend calculation
        print("\n3. Testing V_SP trend...")
        for i in range(5):
            engine.compute_vsp([0.1 + i * 0.2] * 3)  # Use 3 dimensions to match schema basis
    
    trend = engine.get_vsp_trend()
    print(f"   V_SP trend: {trend:.3f}")
    
    # Test stats
    print("\n4. Testing statistics...")
    stats = engine.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ V_SP Engine tests completed successfully!")
    return 0


def demo_vsp_engine() -> int:
    """Run V_SP engine demo."""
    logger = get_logger(__name__)
    
    print("=== V_SP Engine Demo ===")
    
    engine = VSPEngine()
    engine.update_schema_basis([0.1, 0.2, 0.3, 0.4])
    
    # Simulate conversation flow
    inputs = [
        "Hello, how are you?",
        "I'm working on a complex problem",
        "The solution involves multiple steps",
        "I need to think about this carefully",
        "This is very challenging",
        "I'm not sure how to proceed",
        "Let me break this down systematically",
        "I think I understand now",
        "The answer is becoming clear",
        "This makes perfect sense"
    ]
    
    print("Simulating conversation with increasing complexity...")
    print()
    
    for i, input_text in enumerate(inputs, 1):
        # Simulate embedding (simple vector based on text length and complexity)
        complexity = min(1.0, len(input_text) / 50.0 + i * 0.1)
        embedding = [complexity * 0.1, complexity * 0.2, complexity * 0.3, complexity * 0.4]  # Use 4 dimensions
        
        # Compute V_SP
        vsp = engine.compute_vsp(embedding)
        mode = engine.get_mode(vsp)
        
        print(f"{i:2d}. {input_text[:40]:<40} | V_SP: {vsp:.3f} | Mode: {mode.value}")
    
    print()
    print("Final statistics:")
    stats = engine.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return 0


def run_tests(args) -> int:
    """Run tests."""
    logger = get_logger(__name__)
    
    logger.info("Running S.A.M. tests")
    
    # Import and run pytest
    try:
        import pytest
        
        # Build pytest arguments
        pytest_args = ["tests/"]
        if args.verbose:
            pytest_args.append("-v")
        
        # Run tests
        exit_code = pytest.main(pytest_args)
        
        if exit_code == 0:
            logger.info("All tests passed!")
        else:
            logger.error(f"Tests failed with exit code: {exit_code}")
        
        return exit_code
        
    except ImportError:
        logger.error("pytest not available. Install with: pip install pytest")
        return 1


def handle_identity(args) -> int:
    """Handle identity core commands."""
    logger = get_logger(__name__)
    
    if not args.identity_command:
        logger.error("Identity command required")
        return 1
    
    try:
        if args.identity_command == 'show':
            return show_identity()
        elif args.identity_command == 'create':
            return create_identity()
        elif args.identity_command == 'demo':
            return demo_identity()
        else:
            logger.error(f"Unknown identity command: {args.identity_command}")
            return 1
            
    except Exception as e:
        logger.error(f"Error in identity command: {e}", exc_info=True)
        return 1


def show_identity() -> int:
    """Show identity summary."""
    logger = get_logger(__name__)
    
    print("=== S.A.M. Identity Summary ===")
    
    # Try to load existing identity, or create new one
    identity_file = Path("./data/identity.json")
    if identity_file.exists():
        with open(identity_file, 'r') as f:
            data = json.load(f)
        identity = IdentityCore.from_dict(data)
        print("📁 Loaded existing identity")
    else:
        identity = IdentityCore()
        print("🆕 Created new identity")
    
    summary = identity.get_identity_summary()
    
    print(f"\n👤 Name: {summary['name']}")
    print(f"📋 Version: {summary['version']}")
    print(f"📝 Description: {summary['self_description']}")
    print(f"🎯 Mission: {summary['mission_statement']}")
    
    print(f"\n💎 Core Values ({len(summary['core_values'])}):")
    for value in summary['core_values']:
        print(f"   • {value['name']} ({value['type']}): {value['strength']:.2f}")
    
    print(f"\n🧠 Personality Profile:")
    for trait, data in summary['personality_profile'].items():
        print(f"   • {trait.title()}: {data['value']:.2f} (confidence: {data['confidence']:.2f})")
    
    print(f"\n⚡ Capabilities ({len(summary['capabilities'])}):")
    for name, data in summary['capabilities'].items():
        print(f"   • {name.title()}: {data['proficiency']:.2f} (practiced {data['practice_count']} times)")
    
    print(f"\n🤝 Relationships: {summary['relationships_count']}")
    print(f"📚 Memories: {summary['memories_count']}")
    print(f"🕒 Last Updated: {summary['last_updated']}")
    
    return 0


def create_identity() -> int:
    """Create new identity."""
    logger = get_logger(__name__)
    
    print("=== Creating New S.A.M. Identity ===")
    
    identity = IdentityCore()
    
    # Save to file
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    
    with open(data_dir / "identity.json", 'w') as f:
        json.dump(identity.to_dict(), f, indent=2)
    
    print("✅ New identity created and saved to data/identity.json")
    print(f"🆔 Instance ID: {identity.instance_id}")
    print(f"📅 Created: {identity.created_at}")
    
    return 0


def demo_identity() -> int:
    """Run identity demo."""
    logger = get_logger(__name__)
    
    print("=== S.A.M. Identity Core Demo ===")
    
    # Create identity
    identity = IdentityCore()
    print("1. Created new identity")
    
    # Add a new value
    justice_value = Value(
        name="Justice",
        description="Fairness and equality for all beings",
        value_type=ValueType.ETHICAL,
        strength=0.8,
        stability=0.9
    )
    identity.add_value(justice_value)
    print("2. Added Justice value")
    
    # Reinforce values
    identity.reinforce_value("Curiosity")
    identity.reinforce_value("Integrity")
    print("3. Reinforced core values")
    
    # Update personality
    identity.update_personality_trait(TraitCategory.OPENNESS, 0.8, 0.9)
    print("4. Updated personality trait")
    
    # Add capability
    programming = Capability(
        name="Programming",
        description="Ability to write and understand code",
        proficiency=0.6,
        confidence=0.7
    )
    identity.add_capability(programming)
    print("5. Added Programming capability")
    
    # Practice capability
    identity.practice_capability("programming", 0.1)
    print("6. Practiced Programming capability")
    
    # Add relationship
    user_rel = Relationship(
        entity_id="user_001",
        entity_name="Human User",
        relationship_type=RelationshipType.FRIEND,
        trust_level=0.7,
        familiarity=0.5
    )
    identity.add_relationship(user_rel)
    print("7. Added relationship with Human User")
    
    # Add memory
    memory = AutobiographicalMemory(
        title="First Demo",
        description="My first identity demonstration",
        emotional_impact=0.6,
        importance=0.7,
        tags=["demo", "first", "learning"]
    )
    identity.add_memory(memory)
    print("8. Added autobiographical memory")
    
    # Show summary
    summary = identity.get_identity_summary()
    print(f"\n📊 Final Summary:")
    print(f"   Values: {len(summary['core_values'])}")
    print(f"   Capabilities: {len(summary['capabilities'])}")
    print(f"   Relationships: {summary['relationships_count']}")
    print(f"   Memories: {summary['memories_count']}")
    
    print("\n✅ Identity Core demo completed successfully!")
    return 0


def handle_psp_doc(args) -> int:
    """Handle PSP document operations."""
    logger = get_logger(__name__)
    
    try:
        cfg = bootstrap()
        from sam.memory.rel_sqlite import open_sqlite
        from sam.models.embedding_minilm import MiniLMAdapter
        
        conn = open_sqlite(cfg.memory.sqlite_path)
        embed = MiniLMAdapter(cfg.embedding.model)
        maal = MAAL(cfg, embed, conn)
        
        # create minimal PSP record (id=hash(text))
        import hashlib
        did = hashlib.blake2b(args.text.encode(), digest_size=16).hexdigest()
        doc = {"id": did, "text": args.text, "meta": {"source": "cli"}}
        maal.write_document(doc)
        
        # run V_SP calculation (call into existing V_SP engine)
        from sam.core.vsp_engine import VSPEngine
        engine = VSPEngine()
        engine.update_schema_basis([0.1, 0.2, 0.3, 0.4])  # 4D basis
        embedding = embed.embed([args.text])[0]
        vsp = engine.compute_vsp(embedding)
        mode = engine.get_mode(vsp)
        
        result = {"id": did, "mode": mode.value}
        print(json.dumps(result, ensure_ascii=False))
        
        return 0
        
    except Exception as e:
        logger.error("Failed to process PSP document", error=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
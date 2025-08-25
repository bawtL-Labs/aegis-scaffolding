"""
Command-line interface for S.A.M. (Sovereign Autonomous Model)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .core.psp import PSP
from .core.vsp_engine import VSPEngine, Mode
from .memory.maal import MAAL
from .utils.logging import setup_logging, get_logger


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
    start_parser.add_argument('--config', default='./sam/ops/config.yaml', help='Config file')
    
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
    
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Initializing S.A.M. instance", data_dir=str(data_dir))
    
    # Create initial PSP
    psp = PSP()
    psp.set_mode("idle")
    
    # Initialize MAAL
    with MAAL(
        sqlite_path=str(data_dir / "sam.db"),
        lancedb_path=str(data_dir / "vectors.lancedb")
    ) as maal:
        # Save initial PSP
        psp_id = maal.save_psp(psp)
        logger.info("Initial PSP saved", psp_id=psp_id)
    
    logger.info("S.A.M. instance initialized successfully")
    return 0


def start_sam(args) -> int:
    """Start S.A.M. instance."""
    logger = get_logger(__name__)
    
    logger.info("Starting S.A.M. instance")
    
    # Load existing PSP
    with MAAL() as maal:
        psp = maal.load_latest_psp()
        if psp is None:
            logger.error("No PSP found. Run 'sam init' first.")
            return 1
        
        logger.info("PSP loaded", 
                   instance_id=psp.instance_id,
                   mode=psp.mode,
                   working_memory_size=len(psp.working_memory))
    
    logger.info("S.A.M. instance started successfully")
    return 0


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


if __name__ == "__main__":
    sys.exit(main())
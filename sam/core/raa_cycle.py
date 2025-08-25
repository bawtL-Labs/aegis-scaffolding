"""
RAA (Reflect → Abstract → Act) Metabolic Cycle

Implements the core cognitive rhythm with load-adaptive pacing and hysteresis.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

from ..utils.logging import get_logger


class RAAPhase(Enum):
    """RAA cycle phases."""
    REFLECT = "reflect"
    ABSTRACT = "abstract"
    ACT = "act"


class RAACycle:
    """
    RAA Metabolic Cycle - Core cognitive rhythm for S.A.M.
    
    Maintains Reflect/Abstract/Act rhythm across modes with adjustable
    pacing and CDP hooks for deep deliberation.
    """
    
    def __init__(self, 
                 base_cycle_ms: int = 1000,
                 mode_multipliers: Optional[Dict[str, float]] = None):
        """
        Initialize RAA cycle.
        
        Args:
            base_cycle_ms: Base cycle duration in milliseconds
            mode_multipliers: Mode-specific cycle multipliers
        """
        self.logger = get_logger(__name__)
        
        self.base_cycle_ms = base_cycle_ms
        self.mode_multipliers = mode_multipliers or {
            "idle": 2.0,    # Slower in idle
            "flow": 1.0,    # Normal pace
            "deep": 0.5,    # Faster in deep
            "crisis": 0.2   # Very fast in crisis
        }
        
        self.current_phase = RAAPhase.REFLECT
        self.last_phase_change = datetime.now()
        self.cycle_count = 0
        
        self.logger.info("RAA Cycle initialized", 
                        base_cycle_ms=base_cycle_ms,
                        mode_multipliers=self.mode_multipliers)
    
    def advance_cycle(self, current_mode: str, vsp_value: float) -> RAAPhase:
        """
        Advance the RAA cycle.
        
        Args:
            current_mode: Current cognitive mode
            vsp_value: Current V_SP value
            
        Returns:
            Current phase
        """
        current_time = datetime.now()
        cycle_duration = self._get_cycle_duration(current_mode)
        
        # Check if it's time to advance
        if (current_time - self.last_phase_change).total_seconds() * 1000 >= cycle_duration:
            self._advance_phase()
            self.last_phase_change = current_time
            self.cycle_count += 1
            
            self.logger.debug("RAA phase advanced", 
                            phase=self.current_phase.value,
                            cycle_count=self.cycle_count,
                            mode=current_mode)
        
        return self.current_phase
    
    def _get_cycle_duration(self, mode: str) -> int:
        """Get cycle duration for current mode."""
        multiplier = self.mode_multipliers.get(mode, 1.0)
        return int(self.base_cycle_ms * multiplier)
    
    def _advance_phase(self) -> None:
        """Advance to next phase in cycle."""
        if self.current_phase == RAAPhase.REFLECT:
            self.current_phase = RAAPhase.ABSTRACT
        elif self.current_phase == RAAPhase.ABSTRACT:
            self.current_phase = RAAPhase.ACT
        else:  # ACT
            self.current_phase = RAAPhase.REFLECT
    
    def get_phase_progress(self) -> float:
        """Get progress through current phase (0.0 to 1.0)."""
        current_time = datetime.now()
        elapsed = (current_time - self.last_phase_change).total_seconds() * 1000
        # Assume we're in flow mode for progress calculation
        cycle_duration = self._get_cycle_duration("flow")
        return min(1.0, elapsed / cycle_duration)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAA cycle statistics."""
        return {
            "current_phase": self.current_phase.value,
            "cycle_count": self.cycle_count,
            "phase_progress": self.get_phase_progress(),
            "last_phase_change": self.last_phase_change.isoformat(),
        }
    
    def reset(self) -> None:
        """Reset RAA cycle."""
        self.current_phase = RAAPhase.REFLECT
        self.last_phase_change = datetime.now()
        self.cycle_count = 0
        self.logger.info("RAA cycle reset")
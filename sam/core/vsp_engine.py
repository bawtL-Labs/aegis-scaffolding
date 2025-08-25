"""
V_SP Engine - Schema Perturbation Value computation and mode control.

Computes phase dissonance between new inputs and existing schemas,
driving mode shifts and learning with hysteresis.
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import numpy as np
from pydantic import BaseModel, Field

from ..utils.logging import get_logger


class Mode(Enum):
    """Cognitive modes for S.A.M."""
    IDLE = "idle"
    FLOW = "flow"
    DEEP = "deep"
    CRISIS = "crisis"


@dataclass
class Thresholds:
    """Mode transition thresholds with hysteresis."""
    idle_to_flow: float = 0.3
    flow_to_idle: float = 0.2
    flow_to_deep: float = 0.6
    deep_to_flow: float = 0.5
    deep_to_crisis: float = 0.8
    crisis_to_deep: float = 0.7


@dataclass
class HysteresisConfig:
    """Hysteresis configuration to prevent oscillation."""
    debounce_ms: int = 1000
    trend_decay: float = 0.95
    rolling_window: int = 10


@dataclass
class LensingConfig:
    """Emotional and causal lensing configuration."""
    emotion_weight: float = 0.3
    causal_weight: float = 0.2
    temporal_weight: float = 0.1


class VSPEngine:
    """
    V_SP Engine - Computes schema perturbation values and manages mode transitions.
    
    The V_SP (Schema Perturbation) value measures phase dissonance between
    new inputs and existing schemas, driving cognitive mode transitions.
    """
    
    def __init__(self, 
                 thresholds: Optional[Thresholds] = None,
                 hysteresis: Optional[HysteresisConfig] = None,
                 lensing: Optional[LensingConfig] = None):
        """
        Initialize V_SP Engine.
        
        Args:
            thresholds: Mode transition thresholds
            hysteresis: Hysteresis configuration
            lensing: Lensing configuration
        """
        self.logger = get_logger(__name__)
        
        self.thresholds = thresholds or Thresholds()
        self.hysteresis = hysteresis or HysteresisConfig()
        self.lensing = lensing or LensingConfig()
        
        # State tracking
        self.current_mode = Mode.IDLE
        self.last_mode_change = time.time()
        self.vsp_history: List[float] = []
        self.schema_basis: Optional[np.ndarray] = None
        
        self.logger.info("V_SP Engine initialized", 
                        thresholds=self.thresholds,
                        hysteresis=self.hysteresis,
                        lensing=self.lensing)
    
    def compute_vsp(self, 
                   input_vector: List[float],
                   schema_basis: Optional[List[float]] = None,
                   emotional_lensing: Optional[List[float]] = None,
                   causal_context: Optional[Dict[str, float]] = None,
                   temporal_context: Optional[float] = None) -> float:
        """
        Compute V_SP (Schema Perturbation) value.
        
        Args:
            input_vector: Input embedding vector
            schema_basis: Current schema basis vector (centroid)
            emotional_lensing: Emotional state vector
            causal_context: Causal context weights
            temporal_context: Temporal context factor
            
        Returns:
            V_SP value between 0.0 and 1.0
        """
        if not input_vector:
            return 0.0
        
        # Convert to numpy arrays
        input_vec = np.array(input_vector, dtype=np.float32)
        
        # Use provided schema basis or current one
        if schema_basis is not None:
            schema_vec = np.array(schema_basis, dtype=np.float32)
        elif self.schema_basis is not None:
            schema_vec = self.schema_basis
        else:
            # No schema basis available, return high perturbation
            return 0.8
        
        # Normalize vectors
        input_vec = self._normalize_vector(input_vec)
        schema_vec = self._normalize_vector(schema_vec)
        
        # Compute cosine similarity (phase similarity)
        cosine_sim = np.dot(input_vec, schema_vec)
        phase_similarity = max(0.0, cosine_sim)  # Clamp to [0, 1]
        
        # Compute lensing modifier
        lensing_modifier = self._compute_lensing_modifier(
            emotional_lensing, causal_context, temporal_context
        )
        
        # V_SP formula: (1 - phase_similarity) * (1 + α|L|)
        # where α is the lensing weight and L is the lensing modifier
        vsp = (1.0 - phase_similarity) * (1.0 + self.lensing.emotion_weight * abs(lensing_modifier))
        
        # Clamp to [0, 1]
        vsp = max(0.0, min(1.0, vsp))
        
        # Update history
        self._update_history(vsp)
        
        self.logger.debug("V_SP computed", 
                         vsp=vsp,
                         phase_similarity=phase_similarity,
                         lensing_modifier=lensing_modifier)
        
        return vsp
    
    def _normalize_vector(self, vec: np.ndarray) -> np.ndarray:
        """Normalize vector to unit length."""
        norm = np.linalg.norm(vec)
        if norm == 0:
            return vec
        return vec / norm
    
    def _compute_lensing_modifier(self,
                                 emotional_lensing: Optional[List[float]] = None,
                                 causal_context: Optional[Dict[str, float]] = None,
                                 temporal_context: Optional[float] = None) -> float:
        """Compute lensing modifier from emotional, causal, and temporal factors."""
        modifier = 0.0
        
        # Emotional lensing
        if emotional_lensing:
            # Use valence-arousal model (first two dimensions)
            if len(emotional_lensing) >= 2:
                valence = emotional_lensing[0]  # [-1, 1]
                arousal = emotional_lensing[1]  # [-1, 1]
                emotion_modifier = (valence + arousal) / 2.0
                modifier += self.lensing.emotion_weight * emotion_modifier
        
        # Causal context
        if causal_context:
            # Weight by causal relationships
            causal_weight = sum(causal_context.values()) / len(causal_context)
            modifier += self.lensing.causal_weight * causal_weight
        
        # Temporal context
        if temporal_context is not None:
            # Recent events have higher weight
            modifier += self.lensing.temporal_weight * temporal_context
        
        return modifier
    
    def _update_history(self, vsp: float) -> None:
        """Update V_SP history with rolling window."""
        self.vsp_history.append(vsp)
        
        # Maintain rolling window
        if len(self.vsp_history) > self.hysteresis.rolling_window:
            self.vsp_history.pop(0)
    
    def get_mode(self, vsp: float) -> Mode:
        """
        Determine cognitive mode based on V_SP value and hysteresis.
        
        Args:
            vsp: Current V_SP value
            
        Returns:
            Cognitive mode
        """
        # Check debounce period
        current_time = time.time()
        if current_time - self.last_mode_change < (self.hysteresis.debounce_ms / 1000.0):
            return self.current_mode
        
        # Determine target mode based on thresholds
        target_mode = self._get_target_mode(vsp)
        
        # Apply hysteresis
        if target_mode != self.current_mode:
            # Check if transition is allowed
            if self._should_transition(vsp, target_mode):
                old_mode = self.current_mode
                self.current_mode = target_mode
                self.last_mode_change = current_time
                
                self.logger.info("Mode transition", 
                               old_mode=old_mode.value,
                               new_mode=target_mode.value,
                               vsp=vsp)
        
        return self.current_mode
    
    def _get_target_mode(self, vsp: float) -> Mode:
        """Get target mode based on V_SP value."""
        if vsp >= self.thresholds.deep_to_crisis:
            return Mode.CRISIS
        elif vsp >= self.thresholds.flow_to_deep:
            return Mode.DEEP
        elif vsp >= self.thresholds.idle_to_flow:
            return Mode.FLOW
        else:
            return Mode.IDLE
    
    def _should_transition(self, vsp: float, target_mode: Mode) -> bool:
        """Check if mode transition should occur based on hysteresis."""
        current_mode = self.current_mode
        
        # Crisis mode has special handling
        if current_mode == Mode.CRISIS:
            return vsp <= self.thresholds.crisis_to_deep
        elif target_mode == Mode.CRISIS:
            return vsp >= self.thresholds.deep_to_crisis
        
        # Normal hysteresis logic
        if current_mode == Mode.IDLE and target_mode == Mode.FLOW:
            return vsp >= self.thresholds.idle_to_flow
        elif current_mode == Mode.FLOW and target_mode == Mode.IDLE:
            return vsp <= self.thresholds.flow_to_idle
        elif current_mode == Mode.FLOW and target_mode == Mode.DEEP:
            return vsp >= self.thresholds.flow_to_deep
        elif current_mode == Mode.DEEP and target_mode == Mode.FLOW:
            return vsp <= self.thresholds.deep_to_flow
        
        return False
    
    def get_vsp_trend(self) -> float:
        """
        Get V_SP trend using exponential decay.
        
        Returns:
            Rolling average V_SP value
        """
        if not self.vsp_history:
            return 0.0
        
        # Simple exponential decay
        trend = 0.0
        weight = 1.0
        total_weight = 0.0
        
        for vsp in reversed(self.vsp_history):
            trend += vsp * weight
            total_weight += weight
            weight *= self.hysteresis.trend_decay
        
        return trend / total_weight if total_weight > 0 else 0.0
    
    def update_schema_basis(self, schema_basis: List[float]) -> None:
        """
        Update the schema basis vector.
        
        Args:
            schema_basis: New schema basis vector
        """
        self.schema_basis = np.array(schema_basis, dtype=np.float32)
        self.logger.info("Schema basis updated", 
                        dimension=len(schema_basis))
    
    def set_thresholds(self, thresholds: Thresholds) -> None:
        """Update mode transition thresholds."""
        self.thresholds = thresholds
        self.logger.info("Thresholds updated", thresholds=thresholds)
    
    def set_hysteresis(self, hysteresis: HysteresisConfig) -> None:
        """Update hysteresis configuration."""
        self.hysteresis = hysteresis
        self.logger.info("Hysteresis updated", hysteresis=hysteresis)
    
    def set_lensing(self, lensing: LensingConfig) -> None:
        """Update lensing configuration."""
        self.lensing = lensing
        self.logger.info("Lensing updated", lensing=lensing)
    
    def get_stats(self) -> Dict[str, float]:
        """Get V_SP engine statistics."""
        return {
            "current_mode": self.current_mode.value,
            "current_vsp": self.vsp_history[-1] if self.vsp_history else 0.0,
            "vsp_trend": self.get_vsp_trend(),
            "vsp_history_length": len(self.vsp_history),
            "time_since_mode_change": time.time() - self.last_mode_change,
        }
    
    def reset(self) -> None:
        """Reset V_SP engine state."""
        self.current_mode = Mode.IDLE
        self.last_mode_change = time.time()
        self.vsp_history.clear()
        self.schema_basis = None
        
        self.logger.info("V_SP Engine reset")
    
    def __str__(self) -> str:
        """String representation."""
        return f"VSPEngine(mode={self.current_mode.value}, vsp_trend={self.get_vsp_trend():.3f})"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return (f"VSPEngine(mode={self.current_mode.value}, "
                f"thresholds={self.thresholds}, "
                f"vsp_trend={self.get_vsp_trend():.3f}, "
                f"history_length={len(self.vsp_history)})")
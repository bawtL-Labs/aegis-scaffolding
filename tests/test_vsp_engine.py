"""
Tests for V_SP Engine implementation.
"""

import pytest
import time
import numpy as np

from sam.core.vsp_engine import VSPEngine, Mode, Thresholds, HysteresisConfig, LensingConfig


class TestVSPEngine:
    """Test V_SP Engine functionality."""
    
    def test_vsp_engine_initialization(self):
        """Test V_SP Engine initialization."""
        engine = VSPEngine()
        
        assert engine.current_mode == Mode.IDLE
        assert len(engine.vsp_history) == 0
        assert engine.schema_basis is None
    
    def test_vsp_computation_basic(self):
        """Test basic V_SP computation."""
        engine = VSPEngine()
        
        # Test with no schema basis (should return high perturbation)
        vsp = engine.compute_vsp([0.1, 0.2, 0.3])
        assert vsp == 0.8  # Default high perturbation
        
        # Test with schema basis
        schema_basis = [0.1, 0.2, 0.3]
        engine.update_schema_basis(schema_basis)
        
        # Similar input should have low V_SP
        vsp_low = engine.compute_vsp([0.1, 0.2, 0.3])
        assert vsp_low < 0.1
        
        # Different input should have high V_SP
        vsp_high = engine.compute_vsp([0.9, 0.8, 0.7])
        assert vsp_high > 0.5
    
    def test_vsp_computation_with_lensing(self):
        """Test V_SP computation with emotional and causal lensing."""
        engine = VSPEngine()
        schema_basis = [0.1, 0.2, 0.3, 0.4]
        engine.update_schema_basis(schema_basis)
        
        input_vec = [0.1, 0.2, 0.3, 0.4]
        
        # Without lensing
        vsp_base = engine.compute_vsp(input_vec)
        
        # With emotional lensing (high arousal)
        vsp_emotional = engine.compute_vsp(
            input_vec,
            emotional_lensing=[0.5, 0.8]  # High valence, high arousal
        )
        
        # Emotional lensing should increase V_SP
        assert vsp_emotional > vsp_base
        
        # With causal context
        vsp_causal = engine.compute_vsp(
            input_vec,
            causal_context={"cause": 0.7, "effect": 0.3}
        )
        
        # Causal context should also affect V_SP
        assert vsp_causal != vsp_base
    
    def test_mode_transitions(self):
        """Test mode transitions based on V_SP values."""
        engine = VSPEngine()
        
        # Start in IDLE mode
        assert engine.current_mode == Mode.IDLE
        
        # Low V_SP should stay in IDLE
        mode = engine.get_mode(0.1)
        assert mode == Mode.IDLE
        
        # High V_SP should transition to FLOW
        mode = engine.get_mode(0.4)
        assert mode == Mode.FLOW
        
        # Very high V_SP should transition to DEEP
        mode = engine.get_mode(0.7)
        assert mode == Mode.DEEP
        
        # Extremely high V_SP should transition to CRISIS
        mode = engine.get_mode(0.9)
        assert mode == Mode.CRISIS
    
    def test_hysteresis(self):
        """Test hysteresis prevents oscillation."""
        engine = VSPEngine()
        
        # Transition to FLOW
        engine.get_mode(0.4)
        assert engine.current_mode == Mode.FLOW
        
        # Small decrease should not cause immediate transition back
        mode = engine.get_mode(0.25)  # Below flow_to_idle threshold
        assert mode == Mode.FLOW  # Should stay in FLOW due to hysteresis
        
        # Larger decrease should cause transition
        mode = engine.get_mode(0.15)  # Well below threshold
        assert mode == Mode.IDLE
    
    def test_debounce(self):
        """Test debounce prevents rapid mode changes."""
        engine = VSPEngine()
        
        # First mode change
        engine.get_mode(0.4)
        assert engine.current_mode == Mode.FLOW
        
        # Immediate second change should be ignored due to debounce
        engine.get_mode(0.1)
        assert engine.current_mode == Mode.FLOW  # Should still be FLOW
    
    def test_vsp_trend(self):
        """Test V_SP trend calculation."""
        engine = VSPEngine()
        
        # Add some V_SP values
        vsp_values = [0.1, 0.3, 0.5, 0.7, 0.9]
        for vsp in vsp_values:
            engine.compute_vsp([vsp] * 10)  # Dummy input
        
        trend = engine.get_vsp_trend()
        
        # Trend should be weighted average with more recent values having higher weight
        assert 0.1 < trend < 0.9
        assert trend > 0.5  # Should be closer to recent values
    
    def test_schema_basis_update(self):
        """Test schema basis updates."""
        engine = VSPEngine()
        
        # Initial schema basis
        schema1 = [0.1, 0.2, 0.3]
        engine.update_schema_basis(schema1)
        
        # V_SP computation should use new basis
        vsp1 = engine.compute_vsp([0.1, 0.2, 0.3])
        
        # Update schema basis
        schema2 = [0.9, 0.8, 0.7]
        engine.update_schema_basis(schema2)
        
        # V_SP computation should now use different basis
        vsp2 = engine.compute_vsp([0.1, 0.2, 0.3])
        
        assert vsp1 != vsp2
    
    def test_configuration_updates(self):
        """Test configuration updates."""
        engine = VSPEngine()
        
        # Update thresholds
        new_thresholds = Thresholds(
            idle_to_flow=0.5,
            flow_to_idle=0.4,
            flow_to_deep=0.8,
            deep_to_flow=0.7,
            deep_to_crisis=0.9,
            crisis_to_deep=0.8
        )
        engine.set_thresholds(new_thresholds)
        
        # Test that new thresholds are used
        mode = engine.get_mode(0.45)  # Between old and new idle_to_flow
        assert mode == Mode.IDLE  # Should stay IDLE with new threshold
        
        # Update hysteresis
        new_hysteresis = HysteresisConfig(
            debounce_ms=2000,
            trend_decay=0.9,
            rolling_window=20
        )
        engine.set_hysteresis(new_hysteresis)
        
        # Update lensing
        new_lensing = LensingConfig(
            emotion_weight=0.5,
            causal_weight=0.3,
            temporal_weight=0.2
        )
        engine.set_lensing(new_lensing)
    
    def test_stats(self):
        """Test statistics gathering."""
        engine = VSPEngine()
        
        # Add some activity
        engine.compute_vsp([0.1, 0.2, 0.3])
        engine.get_mode(0.4)
        
        stats = engine.get_stats()
        
        assert "current_mode" in stats
        assert "current_vsp" in stats
        assert "vsp_trend" in stats
        assert "vsp_history_length" in stats
        assert "time_since_mode_change" in stats
        
        assert stats["current_mode"] == "flow"
        assert stats["vsp_history_length"] == 1
    
    def test_reset(self):
        """Test engine reset."""
        engine = VSPEngine()
        
        # Add some state
        engine.compute_vsp([0.1, 0.2, 0.3])
        engine.get_mode(0.4)
        engine.update_schema_basis([0.1, 0.2, 0.3])
        
        # Reset
        engine.reset()
        
        assert engine.current_mode == Mode.IDLE
        assert len(engine.vsp_history) == 0
        assert engine.schema_basis is None
    
    def test_vector_normalization(self):
        """Test vector normalization."""
        engine = VSPEngine()
        
        # Test with zero vector
        zero_vec = np.array([0.0, 0.0, 0.0])
        normalized = engine._normalize_vector(zero_vec)
        assert np.array_equal(normalized, zero_vec)
        
        # Test with non-zero vector
        vec = np.array([3.0, 4.0, 0.0])
        normalized = engine._normalize_vector(vec)
        norm = np.linalg.norm(normalized)
        assert abs(norm - 1.0) < 1e-6
    
    def test_lensing_modifier_computation(self):
        """Test lensing modifier computation."""
        engine = VSPEngine()
        
        # Test emotional lensing
        modifier = engine._compute_lensing_modifier(
            emotional_lensing=[0.5, 0.8]  # valence, arousal
        )
        expected = engine.lensing.emotion_weight * (0.5 + 0.8) / 2.0
        assert modifier == pytest.approx(expected)
        
        # Test causal context
        modifier = engine._compute_lensing_modifier(
            causal_context={"a": 0.3, "b": 0.7}
        )
        expected = engine.lensing.causal_weight * (0.3 + 0.7) / 2.0
        assert modifier == pytest.approx(expected)
        
        # Test temporal context
        modifier = engine._compute_lensing_modifier(
            temporal_context=0.6
        )
        expected = engine.lensing.temporal_weight * 0.6
        assert modifier == pytest.approx(expected)
        
        # Test combined
        modifier = engine._compute_lensing_modifier(
            emotional_lensing=[0.5, 0.8],
            causal_context={"a": 0.3},
            temporal_context=0.6
        )
        assert modifier != 0.0


class TestMode:
    """Test Mode enum."""
    
    def test_mode_values(self):
        """Test mode enum values."""
        assert Mode.IDLE.value == "idle"
        assert Mode.FLOW.value == "flow"
        assert Mode.DEEP.value == "deep"
        assert Mode.CRISIS.value == "crisis"
    
    def test_mode_comparison(self):
        """Test mode comparison."""
        assert Mode.IDLE != Mode.FLOW
        assert Mode.IDLE == Mode.IDLE


class TestThresholds:
    """Test Thresholds dataclass."""
    
    def test_default_thresholds(self):
        """Test default threshold values."""
        thresholds = Thresholds()
        
        assert thresholds.idle_to_flow == 0.3
        assert thresholds.flow_to_idle == 0.2
        assert thresholds.flow_to_deep == 0.6
        assert thresholds.deep_to_flow == 0.5
        assert thresholds.deep_to_crisis == 0.8
        assert thresholds.crisis_to_deep == 0.7
    
    def test_custom_thresholds(self):
        """Test custom threshold values."""
        thresholds = Thresholds(
            idle_to_flow=0.4,
            flow_to_deep=0.7
        )
        
        assert thresholds.idle_to_flow == 0.4
        assert thresholds.flow_to_deep == 0.7
        assert thresholds.flow_to_idle == 0.2  # Default value
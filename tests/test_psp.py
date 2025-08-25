"""
Tests for PSP (Prioritized State Packet) implementation.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from sam.core.psp import PSP, WorkingMemoryItem, WeightVector, MomentumVector
from sam.utils.crypto import generate_keypair


class TestPSP:
    """Test PSP functionality."""
    
    def test_psp_creation(self):
        """Test basic PSP creation."""
        psp = PSP()
        
        assert psp.psp_version == "1.1"
        assert psp.mode == "idle"
        assert len(psp.working_memory) == 0
        assert psp.instance_id is not None
    
    def test_working_memory_item(self):
        """Test working memory item creation and validation."""
        # Valid item
        item = WorkingMemoryItem(
            type="qualia_ref",
            weight=WeightVector(recency=0.5, perturbation=0.3, connectivity=0.2)
        )
        assert item.type == "qualia_ref"
        assert item.weight.total_weight() == pytest.approx(0.4 * 0.5 + 0.4 * 0.3 + 0.2 * 0.2)
        
        # Invalid type
        with pytest.raises(ValueError):
            WorkingMemoryItem(type="invalid_type")
    
    def test_add_working_memory_item(self):
        """Test adding items to working memory."""
        psp = PSP()
        
        item = WorkingMemoryItem(type="qualia_ref")
        psp.add_working_memory_item(item)
        
        assert len(psp.working_memory) == 1
        assert psp.working_memory[0].type == "qualia_ref"
    
    def test_working_memory_pruning(self):
        """Test working memory pruning when over limit."""
        psp = PSP()
        
        # Add more than 50 items
        for i in range(60):
            item = WorkingMemoryItem(
                type="qualia_ref",
                weight=WeightVector(recency=i/100.0, perturbation=0.1, connectivity=0.1)
            )
            psp.add_working_memory_item(item)
        
        # Should be pruned to 50 items
        assert len(psp.working_memory) == 50
        
        # Should keep highest weight items
        weights = [item.weight.total_weight() for item in psp.working_memory]
        assert weights == sorted(weights, reverse=True)
    
    def test_momentum_update(self):
        """Test momentum vector updates."""
        psp = PSP()
        
        # Update V_SP trend
        psp.update_momentum(vsp_value=0.5)
        assert psp.momentum.vsp_trend.rolling_avg == pytest.approx(0.5 * (1 - 0.95))
        
        # Update again
        psp.update_momentum(vsp_value=0.8)
        expected = 0.5 * 0.95 * (1 - 0.95) + 0.8 * (1 - 0.95)
        assert psp.momentum.vsp_trend.rolling_avg == pytest.approx(expected, rel=1e-2)
    
    def test_mode_transitions(self):
        """Test mode setting and validation."""
        psp = PSP()
        
        # Valid modes
        for mode in ["idle", "flow", "deep", "crisis"]:
            psp.set_mode(mode)
            assert psp.mode == mode
        
        # Invalid mode
        with pytest.raises(ValueError):
            psp.set_mode("invalid_mode")
    
    def test_checksums(self):
        """Test checksum generation and verification."""
        psp = PSP()
        
        # Initial checksums should be set
        assert psp.checksums.kv != ""
        assert psp.checksums.wm != ""
        
        # Checksums should be valid
        assert psp.verify_checksums()
        
        # Modify PSP and verify checksums change
        old_kv = psp.checksums.kv
        psp.set_mode("flow")
        assert psp.checksums.kv != old_kv
        assert psp.verify_checksums()
    
    def test_psp_serialization(self):
        """Test PSP serialization and deserialization."""
        psp = PSP()
        psp.set_mode("flow")
        psp.add_working_memory_item(WorkingMemoryItem(type="qualia_ref"))
        
        # Convert to dict and back
        psp_dict = psp.to_dict()
        psp_restored = PSP.from_dict(psp_dict)
        
        assert psp_restored.mode == psp.mode
        assert len(psp_restored.working_memory) == len(psp.working_memory)
        assert psp_restored.instance_id == psp.instance_id
    
    def test_psp_cloning(self):
        """Test PSP cloning."""
        psp = PSP()
        psp.set_mode("deep")
        psp.add_working_memory_item(WorkingMemoryItem(type="draft_schema"))
        
        psp_clone = psp.clone()
        
        assert psp_clone.mode == psp.mode
        assert len(psp_clone.working_memory) == len(psp.working_memory)
        assert psp_clone.instance_id == psp.instance_id
        
        # Modifying clone shouldn't affect original
        psp_clone.set_mode("crisis")
        assert psp.mode == "deep"
        assert psp_clone.mode == "crisis"
    
    def test_working_memory_filtering(self):
        """Test working memory filtering methods."""
        psp = PSP()
        
        # Add items of different types
        psp.add_working_memory_item(WorkingMemoryItem(type="qualia_ref"))
        psp.add_working_memory_item(WorkingMemoryItem(type="draft_schema"))
        psp.add_working_memory_item(WorkingMemoryItem(type="context"))
        psp.add_working_memory_item(WorkingMemoryItem(type="qualia_ref"))
        
        # Filter by type
        qualia_items = psp.get_working_memory_by_type("qualia_ref")
        assert len(qualia_items) == 2
        
        schema_items = psp.get_working_memory_by_type("draft_schema")
        assert len(schema_items) == 1
        
        # Filter by weight
        high_weight_items = psp.get_working_memory_by_weight(0.5)
        assert len(high_weight_items) == 0  # All items have low default weights
    
    @patch('sam.utils.crypto.sign_data')
    def test_psp_signing(self, mock_sign_data):
        """Test PSP signing functionality."""
        mock_sign_data.return_value = (b"fake_signature", b"fake_public_key")
        
        psp = PSP()
        private_key = b"fake_private_key"
        
        psp.sign_psp(private_key)
        
        assert psp.sign.sig == "fake_signature"
        assert psp.sign.pub == "fake_public_key"
        mock_sign_data.assert_called_once()
    
    def test_momentum_vector_validation(self):
        """Test momentum vector validation."""
        # Valid vector
        momentum = MomentumVector(
            dimensions=512,
            magnitude=0.5,
            direction=[0.1] * 512,
            confidence=0.8
        )
        assert momentum.dimensions == 512
        assert len(momentum.direction) == 512
        
        # Invalid direction length
        with pytest.raises(ValueError):
            MomentumVector(direction=[0.1] * 100)  # Wrong length


class TestWeightVector:
    """Test weight vector functionality."""
    
    def test_weight_calculation(self):
        """Test weight vector total weight calculation."""
        weight = WeightVector(recency=0.5, perturbation=0.3, connectivity=0.2)
        expected = 0.4 * 0.5 + 0.4 * 0.3 + 0.2 * 0.2
        assert weight.total_weight() == pytest.approx(expected)
    
    def test_weight_bounds(self):
        """Test weight vector bounds validation."""
        # Valid weights
        WeightVector(recency=0.0, perturbation=0.5, connectivity=1.0)
        
        # Invalid weights
        with pytest.raises(ValueError):
            WeightVector(recency=-0.1)
        
        with pytest.raises(ValueError):
            WeightVector(perturbation=1.1)
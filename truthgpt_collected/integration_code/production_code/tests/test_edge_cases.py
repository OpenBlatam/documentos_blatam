import pytest
import torch
import numpy as np
from typing import Dict, Any

from core.paper_base import BasePaperConfig, BasePaperModule, ValidationError
from research.paper_malto import MALTOModule, MALTOConfig
import torch.nn as nn


class SimpleModule(BasePaperModule):
    """Simple module for edge case testing."""
    
    def __init__(self, config: BasePaperConfig):
        super().__init__(config)
        self.linear = nn.Linear(config.hidden_dim, config.hidden_dim)
    
    def forward(self, hidden_states: torch.Tensor, **kwargs):
        self.validate_inputs(hidden_states, **kwargs)
        output = self.linear(hidden_states)
        metadata = {'output_mean': output.mean().item()}
        return output, metadata


class TestEdgeCases:
    """Tests para edge cases y casos límite."""
    
    def test_empty_batch_error(self, sample_config):
        """Test que batch vacío genera error."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(0, 10, 512)
        
        with pytest.raises(ValidationError, match="batch_size debe ser > 0"):
            module(hidden_states)
    
    def test_empty_sequence_error(self, sample_config):
        """Test que secuencia vacía genera error."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 0, 512)
        
        with pytest.raises(ValidationError, match="seq_len debe ser > 0"):
            module(hidden_states)
    
    def test_single_element_batch(self, sample_config):
        """Test con batch de un solo elemento."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(1, 10, 512)
        
        output, _ = module(hidden_states)
        assert output.shape == hidden_states.shape
    
    def test_single_element_sequence(self, sample_config):
        """Test con secuencia de un solo elemento."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 1, 512)
        
        output, _ = module(hidden_states)
        assert output.shape == hidden_states.shape
    
    def test_very_large_values(self, sample_config):
        """Test con valores muy grandes."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512) * 1e6
        
        output, _ = module(hidden_states)
        assert output.shape == hidden_states.shape
        assert not torch.isnan(output).any()
    
    def test_very_small_values(self, sample_config):
        """Test con valores muy pequeños."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512) * 1e-6
        
        output, _ = module(hidden_states)
        assert output.shape == hidden_states.shape
        assert not torch.isnan(output).any()
    
    def test_all_zeros(self, sample_config):
        """Test con tensor de ceros."""
        module = SimpleModule(sample_config)
        hidden_states = torch.zeros(2, 10, 512)
        
        output, _ = module(hidden_states)
        assert output.shape == hidden_states.shape
    
    def test_all_ones(self, sample_config):
        """Test con tensor de unos."""
        module = SimpleModule(sample_config)
        hidden_states = torch.ones(2, 10, 512)
        
        output, _ = module(hidden_states)
        assert output.shape == hidden_states.shape
    
    def test_extreme_positive_values(self, sample_config):
        """Test con valores extremadamente positivos."""
        module = SimpleModule(sample_config)
        hidden_states = torch.full((2, 10, 512), 1e10)
        
        with pytest.raises(ValidationError, match="contiene Inf"):
            module(hidden_states)
    
    def test_extreme_negative_values(self, sample_config):
        """Test con valores extremadamente negativos."""
        module = SimpleModule(sample_config)
        hidden_states = torch.full((2, 10, 512), -1e10)
        
        output, _ = module(hidden_states)
        assert output.shape == hidden_states.shape
    
    def test_mixed_precision(self, sample_config):
        """Test con diferentes precisiones."""
        module = SimpleModule(sample_config)
        
        for dtype in [torch.float16, torch.float32, torch.float64]:
            hidden_states = torch.randn(2, 10, 512, dtype=dtype)
            output, _ = module(hidden_states)
            assert output.dtype == dtype
    
    def test_gradient_flow(self, sample_config):
        """Test que los gradientes fluyen correctamente."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512, requires_grad=True)
        
        output, _ = module(hidden_states)
        loss = output.mean()
        loss.backward()
        
        assert hidden_states.grad is not None
        assert not torch.isnan(hidden_states.grad).any()
    
    def test_detached_tensors(self, sample_config):
        """Test con tensores detached."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512).detach()
        
        output, _ = module(hidden_states)
        assert output.shape == hidden_states.shape
    
    def test_non_contiguous_tensors(self, sample_config):
        """Test con tensores no contiguos."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 20, 512)[:, ::2, :]
        
        assert not hidden_states.is_contiguous()
        output, _ = module(hidden_states)
        assert output.shape == hidden_states.shape
    
    def test_malto_all_features_disabled_edge_case(self):
        """Test MALTO con todas las features deshabilitadas."""
        config = MALTOConfig(
            use_uncertainty_quantification=False,
            use_nli_validation=False,
            word_level_detection=False
        )
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        assert output.shape == hidden_states.shape
    
    def test_malto_extreme_thresholds(self):
        """Test MALTO con thresholds extremos."""
        config_zero = MALTOConfig(uncertainty_threshold=0.0)
        config_one = MALTOConfig(uncertainty_threshold=1.0)
        
        module_zero = MALTOModule(config_zero)
        module_one = MALTOModule(config_one)
        
        hidden_states = torch.randn(2, 10, 512)
        
        output_zero, metadata_zero = module_zero(hidden_states)
        output_one, metadata_one = module_one(hidden_states)
        
        assert output_zero.shape == output_one.shape
        assert metadata_zero['word_hallucination_ratio'] >= metadata_one['word_hallucination_ratio']
    
    def test_config_boundary_values(self):
        """Test config con valores en los límites."""
        config_min = BasePaperConfig(hidden_dim=1)
        config_max = BasePaperConfig(hidden_dim=32768)
        
        assert config_min.hidden_dim == 1
        assert config_max.hidden_dim == 32768
    
    def test_model_with_minimal_config(self):
        """Test modelo con configuración mínima."""
        config = BasePaperConfig(hidden_dim=1)
        module = SimpleModule(config)
        hidden_states = torch.randn(1, 1, 1)
        
        output, _ = module(hidden_states)
        assert output.shape == hidden_states.shape
    
    def test_repeated_forward_same_input(self, sample_config):
        """Test forward repetido con mismo input."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        
        outputs = []
        for _ in range(10):
            output, _ = module(hidden_states)
            outputs.append(output)
        
        assert len(outputs) == 10
        assert all(torch.allclose(outputs[0], out) for out in outputs[1:])




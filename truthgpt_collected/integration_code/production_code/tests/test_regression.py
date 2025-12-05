import pytest
import torch
import numpy as np
from typing import Dict, Any, List

from core.paper_base import BasePaperConfig, BasePaperModule
from research.paper_malto import MALTOModule, MALTOConfig
from research.paper_solar import SOLARModule, SOLARConfig
from research.paper_hademif import HaDeMiFModule, HaDeMiFConfig
import torch.nn as nn


class SimpleModule(BasePaperModule):
    """Simple module for regression testing."""
    
    def __init__(self, config: BasePaperConfig):
        super().__init__(config)
        self.linear = nn.Linear(config.hidden_dim, config.hidden_dim)
    
    def forward(self, hidden_states: torch.Tensor, **kwargs):
        self.validate_inputs(hidden_states, **kwargs)
        output = self.linear(hidden_states)
        metadata = {'output_mean': output.mean().item()}
        self._update_metrics(**metadata)
        return output, metadata


class TestRegression:
    """Tests de regresión para asegurar que cambios no rompen funcionalidad existente."""
    
    def test_basic_functionality_preserved(self, sample_config):
        """Test que funcionalidad básica se preserva."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert isinstance(metadata, dict)
        assert 'output_mean' in metadata
    
    def test_validation_still_works(self, sample_config):
        """Test que validación sigue funcionando."""
        module = SimpleModule(sample_config)
        
        with pytest.raises(Exception):
            module(torch.randn(2, 10, 256))
    
    def test_metrics_tracking_preserved(self, sample_config):
        """Test que tracking de métricas se preserva."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        
        module(hidden_states)
        module(hidden_states)
        
        assert module._forward_count == 2
        metrics = module.get_metrics()
        assert metrics['forward_count'] == 2
    
    def test_save_load_still_works(self, sample_config, temp_dir):
        """Test que save/load sigue funcionando."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        
        original_output, _ = module(hidden_states)
        
        model_path = temp_dir / "regression_model.pt"
        module.save_model(model_path)
        
        loaded_module = SimpleModule.load_model(model_path, config=sample_config)
        loaded_output, _ = loaded_module(hidden_states)
        
        torch.testing.assert_close(original_output, loaded_output, atol=1e-5, rtol=1e-5)
    
    def test_malto_backward_compatibility(self):
        """Test que MALTO mantiene compatibilidad hacia atrás."""
        try:
            config = MALTOConfig()
        except TypeError:
            config = MALTOConfig(
                use_uncertainty_quantification=True,
                use_nli_validation=True,
                word_level_detection=True,
                uncertainty_threshold=0.5,
                nli_threshold=0.3,
                mitigation_strength=0.4
            )
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert 'uncertainty_mean' in metadata
        assert 'nli_contradiction_score' in metadata
    
    def test_solar_backward_compatibility(self):
        """Test que SOLAR mantiene compatibilidad hacia atrás."""
        config = SOLARConfig()
        module = SOLARModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
    
    def test_hademif_backward_compatibility(self):
        """Test que HaDeMiF mantiene compatibilidad hacia atrás."""
        config = HaDeMiFConfig()
        module = HaDeMiFModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
    
    def test_output_consistency_across_runs(self, sample_config):
        """Test que outputs son consistentes entre runs."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        
        outputs = []
        for _ in range(5):
            output, _ = module(hidden_states)
            outputs.append(output)
        
        for i in range(1, len(outputs)):
            torch.testing.assert_close(outputs[0], outputs[i], atol=1e-6, rtol=1e-6)
    
    def test_parameter_count_consistency(self, sample_config):
        """Test que conteo de parámetros es consistente."""
        module = SimpleModule(sample_config)
        
        count1 = module.count_parameters()
        count2 = module.count_parameters()
        
        assert count1 == count2
    
    def test_model_info_consistency(self, sample_config):
        """Test que model_info es consistente."""
        module = SimpleModule(sample_config)
        
        info1 = module.get_model_info()
        info2 = module.get_model_info()
        
        assert info1['total_parameters'] == info2['total_parameters']
        assert info1['trainable_parameters'] == info2['trainable_parameters']
    
    def test_config_serialization_consistency(self, temp_dir):
        """Test que serialización de config es consistente."""
        config = BasePaperConfig(hidden_dim=512)
        
        config_path = temp_dir / "regression_config.json"
        config.save(config_path)
        
        loaded_config1 = BasePaperConfig.load(config_path)
        loaded_config2 = BasePaperConfig.load(config_path)
        
        assert loaded_config1.hidden_dim == loaded_config2.hidden_dim
        assert loaded_config1.to_dict() == loaded_config2.to_dict()
    
    def test_error_handling_preserved(self, sample_config):
        """Test que manejo de errores se preserva."""
        module = SimpleModule(sample_config)
        
        with pytest.raises(Exception):
            module(torch.randn(0, 10, 512))
        
        with pytest.raises(Exception):
            module(torch.randn(2, 0, 512))
        
        with pytest.raises(Exception):
            module(torch.randn(2, 10, 256))


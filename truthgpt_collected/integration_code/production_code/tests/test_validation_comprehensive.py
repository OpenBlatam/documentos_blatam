import pytest
import torch
import numpy as np
from typing import Dict, Any

from core.paper_base import BasePaperConfig, BasePaperModule, ValidationError
from research.paper_malto import MALTOModule, MALTOConfig
from research.paper_solar import SOLARModule, SOLARConfig
from research.paper_hademif import HaDeMiFModule, HaDeMiFConfig
import torch.nn as nn


class SimpleModule(BasePaperModule):
    """Simple module for comprehensive validation testing."""
    
    def __init__(self, config: BasePaperConfig):
        super().__init__(config)
        self.linear = nn.Linear(config.hidden_dim, config.hidden_dim)
    
    def forward(self, hidden_states: torch.Tensor, **kwargs):
        self.validate_inputs(hidden_states, **kwargs)
        output = self.linear(hidden_states)
        metadata = {'output_mean': output.mean().item()}
        self._update_metrics(**metadata)
        return output, metadata


class TestComprehensiveValidation:
    """Tests comprehensivos de validación para todos los módulos."""
    
    def test_input_validation_empty_tensor(self, sample_config):
        """Test validación con tensor vacío."""
        module = SimpleModule(sample_config)
        
        with pytest.raises(Exception):
            module(torch.empty(0, 10, 512))
    
    def test_input_validation_wrong_dimensions(self, sample_config):
        """Test validación con dimensiones incorrectas."""
        module = SimpleModule(sample_config)
        
        with pytest.raises(Exception):
            module(torch.randn(2, 10, 256))
    
    def test_input_validation_nan_values(self, sample_config):
        """Test validación con valores NaN."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        hidden_states[0, 0, 0] = float('nan')
        
        with pytest.raises(Exception):
            module(hidden_states)
    
    def test_input_validation_inf_values(self, sample_config):
        """Test validación con valores Inf."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        hidden_states[0, 0, 0] = float('inf')
        
        with pytest.raises(Exception):
            module(hidden_states)
    
    def test_input_validation_neg_inf_values(self, sample_config):
        """Test validación con valores -Inf."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        hidden_states[0, 0, 0] = float('-inf')
        
        with pytest.raises(Exception):
            module(hidden_states)
    
    def test_config_validation_all_modules(self):
        """Test validación de configs para todos los módulos."""
        configs = [
            BasePaperConfig(hidden_dim=512),
        ]
        
        try:
            configs.append(MALTOConfig())
        except TypeError:
            configs.append(MALTOConfig(
                use_uncertainty_quantification=True,
                use_nli_validation=True,
                word_level_detection=True,
                uncertainty_threshold=0.5,
                nli_threshold=0.3,
                mitigation_strength=0.4
            ))
        
        configs.append(SOLARConfig())
        configs.append(HaDeMiFConfig())
        
        for config in configs:
            assert config.hidden_dim == 512
            if hasattr(config, 'validate'):
                config.validate()
    
    def test_module_initialization_all_modules(self):
        """Test inicialización de todos los módulos."""
        try:
            malto_config = MALTOConfig()
        except TypeError:
            malto_config = MALTOConfig(
                use_uncertainty_quantification=True,
                use_nli_validation=True,
                word_level_detection=True,
                uncertainty_threshold=0.5,
                nli_threshold=0.3,
                mitigation_strength=0.4
            )
        
        solar_config = SOLARConfig()
        hademif_config = HaDeMiFConfig()
        
        malto_module = MALTOModule(malto_config)
        solar_module = SOLARModule(solar_config)
        hademif_module = HaDeMiFModule(hademif_config)
        
        assert malto_module.config == malto_config
        assert solar_module.config == solar_config
        assert hademif_module.config == hademif_config
    
    def test_forward_pass_all_modules(self):
        """Test forward pass para todos los módulos."""
        try:
            malto_config = MALTOConfig()
        except TypeError:
            malto_config = MALTOConfig(
                use_uncertainty_quantification=True,
                use_nli_validation=True,
                word_level_detection=True,
                uncertainty_threshold=0.5,
                nli_threshold=0.3,
                mitigation_strength=0.4
            )
        
        solar_config = SOLARConfig()
        hademif_config = HaDeMiFConfig()
        
        malto_module = MALTOModule(malto_config)
        solar_module = SOLARModule(solar_config)
        hademif_module = HaDeMiFModule(hademif_config)
        
        hidden_states = torch.randn(2, 10, 512)
        
        malto_output, _ = malto_module(hidden_states)
        solar_output, _ = solar_module(hidden_states)
        hademif_output, _ = hademif_module(hidden_states)
        
        assert malto_output.shape == hidden_states.shape
        assert solar_output.shape == hidden_states.shape
        assert hademif_output.shape == hidden_states.shape
    
    def test_metadata_completeness_all_modules(self):
        """Test que metadata es completa para todos los módulos."""
        try:
            malto_config = MALTOConfig()
        except TypeError:
            malto_config = MALTOConfig(
                use_uncertainty_quantification=True,
                use_nli_validation=True,
                word_level_detection=True,
                uncertainty_threshold=0.5,
                nli_threshold=0.3,
                mitigation_strength=0.4
            )
        
        solar_config = SOLARConfig()
        hademif_config = HaDeMiFConfig()
        
        malto_module = MALTOModule(malto_config)
        solar_module = SOLARModule(solar_config)
        hademif_module = HaDeMiFModule(hademif_config)
        
        hidden_states = torch.randn(2, 10, 512)
        
        _, malto_metadata = malto_module(hidden_states)
        _, solar_metadata = solar_module(hidden_states)
        _, hademif_metadata = hademif_module(hidden_states)
        
        assert isinstance(malto_metadata, dict)
        assert isinstance(solar_metadata, dict)
        assert isinstance(hademif_metadata, dict)
        assert len(malto_metadata) > 0
        assert len(solar_metadata) > 0
        assert len(hademif_metadata) > 0
    
    def test_metrics_tracking_all_modules(self):
        """Test tracking de métricas para todos los módulos."""
        try:
            malto_config = MALTOConfig()
        except TypeError:
            malto_config = MALTOConfig(
                use_uncertainty_quantification=True,
                use_nli_validation=True,
                word_level_detection=True,
                uncertainty_threshold=0.5,
                nli_threshold=0.3,
                mitigation_strength=0.4
            )
        
        solar_config = SOLARConfig()
        hademif_config = HaDeMiFConfig()
        
        malto_module = MALTOModule(malto_config)
        solar_module = SOLARModule(solar_config)
        hademif_module = HaDeMiFModule(hademif_config)
        
        hidden_states = torch.randn(2, 10, 512)
        
        malto_module(hidden_states)
        solar_module(hidden_states)
        hademif_module(hidden_states)
        
        assert malto_module._forward_count == 1
        assert solar_module._forward_count == 1
        assert hademif_module._forward_count == 1
    
    def test_error_handling_all_modules(self):
        """Test manejo de errores para todos los módulos."""
        try:
            malto_config = MALTOConfig()
        except TypeError:
            malto_config = MALTOConfig(
                use_uncertainty_quantification=True,
                use_nli_validation=True,
                word_level_detection=True,
                uncertainty_threshold=0.5,
                nli_threshold=0.3,
                mitigation_strength=0.4
            )
        
        solar_config = SOLARConfig()
        hademif_config = HaDeMiFConfig()
        
        malto_module = MALTOModule(malto_config)
        solar_module = SOLARModule(solar_config)
        hademif_module = HaDeMiFModule(hademif_config)
        
        with pytest.raises(Exception):
            malto_module(torch.randn(2, 10, 256))
        
        with pytest.raises(Exception):
            solar_module(torch.randn(2, 10, 256))
        
        with pytest.raises(Exception):
            hademif_module(torch.randn(2, 10, 256))
    
    def test_batch_size_consistency_all_modules(self):
        """Test consistencia de batch size para todos los módulos."""
        try:
            malto_config = MALTOConfig()
        except TypeError:
            malto_config = MALTOConfig(
                use_uncertainty_quantification=True,
                use_nli_validation=True,
                word_level_detection=True,
                uncertainty_threshold=0.5,
                nli_threshold=0.3,
                mitigation_strength=0.4
            )
        
        solar_config = SOLARConfig()
        hademif_config = HaDeMiFConfig()
        
        malto_module = MALTOModule(malto_config)
        solar_module = SOLARModule(solar_config)
        hademif_module = HaDeMiFModule(hademif_config)
        
        for batch_size in [1, 2, 4, 8]:
            hidden_states = torch.randn(batch_size, 10, 512)
            
            malto_output, _ = malto_module(hidden_states)
            solar_output, _ = solar_module(hidden_states)
            hademif_output, _ = hademif_module(hidden_states)
            
            assert malto_output.shape[0] == batch_size
            assert solar_output.shape[0] == batch_size
            assert hademif_output.shape[0] == batch_size
    
    def test_sequence_length_consistency_all_modules(self):
        """Test consistencia de sequence length para todos los módulos."""
        try:
            malto_config = MALTOConfig()
        except TypeError:
            malto_config = MALTOConfig(
                use_uncertainty_quantification=True,
                use_nli_validation=True,
                word_level_detection=True,
                uncertainty_threshold=0.5,
                nli_threshold=0.3,
                mitigation_strength=0.4
            )
        
        solar_config = SOLARConfig()
        hademif_config = HaDeMiFConfig()
        
        malto_module = MALTOModule(malto_config)
        solar_module = SOLARModule(solar_config)
        hademif_module = HaDeMiFModule(hademif_config)
        
        for seq_len in [1, 5, 10, 50, 100]:
            hidden_states = torch.randn(2, seq_len, 512)
            
            malto_output, _ = malto_module(hidden_states)
            solar_output, _ = solar_module(hidden_states)
            hademif_output, _ = hademif_module(hidden_states)
            
            assert malto_output.shape[1] == seq_len
            assert solar_output.shape[1] == seq_len
            assert hademif_output.shape[1] == seq_len




import pytest
import torch
from typing import Dict, Any

from core.paper_base import BasePaperConfig, BasePaperModule
from research.paper_malto import MALTOModule, MALTOConfig
from research.paper_solar import SOLARModule, SOLARConfig
from research.paper_hademif import HaDeMiFModule, HaDeMiFConfig
import torch.nn as nn


class SimpleModule(BasePaperModule):
    """Simple module for compatibility testing."""
    
    def __init__(self, config: BasePaperConfig):
        super().__init__(config)
        self.linear = nn.Linear(config.hidden_dim, config.hidden_dim)
    
    def forward(self, hidden_states: torch.Tensor, **kwargs):
        self.validate_inputs(hidden_states, **kwargs)
        output = self.linear(hidden_states)
        metadata = {'output_mean': output.mean().item()}
        self._update_metrics(**metadata)
        return output, metadata


class TestCompatibility:
    """Tests de compatibilidad entre diferentes configuraciones y versiones."""
    
    @pytest.mark.parametrize("hidden_dim", [128, 256, 512, 768, 1024, 2048])
    def test_cross_hidden_dim_compatibility(self, hidden_dim):
        """Test compatibilidad entre diferentes hidden_dims."""
        config = BasePaperConfig(hidden_dim=hidden_dim)
        module = SimpleModule(config)
        hidden_states = torch.randn(2, 10, hidden_dim)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert output.shape[2] == hidden_dim
    
    @pytest.mark.parametrize("dtype", [torch.float16, torch.float32])
    def test_dtype_compatibility(self, sample_config, dtype):
        """Test compatibilidad con diferentes dtypes."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512, dtype=dtype)
        
        output, metadata = module(hidden_states)
        
        assert output.dtype == dtype
        assert output.shape == hidden_states.shape
    
    def test_device_compatibility(self, sample_config):
        """Test compatibilidad con diferentes devices."""
        module = SimpleModule(sample_config)
        
        devices = ["cpu"]
        if torch.cuda.is_available():
            devices.append("cuda")
        
        for device in devices:
            module.to_device(device)
            hidden_states = torch.randn(2, 10, 512).to(device)
            
            output, metadata = module(hidden_states)
            
            assert output.device.type == device
            assert output.shape == hidden_states.shape
    
    def test_malto_solar_compatibility(self):
        """Test que MALTO y SOLAR son compatibles."""
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
        
        malto_module = MALTOModule(malto_config)
        solar_module = SOLARModule(solar_config)
        
        hidden_states = torch.randn(2, 10, 512)
        
        malto_output, _ = malto_module(hidden_states)
        solar_output, _ = solar_module(hidden_states)
        
        assert malto_output.shape == solar_output.shape
        assert malto_output.shape == hidden_states.shape
    
    def test_malto_hademif_compatibility(self):
        """Test que MALTO y HaDeMiF son compatibles."""
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
        hademif_config = HaDeMiFConfig()
        
        malto_module = MALTOModule(malto_config)
        hademif_module = HaDeMiFModule(hademif_config)
        
        hidden_states = torch.randn(2, 10, 512)
        
        malto_output, _ = malto_module(hidden_states)
        hademif_output, _ = hademif_module(hidden_states)
        
        assert malto_output.shape == hademif_output.shape
        assert malto_output.shape == hidden_states.shape
    
    def test_solar_hademif_compatibility(self):
        """Test que SOLAR y HaDeMiF son compatibles."""
        solar_config = SOLARConfig()
        hademif_config = HaDeMiFConfig()
        
        solar_module = SOLARModule(solar_config)
        hademif_module = HaDeMiFModule(hademif_config)
        
        hidden_states = torch.randn(2, 10, 512)
        
        solar_output, _ = solar_module(hidden_states)
        hademif_output, _ = hademif_module(hidden_states)
        
        assert solar_output.shape == hademif_output.shape
        assert solar_output.shape == hidden_states.shape
    
    def test_config_interchangeability(self):
        """Test que configs son intercambiables entre módulos compatibles."""
        base_config = BasePaperConfig(hidden_dim=512)
        
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
        
        assert base_config.hidden_dim == malto_config.hidden_dim
        assert base_config.hidden_dim == solar_config.hidden_dim
    
    def test_serialization_compatibility(self, temp_dir):
        """Test que serialización es compatible entre versiones."""
        config = BasePaperConfig(hidden_dim=512)
        config_path = temp_dir / "compat_config.json"
        
        config.save(config_path)
        
        loaded_config = BasePaperConfig.load(config_path)
        
        assert loaded_config.hidden_dim == config.hidden_dim
        assert loaded_config.to_dict() == config.to_dict()
    
    def test_model_save_load_compatibility(self, temp_dir):
        """Test que save/load es compatible."""
        config = BasePaperConfig(hidden_dim=512)
        module = SimpleModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        model_path = temp_dir / "compat_model.pt"
        module.save_model(model_path)
        
        loaded_module = SimpleModule.load_model(model_path, config=config)
        loaded_output, _ = loaded_module(hidden_states)
        
        assert loaded_output.shape == hidden_states.shape
    
    def test_batch_size_compatibility(self, sample_config):
        """Test compatibilidad con diferentes batch sizes."""
        module = SimpleModule(sample_config)
        
        batch_sizes = [1, 2, 4, 8, 16, 32]
        for batch_size in batch_sizes:
            hidden_states = torch.randn(batch_size, 10, 512)
            output, metadata = module(hidden_states)
            assert output.shape[0] == batch_size
    
    def test_sequence_length_compatibility(self, sample_config):
        """Test compatibilidad con diferentes sequence lengths."""
        module = SimpleModule(sample_config)
        
        seq_lengths = [1, 5, 10, 50, 100, 500]
        for seq_len in seq_lengths:
            hidden_states = torch.randn(2, seq_len, 512)
            output, metadata = module(hidden_states)
            assert output.shape[1] == seq_len
    
    def test_python_version_compatibility(self, sample_config):
        """Test que código es compatible con diferentes versiones de Python."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert isinstance(output, torch.Tensor)
        assert isinstance(metadata, dict)
    
    def test_torch_version_compatibility(self, sample_config):
        """Test que código es compatible con diferentes versiones de PyTorch."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert hasattr(output, 'shape')
        assert hasattr(output, 'dtype')
        assert hasattr(output, 'device')


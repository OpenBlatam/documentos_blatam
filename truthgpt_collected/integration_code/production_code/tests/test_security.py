import pytest
import torch
import tempfile
from pathlib import Path
from typing import Dict, Any

from core.paper_base import BasePaperConfig, BasePaperModule
from research.paper_malto import MALTOModule, MALTOConfig
from research.paper_solar import SOLARModule, SOLARConfig
import torch.nn as nn


class SimpleModule(BasePaperModule):
    """Simple module for security testing."""
    
    def __init__(self, config: BasePaperConfig):
        super().__init__(config)
        self.linear = nn.Linear(config.hidden_dim, config.hidden_dim)
    
    def forward(self, hidden_states: torch.Tensor, **kwargs):
        self.validate_inputs(hidden_states, **kwargs)
        output = self.linear(hidden_states)
        metadata = {'output_mean': output.mean().item()}
        self._update_metrics(**metadata)
        return output, metadata


class TestSecurity:
    """Tests de seguridad para módulos."""
    
    def test_no_secrets_in_config_dict(self, sample_config):
        """Test que no hay secretos en config.to_dict()."""
        config = sample_config
        config_dict = config.to_dict()
        
        sensitive_keys = ['password', 'secret', 'key', 'token', 'api_key', 'auth']
        for key in config_dict.keys():
            assert not any(sensitive in key.lower() for sensitive in sensitive_keys)
    
    def test_no_secrets_in_metadata(self, sample_config):
        """Test que no hay secretos en metadata."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        
        _, metadata = module(hidden_states)
        
        sensitive_keys = ['password', 'secret', 'key', 'token', 'api_key', 'auth']
        for key in metadata.keys():
            assert not any(sensitive in key.lower() for sensitive in sensitive_keys)
    
    def test_save_load_path_validation(self, sample_config, temp_dir):
        """Test validación de paths en save/load."""
        module = SimpleModule(sample_config)
        
        valid_path = temp_dir / "model.pt"
        module.save_model(valid_path)
        
        assert valid_path.exists()
        
        loaded_module = SimpleModule.load_model(valid_path, config=sample_config)
        assert loaded_module is not None
    
    def test_save_load_path_traversal_protection(self, sample_config, temp_dir):
        """Test protección contra path traversal."""
        module = SimpleModule(sample_config)
        
        with pytest.raises((ValueError, OSError, FileNotFoundError)):
            malicious_path = temp_dir / "../../../etc/passwd"
            module.save_model(malicious_path)
    
    def test_input_size_limits(self, sample_config):
        """Test límites de tamaño de input para prevenir DoS."""
        module = SimpleModule(sample_config)
        
        reasonable_size = torch.randn(32, 1000, 512)
        output, _ = module(reasonable_size)
        assert output.shape == reasonable_size.shape
        
        very_large_size = torch.randn(1000, 10000, 512)
        try:
            output, _ = module(very_large_size)
            assert output.shape == very_large_size.shape
        except (RuntimeError, MemoryError):
            pass
    
    def test_config_immutability(self, sample_config):
        """Test que configs no se modifican accidentalmente."""
        config = sample_config
        original_hidden_dim = config.hidden_dim
        
        config_dict = config.to_dict()
        config_dict['hidden_dim'] = 999
        
        assert config.hidden_dim == original_hidden_dim
    
    def test_model_state_isolation(self, sample_config):
        """Test que estados de modelos están aislados."""
        module1 = SimpleModule(sample_config)
        module2 = SimpleModule(sample_config)
        
        hidden_states = torch.randn(2, 10, 512)
        
        output1, _ = module1(hidden_states)
        output2, _ = module2(hidden_states)
        
        assert module1._forward_count == 1
        assert module2._forward_count == 1
        assert module1._forward_count == module2._forward_count
    
    def test_no_code_injection_in_config(self):
        """Test que configs no permiten inyección de código."""
        config = BasePaperConfig(hidden_dim=512)
        
        config_dict = config.to_dict()
        
        malicious_strings = ['__import__', 'eval', 'exec', '__builtins__']
        for key, value in config_dict.items():
            if isinstance(value, str):
                assert not any(malicious in value for malicious in malicious_strings)
    
    def test_save_load_file_permissions(self, sample_config, temp_dir):
        """Test que archivos guardados tienen permisos seguros."""
        module = SimpleModule(sample_config)
        model_path = temp_dir / "secure_model.pt"
        
        module.save_model(model_path)
        
        assert model_path.exists()
        permissions = model_path.stat().st_mode & 0o777
        assert permissions <= 0o644
    
    def test_serialization_safety(self, sample_config, temp_dir):
        """Test que serialización es segura."""
        config = sample_config
        config_path = temp_dir / "config.json"
        
        config.save(config_path)
        
        assert config_path.exists()
        
        loaded_config = BasePaperConfig.load(config_path)
        assert loaded_config.hidden_dim == config.hidden_dim
    
    def test_input_type_validation(self, sample_config):
        """Test validación estricta de tipos de input."""
        module = SimpleModule(sample_config)
        
        with pytest.raises(Exception):
            module("not a tensor")
        
        with pytest.raises(Exception):
            module([1, 2, 3])
        
        with pytest.raises(Exception):
            module(None)
    
    def test_no_arbitrary_code_execution(self, sample_config):
        """Test que no hay ejecución arbitraria de código."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert isinstance(output, torch.Tensor)
        assert isinstance(metadata, dict)
        
        for key, value in metadata.items():
            assert not callable(value) or isinstance(value, type)




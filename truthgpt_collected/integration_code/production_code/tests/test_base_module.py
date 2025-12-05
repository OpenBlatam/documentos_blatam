import pytest
import torch
import torch.nn as nn
from pathlib import Path
from typing import Dict, Any, Tuple

from core.paper_base import (
    BasePaperModule,
    BasePaperConfig,
    ConfigurationError,
    ValidationError,
    ModelError
)


class ConcretePaperModule(BasePaperModule):
    """Concrete implementation for testing BasePaperModule."""
    
    def __init__(self, config: BasePaperConfig):
        super().__init__(config)
        self.linear = nn.Linear(config.hidden_dim, config.hidden_dim)
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """Simple forward pass for testing."""
        self.validate_inputs(hidden_states, **kwargs)
        output = self.linear(hidden_states)
        metadata = {
            'output_mean': output.mean().item(),
            'output_std': output.std().item(),
            'input_shape': list(hidden_states.shape)
        }
        self._update_metrics(output_mean=metadata['output_mean'])
        return output, metadata


class TestBasePaperModule:
    """Comprehensive tests for BasePaperModule."""
    
    def test_initialization_with_valid_config(self, sample_config):
        """Test initialization with valid config."""
        module = ConcretePaperModule(sample_config)
        assert module.config == sample_config
        assert module._forward_count == 0
        assert isinstance(module._metrics, dict)
        assert len(module._metrics) == 0
    
    def test_initialization_with_invalid_config(self):
        """Test initialization fails with invalid config."""
        with pytest.raises(ConfigurationError, match="config debe ser instancia de BasePaperConfig"):
            ConcretePaperModule(None)
        
        with pytest.raises(ConfigurationError):
            ConcretePaperModule("not a config")
        
        with pytest.raises(ConfigurationError):
            ConcretePaperModule({"hidden_dim": 512})
    
    def test_forward_pass_basic(self, sample_config, sample_hidden_states):
        """Test basic forward pass."""
        module = ConcretePaperModule(sample_config)
        output, metadata = module(sample_hidden_states)
        
        assert output.shape == sample_hidden_states.shape
        assert isinstance(metadata, dict)
        assert 'output_mean' in metadata
        assert 'output_std' in metadata
        assert module._forward_count == 1
    
    def test_validate_inputs_valid(self, sample_config, sample_hidden_states):
        """Test input validation with valid inputs."""
        module = ConcretePaperModule(sample_config)
        module.validate_inputs(sample_hidden_states)
    
    def test_validate_inputs_wrong_type(self, sample_config):
        """Test input validation fails with wrong type."""
        module = ConcretePaperModule(sample_config)
        
        with pytest.raises(TypeError, match="hidden_states debe ser torch.Tensor"):
            module.validate_inputs("not a tensor")
        
        with pytest.raises(TypeError):
            module.validate_inputs([1, 2, 3])
    
    def test_validate_inputs_wrong_dimensions(self, sample_config):
        """Test input validation fails with wrong dimensions."""
        module = ConcretePaperModule(sample_config)
        
        with pytest.raises(ValidationError, match="debe tener 3 dimensiones"):
            module.validate_inputs(torch.randn(2, 10))
        
        with pytest.raises(ValidationError):
            module.validate_inputs(torch.randn(2))
        
        with pytest.raises(ValidationError):
            module.validate_inputs(torch.randn(2, 10, 512, 4))
    
    def test_validate_inputs_zero_batch_size(self, sample_config):
        """Test input validation fails with zero batch size."""
        module = ConcretePaperModule(sample_config)
        
        with pytest.raises(ValidationError, match="batch_size debe ser > 0"):
            module.validate_inputs(torch.randn(0, 10, 512))
    
    def test_validate_inputs_zero_seq_len(self, sample_config):
        """Test input validation fails with zero sequence length."""
        module = ConcretePaperModule(sample_config)
        
        with pytest.raises(ValidationError, match="seq_len debe ser > 0"):
            module.validate_inputs(torch.randn(2, 0, 512))
    
    def test_validate_inputs_wrong_hidden_dim(self, sample_config):
        """Test input validation fails with wrong hidden_dim."""
        module = ConcretePaperModule(sample_config)
        
        with pytest.raises(ValidationError, match="no coincide con config.hidden_dim"):
            module.validate_inputs(torch.randn(2, 10, 256))
    
    def test_validate_inputs_contains_nan(self, sample_config):
        """Test input validation fails with NaN values."""
        module = ConcretePaperModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        hidden_states[0, 0, 0] = float('nan')
        
        with pytest.raises(ValidationError, match="contiene NaN"):
            module.validate_inputs(hidden_states)
    
    def test_validate_inputs_contains_inf(self, sample_config):
        """Test input validation fails with Inf values."""
        module = ConcretePaperModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        hidden_states[0, 0, 0] = float('inf')
        
        with pytest.raises(ValidationError, match="contiene Inf"):
            module.validate_inputs(hidden_states)
    
    def test_get_model_info(self, sample_config):
        """Test getting model information."""
        module = ConcretePaperModule(sample_config)
        info = module.get_model_info()
        
        assert isinstance(info, dict)
        assert 'model_name' in info
        assert 'config' in info
        assert 'total_parameters' in info
        assert 'trainable_parameters' in info
        assert 'non_trainable_parameters' in info
        assert 'forward_count' in info
        assert info['model_name'] == 'ConcretePaperModule'
        assert info['forward_count'] == 0
    
    def test_count_parameters(self, sample_config):
        """Test parameter counting."""
        module = ConcretePaperModule(sample_config)
        
        total = module.count_parameters()
        trainable = module.count_parameters(trainable_only=True)
        
        assert total > 0
        assert trainable > 0
        assert trainable <= total
    
    def test_save_and_load_model(self, sample_config, sample_hidden_states, temp_dir):
        """Test saving and loading model."""
        module = ConcretePaperModule(sample_config)
        module(sample_hidden_states)
        
        model_path = temp_dir / "test_model.pt"
        module.save_model(model_path)
        assert model_path.exists()
        
        loaded_module = ConcretePaperModule.load_model(model_path, config=sample_config)
        assert isinstance(loaded_module, ConcretePaperModule)
        assert loaded_module.config.hidden_dim == sample_config.hidden_dim
    
    def test_save_model_with_config(self, sample_config, temp_dir):
        """Test saving model with config file."""
        module = ConcretePaperModule(sample_config)
        model_path = temp_dir / "test_model.pt"
        
        module.save_model(model_path, include_config=True)
        assert model_path.exists()
        
        config_path = temp_dir / "test_model_config.json"
        assert config_path.exists()
    
    def test_save_model_without_config(self, sample_config, temp_dir):
        """Test saving model without config file."""
        module = ConcretePaperModule(sample_config)
        model_path = temp_dir / "test_model.pt"
        
        module.save_model(model_path, include_config=False)
        assert model_path.exists()
        
        config_path = temp_dir / "test_model_config.json"
        assert not config_path.exists()
    
    def test_load_model_nonexistent(self, temp_dir, sample_config):
        """Test loading non-existent model raises error."""
        model_path = temp_dir / "nonexistent.pt"
        
        with pytest.raises(FileNotFoundError):
            ConcretePaperModule.load_model(model_path, config=sample_config)
    
    def test_load_model_without_config_file(self, sample_config, temp_dir):
        """Test loading model without config file raises error."""
        module = ConcretePaperModule(sample_config)
        model_path = temp_dir / "test_model.pt"
        
        module.save_model(model_path, include_config=False)
        
        with pytest.raises(ConfigurationError):
            ConcretePaperModule.load_model(model_path, config=None)
    
    def test_get_metrics(self, sample_config, sample_hidden_states):
        """Test getting metrics."""
        module = ConcretePaperModule(sample_config)
        module(sample_hidden_states)
        
        metrics = module.get_metrics()
        assert isinstance(metrics, dict)
        assert 'forward_count' in metrics
        assert 'model_info' in metrics
        assert metrics['forward_count'] == 1
    
    def test_reset_metrics(self, sample_config, sample_hidden_states):
        """Test resetting metrics."""
        module = ConcretePaperModule(sample_config)
        module(sample_hidden_states)
        module(sample_hidden_states)
        
        assert module._forward_count == 2
        assert len(module._metrics) > 0
        
        module.reset_metrics()
        
        assert module._forward_count == 0
        assert len(module._metrics) == 0
    
    def test_update_metrics(self, sample_config):
        """Test updating metrics."""
        module = ConcretePaperModule(sample_config)
        
        module._update_metrics(test_metric=1.0, another_metric=2.0)
        
        assert module._metrics['test_metric'] == 1.0
        assert module._metrics['another_metric'] == 2.0
        assert module._forward_count == 1
    
    def test_to_device(self, sample_config, device):
        """Test moving model to device."""
        module = ConcretePaperModule(sample_config)
        module.to_device(device)
        
        assert module._device is not None
        assert str(module._device) == device
    
    def test_set_dtype(self, sample_config):
        """Test setting dtype."""
        module = ConcretePaperModule(sample_config)
        module.set_dtype(torch.float16)
        
        assert module._dtype == torch.float16
    
    def test_forward_count_tracking(self, sample_config, sample_hidden_states):
        """Test forward count tracking."""
        module = ConcretePaperModule(sample_config)
        
        assert module._forward_count == 0
        
        module(sample_hidden_states)
        assert module._forward_count == 1
        
        module(sample_hidden_states)
        assert module._forward_count == 2
        
        module(sample_hidden_states)
        assert module._forward_count == 3
    
    def test_repr(self, sample_config):
        """Test string representation."""
        module = ConcretePaperModule(sample_config)
        repr_str = repr(module)
        
        assert 'ConcretePaperModule' in repr_str
        assert 'config=' in repr_str
        assert 'parameters=' in repr_str
        assert 'forward_count=' in repr_str
    
    def test_forward_with_kwargs(self, sample_config, sample_hidden_states):
        """Test forward pass with additional kwargs."""
        module = ConcretePaperModule(sample_config)
        output, metadata = module(sample_hidden_states, extra_param=123)
        
        assert output.shape == sample_hidden_states.shape
        assert isinstance(metadata, dict)
    
    def test_different_batch_sizes(self, sample_config):
        """Test with different batch sizes."""
        module = ConcretePaperModule(sample_config)
        
        for batch_size in [1, 2, 4, 8]:
            hidden_states = torch.randn(batch_size, 10, 512)
            output, _ = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_different_seq_lengths(self, sample_config):
        """Test with different sequence lengths."""
        module = ConcretePaperModule(sample_config)
        
        for seq_len in [1, 5, 10, 50, 100]:
            hidden_states = torch.randn(2, seq_len, 512)
            output, _ = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_model_state_consistency(self, sample_config, sample_hidden_states, temp_dir):
        """Test that model state is consistent after save/load."""
        module = ConcretePaperModule(sample_config)
        original_output, _ = module(sample_hidden_states)
        
        model_path = temp_dir / "test_model.pt"
        module.save_model(model_path)
        
        loaded_module = ConcretePaperModule.load_model(model_path, config=sample_config)
        loaded_output, _ = loaded_module(sample_hidden_states)
        
        torch.testing.assert_close(original_output, loaded_output)




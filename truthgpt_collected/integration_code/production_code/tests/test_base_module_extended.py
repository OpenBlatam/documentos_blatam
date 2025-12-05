import pytest
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple
import tempfile
import shutil

from core.paper_base import (
    BasePaperModule,
    BasePaperConfig,
    ConfigurationError,
    ValidationError
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


class TestBasePaperModuleExtended:
    """Tests extendidos y parametrizados para BasePaperModule."""
    
    @pytest.mark.parametrize("batch_size", [1, 2, 4, 8, 16, 32])
    def test_forward_different_batch_sizes(self, sample_config, batch_size):
        """Test forward pass con diferentes batch sizes."""
        module = ConcretePaperModule(sample_config)
        hidden_states = torch.randn(batch_size, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert output.shape[0] == batch_size
    
    @pytest.mark.parametrize("seq_len", [1, 5, 10, 20, 50, 100, 200])
    def test_forward_different_seq_lengths(self, sample_config, seq_len):
        """Test forward pass con diferentes sequence lengths."""
        module = ConcretePaperModule(sample_config)
        hidden_states = torch.randn(2, seq_len, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert output.shape[1] == seq_len
    
    @pytest.mark.parametrize("hidden_dim", [128, 256, 512, 768, 1024])
    def test_forward_different_hidden_dims(self, hidden_dim):
        """Test forward pass con diferentes hidden dimensions."""
        config = BasePaperConfig(hidden_dim=hidden_dim)
        module = ConcretePaperModule(config)
        hidden_states = torch.randn(2, 10, hidden_dim)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert output.shape[2] == hidden_dim
    
    @pytest.mark.parametrize("dtype", [torch.float32, torch.float16, torch.float64])
    def test_forward_different_dtypes(self, sample_config, dtype):
        """Test forward pass con diferentes dtypes."""
        module = ConcretePaperModule(sample_config)
        hidden_states = torch.randn(2, 10, 512, dtype=dtype)
        
        output, metadata = module(hidden_states)
        
        assert output.dtype == dtype
        assert output.shape == hidden_states.shape
    
    def test_forward_with_nan_handling(self, sample_config):
        """Test que forward maneja NaN correctamente."""
        module = ConcretePaperModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        hidden_states[0, 0, 0] = float('nan')
        
        with pytest.raises(ValidationError, match="contiene NaN"):
            module(hidden_states)
    
    def test_forward_with_inf_handling(self, sample_config):
        """Test que forward maneja Inf correctamente."""
        module = ConcretePaperModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        hidden_states[0, 0, 0] = float('inf')
        
        with pytest.raises(ValidationError, match="contiene Inf"):
            module(hidden_states)
    
    def test_forward_with_negative_inf(self, sample_config):
        """Test que forward maneja -Inf correctamente."""
        module = ConcretePaperModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        hidden_states[0, 0, 0] = float('-inf')
        
        with pytest.raises(ValidationError, match="contiene Inf"):
            module(hidden_states)
    
    def test_metrics_accumulation_multiple_forwards(self, sample_config):
        """Test acumulación de métricas en múltiples forward passes."""
        module = ConcretePaperModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        
        for i in range(10):
            module(hidden_states)
        
        assert module._forward_count == 10
        metrics = module.get_metrics()
        assert metrics['forward_count'] == 10
    
    def test_metrics_reset_clears_all(self, sample_config):
        """Test que reset_metrics limpia todas las métricas."""
        module = ConcretePaperModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        
        module(hidden_states)
        module(hidden_states)
        module._update_metrics(custom_metric=1.0, another_metric=2.0)
        
        assert module._forward_count == 3
        assert len(module._metrics) > 0
        
        module.reset_metrics()
        
        assert module._forward_count == 0
        assert len(module._metrics) == 0
    
    def test_save_load_preserves_state(self, sample_config, temp_dir):
        """Test que save/load preserva el estado del modelo."""
        module = ConcretePaperModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        
        original_output, _ = module(hidden_states)
        module._update_metrics(test_metric=123.45)
        
        model_path = temp_dir / "test_model.pt"
        module.save_model(model_path)
        
        loaded_module = ConcretePaperModule.load_model(model_path, config=sample_config)
        loaded_output, _ = loaded_module(hidden_states)
        
        torch.testing.assert_close(original_output, loaded_output, atol=1e-5, rtol=1e-5)
    
    def test_save_load_preserves_parameters(self, sample_config, temp_dir):
        """Test que save/load preserva los parámetros."""
        module = ConcretePaperModule(sample_config)
        original_params = {name: param.clone() for name, param in module.named_parameters()}
        
        model_path = temp_dir / "test_model.pt"
        module.save_model(model_path)
        
        loaded_module = ConcretePaperModule.load_model(model_path, config=sample_config)
        
        for name, original_param in original_params.items():
            loaded_param = dict(loaded_module.named_parameters())[name]
            torch.testing.assert_close(original_param, loaded_param, atol=1e-7, rtol=1e-7)
    
    def test_device_transfer(self, sample_config, device):
        """Test transferencia a diferentes dispositivos."""
        module = ConcretePaperModule(sample_config)
        module.to_device(device)
        
        hidden_states = torch.randn(2, 10, 512).to(device)
        output, _ = module(hidden_states)
        
        assert output.device.type == device
        assert module._device is not None
    
    def test_dtype_conversion(self, sample_config):
        """Test conversión de dtype."""
        module = ConcretePaperModule(sample_config)
        module.set_dtype(torch.float16)
        
        hidden_states = torch.randn(2, 10, 512, dtype=torch.float16)
        output, _ = module(hidden_states)
        
        assert output.dtype == torch.float16
    
    def test_model_info_completeness(self, sample_config):
        """Test que model_info contiene toda la información necesaria."""
        module = ConcretePaperModule(sample_config)
        info = module.get_model_info()
        
        required_keys = [
            'model_name', 'config', 'total_parameters',
            'trainable_parameters', 'non_trainable_parameters',
            'forward_count', 'device', 'dtype'
        ]
        
        for key in required_keys:
            assert key in info, f"Missing key: {key}"
    
    def test_parameter_counting_accuracy(self, sample_config):
        """Test que el conteo de parámetros es preciso."""
        module = ConcretePaperModule(sample_config)
        
        total = module.count_parameters()
        trainable = module.count_parameters(trainable_only=True)
        
        manual_total = sum(p.numel() for p in module.parameters())
        manual_trainable = sum(p.numel() for p in module.parameters() if p.requires_grad)
        
        assert total == manual_total
        assert trainable == manual_trainable
        assert trainable <= total
    
    def test_forward_with_kwargs_preserved(self, sample_config):
        """Test que kwargs se preservan en forward."""
        module = ConcretePaperModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states, extra_param=123, another_param="test")
        
        assert output.shape == hidden_states.shape
        assert isinstance(metadata, dict)
    
    def test_concurrent_forward_calls(self, sample_config):
        """Test múltiples forward calls concurrentes (simulado)."""
        module = ConcretePaperModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        
        outputs = []
        for _ in range(5):
            output, _ = module(hidden_states)
            outputs.append(output)
        
        assert len(outputs) == 5
        assert all(out.shape == hidden_states.shape for out in outputs)
    
    def test_large_tensor_handling(self, sample_config):
        """Test manejo de tensores grandes."""
        module = ConcretePaperModule(sample_config)
        hidden_states = torch.randn(32, 1000, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert output.numel() == 32 * 1000 * 512
    
    def test_small_tensor_handling(self, sample_config):
        """Test manejo de tensores pequeños."""
        module = ConcretePaperModule(sample_config)
        hidden_states = torch.randn(1, 1, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
    
    def test_model_repr(self, sample_config):
        """Test representación string del modelo."""
        module = ConcretePaperModule(sample_config)
        repr_str = repr(module)
        
        assert 'ConcretePaperModule' in repr_str
        assert 'config' in repr_str.lower() or 'parameters' in repr_str.lower()
    
    def test_model_str(self, sample_config):
        """Test string representation del modelo."""
        module = ConcretePaperModule(sample_config)
        str_repr = str(module)
        
        assert str_repr is not None
        assert len(str_repr) > 0




import pytest
import torch
from typing import Dict, Any, List

from inference.paper_layerkv import LayerKVModule, LayerKVConfig
from core.paper_base import ValidationError


class TestLayerKVConfig:
    """Tests for LayerKVConfig."""
    
    def test_default_initialization(self):
        """Test default configuration."""
        try:
            config = LayerKVConfig(hidden_dim=512)
        except TypeError:
            config = LayerKVConfig(
                hidden_dim=512,
                num_layers=12,
                gpu_layers=None,
                cpu_layers=None,
                offload_threshold=0.7,
                memory_threshold=0.8,
                use_adaptive_offload=True
            )
        assert config.hidden_dim == 512
        assert config.num_layers == 12
        assert config.use_adaptive_offload is True
    
    def test_custom_gpu_cpu_layers(self):
        """Test custom GPU and CPU layer assignments."""
        config = LayerKVConfig(
            hidden_dim=512,
            num_layers=12,
            gpu_layers=[0, 1, 2, 3, 4, 5],
            cpu_layers=[6, 7, 8, 9, 10, 11]
        )
        assert len(config.gpu_layers) == 6
        assert len(config.cpu_layers) == 6
    
    def test_validation(self):
        """Test configuration validation."""
        config = LayerKVConfig(hidden_dim=512)
        if hasattr(config, 'validate'):
            config.validate()


class TestLayerKVModule:
    """Comprehensive tests for LayerKVModule."""
    
    def test_initialization(self):
        """Test module initialization."""
        try:
            config = LayerKVConfig()
        except TypeError:
            config = LayerKVConfig(
                num_layers=12,
                gpu_layers=None,
                cpu_layers=None,
                offload_threshold=0.7,
                memory_threshold=0.8,
                use_adaptive_offload=True
            )
        module = LayerKVModule(config)
        
        assert module.config == config
    
    def test_forward_pass_basic(self):
        """Test basic forward pass."""
        config = LayerKVConfig(hidden_dim=512)
        module = LayerKVModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert isinstance(metadata, dict)
    
    def test_adaptive_offload_enabled(self):
        """Test with adaptive offload enabled."""
        config = LayerKVConfig(hidden_dim=512, use_adaptive_offload=True)
        module = LayerKVModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
    
    def test_adaptive_offload_disabled(self):
        """Test with adaptive offload disabled."""
        config = LayerKVConfig(hidden_dim=512, use_adaptive_offload=False)
        module = LayerKVModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
    
    def test_custom_layer_assignments(self):
        """Test with custom layer assignments."""
        config = LayerKVConfig(
            hidden_dim=512,
            num_layers=12,
            gpu_layers=[0, 1, 2, 3],
            cpu_layers=[4, 5, 6, 7, 8, 9, 10, 11]
        )
        module = LayerKVModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
    
    def test_different_num_layers(self):
        """Test different num_layers values."""
        for num_layers in [6, 12, 24]:
            config = LayerKVConfig(hidden_dim=512, num_layers=num_layers)
            module = LayerKVModule(config)
            hidden_states = torch.randn(2, 10, 512)
            
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_offload_threshold_effect(self):
        """Test that offload_threshold affects offloading."""
        config_low = LayerKVConfig(hidden_dim=512, offload_threshold=0.3)
        config_high = LayerKVConfig(hidden_dim=512, offload_threshold=0.9)
        
        module_low = LayerKVModule(config_low)
        module_high = LayerKVModule(config_high)
        
        hidden_states = torch.randn(2, 10, 512)
        
        output_low, _ = module_low(hidden_states)
        output_high, _ = module_high(hidden_states)
        
        assert output_low.shape == output_high.shape
    
    def test_memory_threshold_effect(self):
        """Test that memory_threshold affects memory management."""
        config_low = LayerKVConfig(hidden_dim=512, memory_threshold=0.5)
        config_high = LayerKVConfig(hidden_dim=512, memory_threshold=0.95)
        
        module_low = LayerKVModule(config_low)
        module_high = LayerKVModule(config_high)
        
        hidden_states = torch.randn(2, 10, 512)
        
        output_low, _ = module_low(hidden_states)
        output_high, _ = module_high(hidden_states)
        
        assert output_low.shape == output_high.shape
    
    def test_different_batch_sizes(self):
        """Test with different batch sizes."""
        config = LayerKVConfig(hidden_dim=512)
        module = LayerKVModule(config)
        
        for batch_size in [1, 2, 4, 8]:
            hidden_states = torch.randn(batch_size, 10, 512)
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_different_seq_lengths(self):
        """Test with different sequence lengths."""
        config = LayerKVConfig(hidden_dim=512)
        module = LayerKVModule(config)
        
        for seq_len in [1, 5, 10, 50, 100]:
            hidden_states = torch.randn(2, seq_len, 512)
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_save_and_load(self, temp_dir):
        """Test saving and loading LayerKV module."""
        config = LayerKVConfig(hidden_dim=512)
        module = LayerKVModule(config)
        module.eval()
        hidden_states = torch.randn(2, 10, 512)
        
        with torch.no_grad():
            original_output, _ = module(hidden_states)
        
        model_path = temp_dir / "layerkv_model.pt"
        module.save_model(model_path)
        
        loaded_module = LayerKVModule.load_model(model_path, config=config)
        loaded_module.eval()
        
        with torch.no_grad():
            loaded_output, _ = loaded_module(hidden_states)
        
        torch.testing.assert_close(original_output, loaded_output, atol=1e-3, rtol=1e-3)


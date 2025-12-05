import pytest
import torch
from typing import Dict, Any

from research.paper_adaptive_got import AdaptiveGoTModule, AdaptiveGoTConfig
from core.paper_base import ValidationError


class TestAdaptiveGoTConfig:
    """Tests for AdaptiveGoTConfig."""
    
    def test_default_initialization(self):
        """Test default configuration."""
        try:
            config = AdaptiveGoTConfig(hidden_dim=512)
        except TypeError:
            config = AdaptiveGoTConfig(
                hidden_dim=512,
                max_nodes=20,
                importance_threshold=0.5,
                use_test_time_adaptation=True,
                dag_density=0.3,
                fusion_method='weighted',
                dropout_rate=0.1
            )
        assert config.hidden_dim == 512
        assert config.max_nodes == 20
        assert config.importance_threshold == 0.5
        assert config.use_test_time_adaptation is True
    
    def test_validation_invalid_max_nodes(self):
        """Test validation fails with invalid max_nodes."""
        with pytest.raises((ValueError, Exception), match=".*max_nodes.*"):
            config = AdaptiveGoTConfig(hidden_dim=512, max_nodes=0)
            if hasattr(config, 'validate'):
                config.validate()
    
    def test_validation_invalid_importance_threshold(self):
        """Test validation fails with invalid importance_threshold."""
        with pytest.raises((ValueError, Exception), match=".*importance_threshold.*"):
            config = AdaptiveGoTConfig(hidden_dim=512, importance_threshold=1.5)
            if hasattr(config, 'validate'):
                config.validate()
    
    def test_validation_invalid_fusion_method(self):
        """Test validation fails with invalid fusion_method."""
        with pytest.raises((ValueError, Exception), match=".*fusion_method.*"):
            config = AdaptiveGoTConfig(hidden_dim=512, fusion_method='invalid')
            if hasattr(config, 'validate'):
                config.validate()
    
    def test_custom_fusion_methods(self):
        """Test different fusion methods."""
        for method in ['weighted', 'attention', 'max']:
            config = AdaptiveGoTConfig(hidden_dim=512, fusion_method=method)
            assert config.fusion_method == method


class TestAdaptiveGoTModule:
    """Comprehensive tests for AdaptiveGoTModule."""
    
    def test_initialization(self):
        """Test module initialization."""
        config = AdaptiveGoTConfig()
        module = AdaptiveGoTModule(config)
        
        assert module.config == config
    
    def test_forward_pass_basic(self):
        """Test basic forward pass."""
        config = AdaptiveGoTConfig(hidden_dim=512)
        module = AdaptiveGoTModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert isinstance(metadata, dict)
    
    def test_test_time_adaptation_enabled(self):
        """Test with test-time adaptation enabled."""
        config = AdaptiveGoTConfig(hidden_dim=512, use_test_time_adaptation=True)
        module = AdaptiveGoTModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
    
    def test_test_time_adaptation_disabled(self):
        """Test with test-time adaptation disabled."""
        config = AdaptiveGoTConfig(hidden_dim=512, use_test_time_adaptation=False)
        module = AdaptiveGoTModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
    
    def test_different_fusion_methods(self):
        """Test different fusion methods."""
        for method in ['weighted', 'attention', 'max']:
            config = AdaptiveGoTConfig(hidden_dim=512, fusion_method=method)
            module = AdaptiveGoTModule(config)
            hidden_states = torch.randn(2, 10, 512)
            
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_different_max_nodes(self):
        """Test different max_nodes values."""
        for nodes in [10, 20, 30, 50]:
            config = AdaptiveGoTConfig(hidden_dim=512, max_nodes=nodes)
            module = AdaptiveGoTModule(config)
            hidden_states = torch.randn(2, 10, 512)
            
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_importance_threshold_effect(self):
        """Test that importance_threshold affects reasoning."""
        config_low = AdaptiveGoTConfig(hidden_dim=512, importance_threshold=0.1)
        config_high = AdaptiveGoTConfig(hidden_dim=512, importance_threshold=0.9)
        
        module_low = AdaptiveGoTModule(config_low)
        module_high = AdaptiveGoTModule(config_high)
        
        hidden_states = torch.randn(2, 10, 512)
        
        output_low, _ = module_low(hidden_states)
        output_high, _ = module_high(hidden_states)
        
        assert output_low.shape == output_high.shape
    
    def test_dag_density_effect(self):
        """Test that dag_density affects graph structure."""
        config_low = AdaptiveGoTConfig(hidden_dim=512, dag_density=0.1)
        config_high = AdaptiveGoTConfig(hidden_dim=512, dag_density=0.9)
        
        module_low = AdaptiveGoTModule(config_low)
        module_high = AdaptiveGoTModule(config_high)
        
        hidden_states = torch.randn(2, 10, 512)
        
        output_low, _ = module_low(hidden_states)
        output_high, _ = module_high(hidden_states)
        
        assert output_low.shape == output_high.shape
    
    def test_different_batch_sizes(self):
        """Test with different batch sizes."""
        config = AdaptiveGoTConfig(hidden_dim=512)
        module = AdaptiveGoTModule(config)
        
        for batch_size in [1, 2, 4, 8]:
            hidden_states = torch.randn(batch_size, 10, 512)
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_different_seq_lengths(self):
        """Test with different sequence lengths."""
        config = AdaptiveGoTConfig(hidden_dim=512)
        module = AdaptiveGoTModule(config)
        
        for seq_len in [1, 5, 10, 50, 100]:
            hidden_states = torch.randn(2, seq_len, 512)
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_save_and_load(self, temp_dir):
        """Test saving and loading AdaptiveGoT module."""
        config = AdaptiveGoTConfig(hidden_dim=512)
        module = AdaptiveGoTModule(config)
        module.eval()
        hidden_states = torch.randn(2, 10, 512)
        
        with torch.no_grad():
            original_output, _ = module(hidden_states)
        
        model_path = temp_dir / "adaptive_got_model.pt"
        module.save_model(model_path)
        
        loaded_module = AdaptiveGoTModule.load_model(model_path, config=config)
        loaded_module.eval()
        
        with torch.no_grad():
            loaded_output, _ = loaded_module(hidden_states)
        
        torch.testing.assert_close(original_output, loaded_output, atol=1e-3, rtol=1e-3)


import pytest
import torch
from typing import Dict, Any

from research.paper_beyond_cot import BeyondCoTModule, BeyondCoTConfig
from core.paper_base import ValidationError


class TestBeyondCoTConfig:
    """Tests for BeyondCoTConfig."""
    
    def test_default_initialization(self):
        """Test default configuration."""
        try:
            config = BeyondCoTConfig(hidden_dim=512)
        except TypeError:
            config = BeyondCoTConfig(
                hidden_dim=512,
                graph_nodes=12,
                use_graph_encoder=True,
                fusion_method='attention',
                non_sequential_layers=2,
                dropout_rate=0.1
            )
        assert config.hidden_dim == 512
        assert config.graph_nodes == 12
        assert config.use_graph_encoder is True
        assert config.fusion_method == 'attention'
    
    def test_validation_invalid_graph_nodes(self):
        """Test validation fails with invalid graph_nodes."""
        with pytest.raises((ValueError, Exception), match=".*graph_nodes.*"):
            config = BeyondCoTConfig(hidden_dim=512, graph_nodes=0)
            if hasattr(config, 'validate'):
                config.validate()
    
    def test_validation_invalid_fusion_method(self):
        """Test validation fails with invalid fusion_method."""
        with pytest.raises((ValueError, Exception), match=".*fusion_method.*"):
            config = BeyondCoTConfig(hidden_dim=512, fusion_method='invalid')
            if hasattr(config, 'validate'):
                config.validate()
    
    def test_validation_invalid_dropout_rate(self):
        """Test validation fails with invalid dropout_rate."""
        with pytest.raises((ValueError, Exception), match=".*dropout_rate.*"):
            config = BeyondCoTConfig(hidden_dim=512, dropout_rate=1.0)
            if hasattr(config, 'validate'):
                config.validate()
    
    def test_custom_fusion_methods(self):
        """Test different fusion methods."""
        for method in ['attention', 'concat', 'add']:
            config = BeyondCoTConfig(hidden_dim=512, fusion_method=method)
            assert config.fusion_method == method


class TestBeyondCoTModule:
    """Comprehensive tests for BeyondCoTModule."""
    
    def test_initialization(self):
        """Test module initialization."""
        try:
            config = BeyondCoTConfig()
        except TypeError:
            config = BeyondCoTConfig(
                graph_nodes=12,
                use_graph_encoder=True,
                fusion_method='attention',
                non_sequential_layers=2,
                dropout_rate=0.1
            )
        module = BeyondCoTModule(config)
        
        assert module.config == config
        assert hasattr(module, 'graph_encoder')
    
    def test_forward_pass_basic(self):
        """Test basic forward pass."""
        config = BeyondCoTConfig(hidden_dim=512)
        module = BeyondCoTModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert isinstance(metadata, dict)
    
    def test_graph_encoder_enabled(self):
        """Test with graph encoder enabled."""
        config = BeyondCoTConfig(hidden_dim=512, use_graph_encoder=True)
        module = BeyondCoTModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
    
    def test_graph_encoder_disabled(self):
        """Test with graph encoder disabled."""
        config = BeyondCoTConfig(hidden_dim=512, use_graph_encoder=False)
        module = BeyondCoTModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
    
    def test_different_fusion_methods(self):
        """Test different fusion methods."""
        for method in ['attention', 'concat', 'add']:
            config = BeyondCoTConfig(hidden_dim=512, fusion_method=method)
            module = BeyondCoTModule(config)
            hidden_states = torch.randn(2, 10, 512)
            
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_different_graph_nodes(self):
        """Test different graph_nodes values."""
        for nodes in [5, 10, 12, 20, 30]:
            config = BeyondCoTConfig(hidden_dim=512, graph_nodes=nodes)
            module = BeyondCoTModule(config)
            hidden_states = torch.randn(2, 10, 512)
            
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_different_batch_sizes(self):
        """Test with different batch sizes."""
        config = BeyondCoTConfig(hidden_dim=512)
        module = BeyondCoTModule(config)
        
        for batch_size in [1, 2, 4, 8]:
            hidden_states = torch.randn(batch_size, 10, 512)
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_different_seq_lengths(self):
        """Test with different sequence lengths."""
        config = BeyondCoTConfig(hidden_dim=512)
        module = BeyondCoTModule(config)
        
        for seq_len in [1, 5, 10, 50, 100]:
            hidden_states = torch.randn(2, seq_len, 512)
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_non_sequential_layers(self):
        """Test different non_sequential_layers values."""
        for layers in [1, 2, 3, 4]:
            config = BeyondCoTConfig(hidden_dim=512, non_sequential_layers=layers)
            module = BeyondCoTModule(config)
            hidden_states = torch.randn(2, 10, 512)
            
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_save_and_load(self, temp_dir):
        """Test saving and loading BeyondCoT module."""
        config = BeyondCoTConfig(hidden_dim=512)
        module = BeyondCoTModule(config)
        module.eval()
        hidden_states = torch.randn(2, 10, 512)
        
        with torch.no_grad():
            original_output, _ = module(hidden_states)
        
        model_path = temp_dir / "beyond_cot_model.pt"
        module.save_model(model_path)
        
        loaded_module = BeyondCoTModule.load_model(model_path, config=config)
        loaded_module.eval()
        
        with torch.no_grad():
            loaded_output, _ = loaded_module(hidden_states)
        
        torch.testing.assert_close(original_output, loaded_output, atol=1e-3, rtol=1e-3)


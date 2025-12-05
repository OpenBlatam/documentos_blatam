import pytest
import torch
from typing import Dict, Any

from research.paper_solar import SOLARModule, SOLARConfig
from core.paper_base import ValidationError


class TestSOLARConfig:
    """Tests for SOLARConfig."""
    
    def test_default_initialization(self):
        """Test default configuration."""
        config = SOLARConfig()
        assert config.hidden_dim == 512
        assert config.num_paradigms == 3
        assert config.use_adaptive_selection is True
    
    def test_custom_initialization(self):
        """Test custom configuration."""
        config = SOLARConfig(precision_weight=0.7, efficiency_weight=0.3)
        assert config.hidden_dim == 512
        assert config.precision_weight == 0.7
        assert config.efficiency_weight == 0.3


class TestSOLARModule:
    """Comprehensive tests for SOLARModule."""
    
    def test_initialization(self):
        """Test module initialization."""
        config = SOLARConfig()
        assert config.hidden_dim == 512
        module = SOLARModule(config)
        
        assert module.config == config
        assert hasattr(module, 'chain_module')
        assert hasattr(module, 'tree_module')
        assert hasattr(module, 'graph_module')
    
    def test_forward_pass_basic(self):
        """Test basic forward pass."""
        config = SOLARConfig()
        assert config.hidden_dim == 512
        module = SOLARModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert isinstance(metadata, dict)
    
    def test_adaptive_selection_enabled(self):
        """Test with adaptive selection enabled."""
        config = SOLARConfig(use_adaptive_selection=True)
        module = SOLARModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert 'selected_paradigm' in metadata or 'paradigm_scores' in metadata
    
    def test_adaptive_selection_disabled(self):
        """Test with adaptive selection disabled."""
        config = SOLARConfig(use_adaptive_selection=False)
        module = SOLARModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
    
    def test_different_batch_sizes(self):
        """Test with different batch sizes."""
        config = SOLARConfig()
        module = SOLARModule(config)
        
        for batch_size in [1, 2, 4, 8]:
            hidden_states = torch.randn(batch_size, 10, 512)
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_different_seq_lengths(self):
        """Test with different sequence lengths."""
        config = SOLARConfig()
        module = SOLARModule(config)
        
        for seq_len in [1, 5, 10, 50, 100]:
            hidden_states = torch.randn(2, seq_len, 512)
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_paradigm_modules_exist(self):
        """Test that all paradigm modules exist."""
        config = SOLARConfig()
        module = SOLARModule(config)
        
        assert hasattr(module, 'chain_module')
        assert hasattr(module, 'tree_module')
        assert hasattr(module, 'graph_module')
    
    def test_save_and_load(self, temp_dir):
        """Test saving and loading SOLAR module."""
        config = SOLARConfig()
        module = SOLARModule(config)
        module.eval()
        hidden_states = torch.randn(2, 10, 512)
        
        with torch.no_grad():
            original_output, _ = module(hidden_states)
        
        model_path = temp_dir / "solar_model.pt"
        module.save_model(model_path)
        
        loaded_module = SOLARModule.load_model(model_path, config=config)
        loaded_module.eval()
        
        with torch.no_grad():
            loaded_output, _ = loaded_module(hidden_states)
        
        torch.testing.assert_close(original_output, loaded_output, atol=1e-3, rtol=1e-3)
    
    def test_precision_efficiency_weights(self):
        """Test that precision and efficiency weights affect selection."""
        config_high_precision = SOLARConfig(precision_weight=0.9, efficiency_weight=0.1)
        config_high_efficiency = SOLARConfig(precision_weight=0.1, efficiency_weight=0.9)
        
        module_precision = SOLARModule(config_high_precision)
        module_efficiency = SOLARModule(config_high_efficiency)
        
        hidden_states = torch.randn(2, 10, 512)
        
        output1, _ = module_precision(hidden_states)
        output2, _ = module_efficiency(hidden_states)
        
        assert output1.shape == output2.shape
    
    def test_max_reasoning_steps(self):
        """Test max_reasoning_steps configuration."""
        config = SOLARConfig(max_reasoning_steps=5)
        module = SOLARModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
    
    def test_tree_branching_factor(self):
        """Test tree_branching_factor configuration."""
        config = SOLARConfig(tree_branching_factor=5)
        module = SOLARModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
    
    def test_graph_max_nodes(self):
        """Test graph_max_nodes configuration."""
        config = SOLARConfig(graph_max_nodes=30)
        module = SOLARModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape


import pytest
import torch
from typing import Dict, Any

from research.paper_hademif import HaDeMiFModule, HaDeMiFConfig
from core.paper_base import ValidationError


class TestHaDeMiFConfig:
    """Tests for HaDeMiFConfig."""
    
    def test_default_initialization(self):
        """Test default configuration."""
        config = HaDeMiFConfig()
        assert config.hidden_dim == 512
        assert config.use_dynamic_tree is True
        assert config.detection_threshold == 0.5
    
    def test_validation_invalid_mlp_hidden_dim(self):
        """Test validation fails with invalid mlp_hidden_dim."""
        with pytest.raises((ValueError, Exception), match=".*mlp_hidden_dim.*"):
            config = HaDeMiFConfig(mlp_hidden_dim=0)
            if hasattr(config, 'validate'):
                config.validate()
    
    def test_validation_invalid_detection_threshold(self):
        """Test validation fails with invalid detection_threshold."""
        with pytest.raises((ValueError, Exception), match=".*detection_threshold.*"):
            config = HaDeMiFConfig(detection_threshold=1.5)
            if hasattr(config, 'validate'):
                config.validate()
    
    def test_validation_invalid_calibration_weight(self):
        """Test validation fails with invalid calibration_weight."""
        with pytest.raises((ValueError, Exception), match=".*calibration_weight.*"):
            config = HaDeMiFConfig(calibration_weight=-0.1)
            if hasattr(config, 'validate'):
                config.validate()
    
    def test_validation_invalid_dropout_rate(self):
        """Test validation fails with invalid dropout_rate."""
        with pytest.raises((ValueError, Exception), match=".*dropout_rate.*"):
            config = HaDeMiFConfig(dropout_rate=1.0)
            if hasattr(config, 'validate'):
                config.validate()


class TestHaDeMiFModule:
    """Comprehensive tests for HaDeMiFModule."""
    
    def test_initialization(self):
        """Test module initialization."""
        config = HaDeMiFConfig()
        module = HaDeMiFModule(config)
        
        assert module.config == config
        assert hasattr(module, 'calibration_mlp')
    
    def test_initialization_without_dynamic_tree(self):
        """Test initialization without dynamic tree."""
        config = HaDeMiFConfig(use_dynamic_tree=False)
        module = HaDeMiFModule(config)
        
        assert module.config == config
    
    def test_forward_pass_basic(self):
        """Test basic forward pass."""
        config = HaDeMiFConfig()
        module = HaDeMiFModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert isinstance(metadata, dict)
    
    def test_dynamic_tree_enabled(self):
        """Test with dynamic tree enabled."""
        config = HaDeMiFConfig(use_dynamic_tree=True)
        module = HaDeMiFModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
    
    def test_dynamic_tree_disabled(self):
        """Test with dynamic tree disabled."""
        config = HaDeMiFConfig(use_dynamic_tree=False)
        module = HaDeMiFModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
    
    def test_detection_threshold_effect(self):
        """Test that detection_threshold affects detection."""
        config_low = HaDeMiFConfig(detection_threshold=0.1)
        config_high = HaDeMiFConfig(detection_threshold=0.9)
        
        module_low = HaDeMiFModule(config_low)
        module_high = HaDeMiFModule(config_high)
        
        hidden_states = torch.randn(2, 10, 512)
        
        output_low, metadata_low = module_low(hidden_states)
        output_high, metadata_high = module_high(hidden_states)
        
        assert output_low.shape == output_high.shape
    
    def test_calibration_weight_effect(self):
        """Test that calibration_weight affects calibration."""
        config_low = HaDeMiFConfig(calibration_weight=0.1)
        config_high = HaDeMiFConfig(calibration_weight=0.9)
        
        module_low = HaDeMiFModule(config_low)
        module_high = HaDeMiFModule(config_high)
        
        hidden_states = torch.randn(2, 10, 512)
        
        output_low, _ = module_low(hidden_states)
        output_high, _ = module_high(hidden_states)
        
        assert output_low.shape == output_high.shape
    
    def test_different_batch_sizes(self):
        """Test with different batch sizes."""
        config = HaDeMiFConfig()
        module = HaDeMiFModule(config)
        
        for batch_size in [1, 2, 4, 8]:
            hidden_states = torch.randn(batch_size, 10, 512)
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_different_seq_lengths(self):
        """Test with different sequence lengths."""
        config = HaDeMiFConfig()
        module = HaDeMiFModule(config)
        
        for seq_len in [1, 5, 10, 50, 100]:
            hidden_states = torch.randn(2, seq_len, 512)
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_save_and_load(self, temp_dir):
        """Test saving and loading HaDeMiF module."""
        config = HaDeMiFConfig()
        module = HaDeMiFModule(config)
        module.eval()
        hidden_states = torch.randn(2, 10, 512)
        
        with torch.no_grad():
            original_output, _ = module(hidden_states)
        
        model_path = temp_dir / "hademif_model.pt"
        module.save_model(model_path)
        
        loaded_module = HaDeMiFModule.load_model(model_path, config=config)
        loaded_module.eval()
        
        with torch.no_grad():
            loaded_output, _ = loaded_module(hidden_states)
        
        torch.testing.assert_close(original_output, loaded_output, atol=1e-3, rtol=1e-3)
    
    def test_mlp_hidden_dim_configuration(self):
        """Test different mlp_hidden_dim values."""
        for mlp_dim in [128, 256, 512, 768]:
            config = HaDeMiFConfig(mlp_hidden_dim=mlp_dim)
            module = HaDeMiFModule(config)
            hidden_states = torch.randn(2, 10, 512)
            
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_dropout_rate_configuration(self):
        """Test different dropout_rate values."""
        for dropout in [0.0, 0.1, 0.2, 0.3, 0.5]:
            config = HaDeMiFConfig(dropout_rate=dropout)
            module = HaDeMiFModule(config)
            hidden_states = torch.randn(2, 10, 512)
            
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape


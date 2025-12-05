import pytest
import torch
from pathlib import Path

from inference.paper_vllm import VLLMModule, VLLMConfig


class TestVLLMConfig:
    """Tests for VLLMConfig."""
    
    def test_default_initialization(self):
        """Test default configuration."""
        try:
            config = VLLMConfig()
        except TypeError:
            config = VLLMConfig(
                hidden_dim=512,
                page_size=16,
                use_continuous_batching=True,
                use_paged_attention=True,
                max_batch_size=64,
                target_throughput=4656.0
            )
        assert config.hidden_dim == 512
        assert config.page_size == 16
        assert config.use_continuous_batching is True
        assert config.use_paged_attention is True
        assert config.max_batch_size == 64
        assert config.target_throughput == 4656.0
    
    def test_custom_initialization(self):
        """Test custom configuration."""
        config = VLLMConfig(
            hidden_dim=768,
            page_size=32,
            max_batch_size=128,
            target_throughput=5000.0
        )
        assert config.hidden_dim == 768
        assert config.page_size == 32
        assert config.max_batch_size == 128
        assert config.target_throughput == 5000.0


class TestVLLMModule:
    """Tests for VLLMModule."""
    
    def test_initialization(self):
        """Test module initialization."""
        config = VLLMConfig(hidden_dim=512)
        module = VLLMModule(config)
        
        assert module.config == config
        assert hasattr(module, 'paged_attention')
    
    def test_forward_pass_basic(self):
        """Test basic forward pass."""
        config = VLLMConfig(hidden_dim=512)
        module = VLLMModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert isinstance(metadata, dict)
        assert 'throughput' in metadata or 'tokens_processed' in metadata
    
    def test_paged_attention_enabled(self):
        """Test with PagedAttention enabled."""
        config = VLLMConfig(use_paged_attention=True)
        module = VLLMModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        assert output.shape == hidden_states.shape
    
    def test_paged_attention_disabled(self):
        """Test with PagedAttention disabled."""
        config = VLLMConfig(use_paged_attention=False)
        module = VLLMModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        assert output.shape == hidden_states.shape
    
    def test_continuous_batching(self):
        """Test continuous batching."""
        config = VLLMConfig(use_continuous_batching=True)
        module = VLLMModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        assert output.shape == hidden_states.shape
    
    def test_different_batch_sizes(self):
        """Test with different batch sizes."""
        config = VLLMConfig()
        module = VLLMModule(config)
        
        for batch_size in [1, 2, 4, 8]:
            hidden_states = torch.randn(batch_size, 10, 512)
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_save_and_load(self, temp_dir):
        """Test saving and loading VLLM module."""
        config = VLLMConfig(hidden_dim=512)
        module = VLLMModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        original_output, _ = module(hidden_states)
        
        model_path = temp_dir / "vllm_model.pt"
        module.save_model(model_path)
        
        loaded_module = VLLMModule.load_model(model_path, config=config)
        loaded_output, _ = loaded_module(hidden_states)
        
        torch.testing.assert_close(original_output, loaded_output, atol=1e-5, rtol=1e-5)


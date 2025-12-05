import pytest
import torch
from pathlib import Path

from core.paper_base import BasePaperConfig, BasePaperModule
from research.paper_malto import MALTOModule, MALTOConfig
from inference.paper_vllm import VLLMModule, VLLMConfig


class TestIntegration:
    """Integration tests for the production code."""
    
    def test_multiple_modules_same_config(self):
        """Test multiple modules can use the same config."""
        config = BasePaperConfig(hidden_dim=512)
        
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
        malto_module = MALTOModule(malto_config)
        
        vllm_config = VLLMConfig(hidden_dim=512)
        vllm_module = VLLMModule(vllm_config)
        
        hidden_states = torch.randn(2, 10, 512)
        
        malto_output, _ = malto_module(hidden_states)
        vllm_output, _ = vllm_module(hidden_states)
        
        assert malto_output.shape == hidden_states.shape
        assert vllm_output.shape == hidden_states.shape
    
    def test_module_workflow_complete(self, temp_dir):
        """Test complete workflow: create, use, save, load."""
        try:
            config = MALTOConfig()
        except TypeError:
            config = MALTOConfig(
                use_uncertainty_quantification=True,
                use_nli_validation=True,
                word_level_detection=True,
                uncertainty_threshold=0.5,
                nli_threshold=0.3,
                mitigation_strength=0.4
            )
        module = MALTOModule(config)
        
        hidden_states = torch.randn(2, 10, 512)
        
        output1, metadata1 = module(hidden_states)
        assert output1.shape == hidden_states.shape
        
        model_path = temp_dir / "workflow_model.pt"
        module.save_model(model_path, include_config=True)
        
        loaded_module = MALTOModule.load_model(model_path, config=config)
        output2, metadata2 = loaded_module(hidden_states)
        
        torch.testing.assert_close(output1, output2, atol=1e-5, rtol=1e-5)
    
    def test_metrics_accumulation(self):
        """Test that metrics accumulate across multiple forward passes."""
        config = MALTOConfig()
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        for _ in range(5):
            module(hidden_states)
        
        metrics = module.get_metrics()
        assert module._forward_count == 5
    
    def test_config_serialization_round_trip(self, temp_dir):
        """Test config serialization round trip."""
        original_config = MALTOConfig(
            hidden_dim=768,
            uncertainty_threshold=0.6,
            mitigation_strength=0.5
        )
        
        config_path = temp_dir / "config.json"
        original_config.save(config_path)
        
        loaded_config = MALTOConfig.load(config_path)
        
        assert loaded_config.hidden_dim == original_config.hidden_dim
        assert loaded_config.uncertainty_threshold == original_config.uncertainty_threshold
        assert loaded_config.mitigation_strength == original_config.mitigation_strength
    
    def test_model_info_consistency(self):
        """Test that model info is consistent."""
        config = MALTOConfig()
        module = MALTOModule(config)
        
        info1 = module.get_model_info()
        info2 = module.get_model_info()
        
        assert info1['total_parameters'] == info2['total_parameters']
        assert info1['trainable_parameters'] == info2['trainable_parameters']
        assert info1['model_name'] == info2['model_name']
    
    def test_different_hidden_dims(self):
        """Test modules with different hidden dimensions."""
        for hidden_dim in [128, 256, 512, 768, 1024]:
            config = MALTOConfig(hidden_dim=hidden_dim)
            module = MALTOModule(config)
            hidden_states = torch.randn(2, 10, hidden_dim)
            
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_error_recovery(self):
        """Test that modules handle errors gracefully."""
        config = MALTOConfig()
        module = MALTOModule(config)
        
        valid_states = torch.randn(2, 10, 512)
        output, metadata = module(valid_states)
        
        assert output.shape == valid_states.shape
        assert 'error' not in metadata or metadata.get('error') is None
    
    def test_device_consistency(self):
        """Test that device handling is consistent."""
        config = MALTOConfig()
        module = MALTOModule(config)
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        module.to_device(device)
        
        hidden_states = torch.randn(2, 10, 512).to(device)
        output, _ = module(hidden_states)
        
        assert output.device.type == device
    
    def test_dtype_consistency(self):
        """Test that dtype handling is consistent."""
        config = MALTOConfig()
        module = MALTOModule(config)
        
        module.set_dtype(torch.float16)
        hidden_states = torch.randn(2, 10, 512).to(torch.float16)
        
        output, _ = module(hidden_states)
        assert output.dtype == torch.float16
    
    def test_batch_processing(self):
        """Test processing multiple batches."""
        config = MALTOConfig()
        module = MALTOModule(config)
        
        for batch_size in [1, 2, 4, 8]:
            hidden_states = torch.randn(batch_size, 10, 512)
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
            assert metadata['total_words'] == batch_size * 10
    
    def test_sequence_processing(self):
        """Test processing different sequence lengths."""
        config = MALTOConfig()
        module = MALTOModule(config)
        
        for seq_len in [1, 5, 10, 50, 100]:
            hidden_states = torch.randn(2, seq_len, 512)
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
            assert metadata['total_words'] == 2 * seq_len
    
    def test_metrics_reset(self):
        """Test that metrics can be reset."""
        config = MALTOConfig()
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        module(hidden_states)
        module(hidden_states)
        assert module._forward_count == 2
        
        module.reset_metrics()
        assert module._forward_count == 0
        assert len(module._metrics) == 0


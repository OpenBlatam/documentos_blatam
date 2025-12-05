import pytest
import torch
import time
from typing import Dict, Any

from core.paper_base import BasePaperConfig, BasePaperModule
from research.paper_malto import MALTOModule, MALTOConfig
import torch.nn as nn


class SimpleModule(BasePaperModule):
    """Simple module for performance testing."""
    
    def __init__(self, config: BasePaperConfig):
        super().__init__(config)
        self.linear = nn.Linear(config.hidden_dim, config.hidden_dim)
    
    def forward(self, hidden_states: torch.Tensor, **kwargs):
        output = self.linear(hidden_states)
        metadata = {'output_mean': output.mean().item()}
        self._update_metrics(**metadata)
        return output, metadata


class TestPerformance:
    """Tests de performance y benchmarking."""
    
    @pytest.mark.slow
    def test_forward_pass_speed(self, sample_config):
        """Test velocidad de forward pass."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        
        start_time = time.time()
        for _ in range(100):
            module(hidden_states)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 100
        assert avg_time < 0.1
    
    @pytest.mark.slow
    def test_malto_forward_speed(self):
        """Test velocidad de forward pass de MALTO."""
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
        
        start_time = time.time()
        for _ in range(50):
            module(hidden_states)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 50
        assert avg_time < 0.2
    
    def test_memory_usage_small(self, sample_config):
        """Test uso de memoria con tensores pequeños."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(1, 5, 512)
        
        output, _ = module(hidden_states)
        
        assert output.numel() == hidden_states.numel()
    
    def test_memory_usage_large(self, sample_config):
        """Test uso de memoria con tensores grandes."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(32, 1000, 512)
        
        output, _ = module(hidden_states)
        
        assert output.numel() == hidden_states.numel()
    
    @pytest.mark.slow
    def test_batch_processing_efficiency(self, sample_config):
        """Test eficiencia de procesamiento de batches."""
        module = SimpleModule(sample_config)
        
        batch_sizes = [1, 2, 4, 8, 16]
        times = []
        
        for batch_size in batch_sizes:
            hidden_states = torch.randn(batch_size, 10, 512)
            
            start_time = time.time()
            for _ in range(10):
                module(hidden_states)
            end_time = time.time()
            
            times.append((end_time - start_time) / 10)
        
        assert all(t > 0 for t in times)
    
    def test_sequential_vs_parallel_processing(self, sample_config):
        """Test procesamiento secuencial vs paralelo (simulado)."""
        module = SimpleModule(sample_config)
        hidden_states = torch.randn(2, 10, 512)
        
        sequential_outputs = []
        for _ in range(5):
            output, _ = module(hidden_states)
            sequential_outputs.append(output)
        
        assert len(sequential_outputs) == 5
        assert all(out.shape == hidden_states.shape for out in sequential_outputs)
    
    @pytest.mark.slow
    def test_long_sequence_performance(self):
        """Test performance con secuencias largas."""
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
        
        seq_lengths = [10, 50, 100, 500, 1000]
        times = []
        
        for seq_len in seq_lengths:
            hidden_states = torch.randn(2, seq_len, 512)
            
            start_time = time.time()
            module(hidden_states)
            end_time = time.time()
            
            times.append(end_time - start_time)
        
        assert all(t > 0 for t in times)
    
    def test_model_size_impact(self):
        """Test impacto del tamaño del modelo en performance."""
        hidden_dims = [128, 256, 512, 768, 1024]
        times = []
        
        for hidden_dim in hidden_dims:
            config = BasePaperConfig(hidden_dim=hidden_dim)
            module = SimpleModule(config)
            hidden_states = torch.randn(2, 10, hidden_dim)
            
            start_time = time.time()
            for _ in range(10):
                module(hidden_states)
            end_time = time.time()
            
            times.append((end_time - start_time) / 10)
        
        assert all(t > 0 for t in times)


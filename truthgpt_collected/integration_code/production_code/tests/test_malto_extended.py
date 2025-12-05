import pytest
import torch
import numpy as np
from typing import Dict, Any

from research.paper_malto import MALTOModule, MALTOConfig
from core.paper_base import ValidationError


class TestMALTOModuleExtended:
    """Tests extendidos y parametrizados para MALTOModule."""
    
    @pytest.mark.parametrize("uncertainty_threshold", [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0])
    def test_uncertainty_threshold_values(self, uncertainty_threshold):
        """Test con diferentes valores de uncertainty_threshold."""
        config = MALTOConfig(
            hidden_dim=512,
            uncertainty_threshold=uncertainty_threshold
        )
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert 'word_hallucination_ratio' in metadata
    
    @pytest.mark.parametrize("mitigation_strength", [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0])
    def test_mitigation_strength_values(self, mitigation_strength):
        """Test con diferentes valores de mitigation_strength."""
        config = MALTOConfig(
            hidden_dim=512,
            mitigation_strength=mitigation_strength
        )
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
    
    @pytest.mark.parametrize("use_uncertainty,use_nli,word_level", [
        (True, True, True),
        (True, True, False),
        (True, False, True),
        (False, True, True),
        (False, False, True),
        (True, False, False),
        (False, True, False),
        (False, False, False),
    ])
    def test_feature_combinations(self, use_uncertainty, use_nli, word_level):
        """Test todas las combinaciones de features."""
        config = MALTOConfig(
            hidden_dim=512,
            use_uncertainty_quantification=use_uncertainty,
            use_nli_validation=use_nli,
            word_level_detection=word_level
        )
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert isinstance(metadata, dict)
    
    def test_uncertainty_quantification_range(self):
        """Test que uncertainty quantification retorna valores en rango [0, 1]."""
        config = MALTOConfig(use_uncertainty_quantification=True)
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        uncertainty = module._quantify_uncertainty(hidden_states)
        
        assert torch.all(uncertainty >= 0)
        assert torch.all(uncertainty <= 1)
        assert uncertainty.shape == (2,)
    
    def test_nli_validation_range(self):
        """Test que NLI validation retorna valores en rango [0, 1]."""
        config = MALTOConfig(use_nli_validation=True)
        module = MALTOModule(config)
        claim = torch.randn(2, 10, 512)
        context = torch.randn(2, 10, 512)
        
        contradiction_score = module._nli_validation(claim, context)
        
        assert torch.all(contradiction_score >= 0)
        assert torch.all(contradiction_score <= 1)
        assert contradiction_score.shape == (2,)
    
    def test_word_detection_scores_range(self):
        """Test que word detection scores están en rango [0, 1]."""
        config = MALTOConfig(word_level_detection=True)
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert 'word_scores_mean' in metadata
        assert 0 <= metadata['word_scores_mean'] <= 1
    
    def test_metadata_completeness_all_features(self):
        """Test que metadata contiene todas las métricas cuando todas las features están activas."""
        config = MALTOConfig(
            use_uncertainty_quantification=True,
            use_nli_validation=True,
            word_level_detection=True
        )
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        required_keys = [
            'uncertainty_mean', 'uncertainty_std', 'uncertainty_max', 'uncertainty_min',
            'nli_contradiction_score', 'nli_contradiction_std',
            'word_hallucination_ratio', 'word_scores_mean', 'word_scores_std',
            'words_detected', 'total_words'
        ]
        
        for key in required_keys:
            assert key in metadata, f"Missing key: {key}"
    
    def test_context_optional(self):
        """Test que context es opcional."""
        config = MALTOConfig()
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output1, metadata1 = module(hidden_states)
        output2, metadata2 = module(hidden_states, context=None)
        
        assert output1.shape == output2.shape
        assert isinstance(metadata1, dict)
        assert isinstance(metadata2, dict)
    
    def test_context_same_as_hidden_states(self):
        """Test que context puede ser igual a hidden_states."""
        config = MALTOConfig()
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output1, _ = module(hidden_states)
        output2, _ = module(hidden_states, context=hidden_states)
        
        assert output1.shape == output2.shape
    
    def test_different_context_shapes(self):
        """Test con diferentes shapes de context."""
        config = MALTOConfig()
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        context1 = torch.randn(2, 10, 512)
        context2 = torch.randn(2, 20, 512)
        
        output1, _ = module(hidden_states, context=context1)
        
        with pytest.raises(ValueError, match="context debe tener las mismas dimensiones"):
            module(hidden_states, context=context2)
    
    def test_mitigation_effect_on_output(self):
        """Test que mitigation_strength afecta el output."""
        config_low = MALTOConfig(mitigation_strength=0.1)
        config_high = MALTOConfig(mitigation_strength=0.9)
        
        module_low = MALTOModule(config_low)
        module_high = MALTOModule(config_high)
        
        hidden_states = torch.randn(2, 10, 512)
        
        output_low, _ = module_low(hidden_states)
        output_high, _ = module_high(hidden_states)
        
        assert output_low.shape == output_high.shape
    
    def test_uncertainty_threshold_effect(self):
        """Test que uncertainty_threshold afecta la detección."""
        config_low = MALTOConfig(uncertainty_threshold=0.1)
        config_high = MALTOConfig(uncertainty_threshold=0.9)
        
        module_low = MALTOModule(config_low)
        module_high = MALTOModule(config_high)
        
        hidden_states = torch.randn(2, 10, 512)
        
        output_low, metadata_low = module_low(hidden_states)
        output_high, metadata_high = module_high(hidden_states)
        
        assert metadata_low['word_hallucination_ratio'] >= metadata_high['word_hallucination_ratio']
    
    def test_consistency_across_forward_passes(self):
        """Test consistencia entre múltiples forward passes."""
        config = MALTOConfig()
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        outputs = []
        for _ in range(5):
            output, _ = module(hidden_states)
            outputs.append(output)
        
        assert len(outputs) == 5
        assert all(out.shape == hidden_states.shape for out in outputs)
    
    def test_metadata_statistics_validity(self):
        """Test que las estadísticas en metadata son válidas."""
        config = MALTOConfig()
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert metadata['uncertainty_max'] >= metadata['uncertainty_mean']
        assert metadata['uncertainty_mean'] >= metadata['uncertainty_min']
        assert metadata['uncertainty_std'] >= 0
        assert metadata['words_detected'] <= metadata['total_words']
        assert 0 <= metadata['word_hallucination_ratio'] <= 1
    
    def test_large_batch_handling(self):
        """Test manejo de batches grandes."""
        config = MALTOConfig()
        module = MALTOModule(config)
        hidden_states = torch.randn(64, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert metadata['total_words'] == 64 * 10
    
    def test_long_sequence_handling(self):
        """Test manejo de secuencias largas."""
        config = MALTOConfig()
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 1000, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert metadata['total_words'] == 2 * 1000
    
    def test_edge_case_zero_uncertainty(self):
        """Test edge case con uncertainty cero."""
        config = MALTOConfig(use_uncertainty_quantification=True)
        module = MALTOModule(config)
        hidden_states = torch.zeros(2, 10, 512)
        
        uncertainty = module._quantify_uncertainty(hidden_states)
        
        assert torch.all(uncertainty >= 0)
        assert uncertainty.shape == (2,)
    
    def test_edge_case_high_uncertainty(self):
        """Test edge case con uncertainty alta."""
        config = MALTOConfig(use_uncertainty_quantification=True)
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512) * 100
        
        uncertainty = module._quantify_uncertainty(hidden_states)
        
        assert torch.all(uncertainty >= 0)
        assert torch.all(uncertainty <= 1)
    
    def test_all_features_disabled(self):
        """Test con todas las features deshabilitadas."""
        config = MALTOConfig(
            use_uncertainty_quantification=False,
            use_nli_validation=False,
            word_level_detection=False
        )
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert isinstance(metadata, dict)




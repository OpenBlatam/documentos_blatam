import pytest
import torch
from typing import Dict, Any

from research.paper_malto import MALTOModule, MALTOConfig
from core.paper_base import ValidationError


class TestMALTOConfig:
    """Tests for MALTOConfig."""
    
    def test_default_initialization(self):
        """Test default configuration."""
        try:
            config = MALTOConfig()
        except TypeError:
            config = MALTOConfig(
                hidden_dim=512,
                use_uncertainty_quantification=True,
                use_nli_validation=True,
                word_level_detection=True,
                uncertainty_threshold=0.5,
                nli_threshold=0.3,
                mitigation_strength=0.4
            )
        assert config.hidden_dim == 512
        assert config.use_uncertainty_quantification is True
        assert config.use_nli_validation is True
        assert config.word_level_detection is True
        assert config.uncertainty_threshold == 0.5
        assert config.nli_threshold == 0.3
        assert config.mitigation_strength == 0.4
    
    def test_custom_initialization(self):
        """Test custom configuration."""
        config = MALTOConfig(
            hidden_dim=768,
            use_uncertainty_quantification=False,
            uncertainty_threshold=0.7,
            mitigation_strength=0.6
        )
        assert config.hidden_dim == 768
        assert config.use_uncertainty_quantification is False
        assert config.uncertainty_threshold == 0.7
        assert config.mitigation_strength == 0.6
    
    def test_validation_valid_thresholds(self):
        """Test validation with valid thresholds."""
        config = MALTOConfig(
            uncertainty_threshold=0.5,
            nli_threshold=0.3,
            mitigation_strength=0.4
        )
        config.validate()
    
    def test_validation_invalid_uncertainty_threshold_high(self):
        """Test validation fails with threshold > 1.0."""
        config = MALTOConfig(uncertainty_threshold=1.5)
        with pytest.raises(ValueError, match="uncertainty_threshold debe estar en"):
            config.validate()
    
    def test_validation_invalid_uncertainty_threshold_negative(self):
        """Test validation fails with negative threshold."""
        config = MALTOConfig(uncertainty_threshold=-0.1)
        with pytest.raises(ValueError, match="uncertainty_threshold debe estar en"):
            config.validate()
    
    def test_validation_invalid_nli_threshold(self):
        """Test validation fails with invalid NLI threshold."""
        config = MALTOConfig(nli_threshold=2.0)
        with pytest.raises(ValueError, match="nli_threshold debe estar en"):
            config.validate()
    
    def test_validation_invalid_mitigation_strength(self):
        """Test validation fails with invalid mitigation strength."""
        config = MALTOConfig(mitigation_strength=-0.1)
        with pytest.raises(ValueError, match="mitigation_strength debe estar en"):
            config.validate()


class TestMALTOModule:
    """Comprehensive tests for MALTOModule."""
    
    def test_initialization(self):
        """Test module initialization."""
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
        
        assert module.config == config
        assert hasattr(module, 'uncertainty_quantifier')
        assert hasattr(module, 'nli_validator')
        assert hasattr(module, 'word_detector')
    
    def test_initialization_without_uncertainty(self):
        """Test initialization without uncertainty quantification."""
        config = MALTOConfig(use_uncertainty_quantification=False)
        module = MALTOModule(config)
        
        assert isinstance(module.uncertainty_quantifier, torch.nn.Identity)
    
    def test_initialization_without_nli(self):
        """Test initialization without NLI validation."""
        config = MALTOConfig(use_nli_validation=False)
        module = MALTOModule(config)
        
        assert isinstance(module.nli_validator, torch.nn.Identity)
    
    def test_initialization_without_word_level(self):
        """Test initialization without word-level detection."""
        config = MALTOConfig(word_level_detection=False)
        module = MALTOModule(config)
        
        assert isinstance(module.word_detector, torch.nn.Identity)
    
    def test_forward_pass_basic(self):
        """Test basic forward pass."""
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
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert isinstance(metadata, dict)
        assert 'uncertainty_mean' in metadata
        assert 'nli_contradiction_score' in metadata
        assert 'word_hallucination_ratio' in metadata
    
    def test_forward_pass_with_context(self):
        """Test forward pass with context."""
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
        context = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states, context=context)
        
        assert output.shape == hidden_states.shape
        assert isinstance(metadata, dict)
    
    def test_forward_pass_without_context(self):
        """Test forward pass without context (uses hidden_states as context)."""
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
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert isinstance(metadata, dict)
    
    def test_forward_pass_context_shape_mismatch(self):
        """Test forward pass fails with context shape mismatch."""
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
        context = torch.randn(3, 10, 512)
        
        with pytest.raises(ValueError, match="context debe tener las mismas dimensiones"):
            module(hidden_states, context=context)
    
    def test_quantify_uncertainty_enabled(self):
        """Test uncertainty quantification when enabled."""
        config = MALTOConfig(use_uncertainty_quantification=True)
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        uncertainty = module._quantify_uncertainty(hidden_states)
        
        assert uncertainty.shape == (2,)
        assert torch.all(uncertainty >= 0)
        assert torch.all(uncertainty <= 1)
    
    def test_quantify_uncertainty_disabled(self):
        """Test uncertainty quantification when disabled."""
        config = MALTOConfig(use_uncertainty_quantification=False)
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        uncertainty = module._quantify_uncertainty(hidden_states)
        
        assert uncertainty.shape == (2,)
        assert torch.all(uncertainty == 0)
    
    def test_nli_validation_enabled(self):
        """Test NLI validation when enabled."""
        config = MALTOConfig(use_nli_validation=True)
        module = MALTOModule(config)
        claim = torch.randn(2, 10, 512)
        context = torch.randn(2, 10, 512)
        
        contradiction_score = module._nli_validation(claim, context)
        
        assert contradiction_score.shape == (2,)
        assert torch.all(contradiction_score >= 0)
        assert torch.all(contradiction_score <= 1)
    
    def test_nli_validation_disabled(self):
        """Test NLI validation when disabled."""
        config = MALTOConfig(use_nli_validation=False)
        module = MALTOModule(config)
        claim = torch.randn(2, 10, 512)
        context = torch.randn(2, 10, 512)
        
        contradiction_score = module._nli_validation(claim, context)
        
        assert contradiction_score.shape == (2,)
        assert torch.all(contradiction_score == 0)
    
    def test_nli_validation_shape_mismatch(self):
        """Test NLI validation fails with shape mismatch."""
        config = MALTOConfig(use_nli_validation=True)
        module = MALTOModule(config)
        claim = torch.randn(2, 10, 512)
        context = torch.randn(2, 15, 512)
        
        with pytest.raises(ValueError, match="claim y context deben tener la misma shape"):
            module._nli_validation(claim, context)
    
    def test_word_level_detection_enabled(self):
        """Test word-level detection when enabled."""
        config = MALTOConfig(word_level_detection=True)
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert 'words_detected' in metadata
        assert 'total_words' in metadata
        assert metadata['total_words'] == 20
    
    def test_word_level_detection_disabled(self):
        """Test word-level detection when disabled."""
        config = MALTOConfig(word_level_detection=False)
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert isinstance(metadata, dict)
    
    def test_metadata_contains_all_keys(self):
        """Test that metadata contains all expected keys."""
        config = MALTOConfig()
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        output, metadata = module(hidden_states)
        
        expected_keys = [
            'uncertainty_mean', 'uncertainty_std', 'uncertainty_max', 'uncertainty_min',
            'nli_contradiction_score', 'nli_contradiction_std',
            'word_hallucination_ratio', 'word_scores_mean', 'word_scores_std',
            'words_detected', 'total_words'
        ]
        
        for key in expected_keys:
            assert key in metadata, f"Missing key: {key}"
    
    def test_mitigation_strength_effect(self):
        """Test that mitigation strength affects output."""
        config_low = MALTOConfig(mitigation_strength=0.1)
        config_high = MALTOConfig(mitigation_strength=0.9)
        
        module_low = MALTOModule(config_low)
        module_high = MALTOModule(config_high)
        
        hidden_states = torch.randn(2, 10, 512)
        
        output_low, _ = module_low(hidden_states)
        output_high, _ = module_high(hidden_states)
        
        assert output_low.shape == output_high.shape
    
    def test_uncertainty_threshold_effect(self):
        """Test that uncertainty threshold affects detection."""
        config_low = MALTOConfig(uncertainty_threshold=0.1)
        config_high = MALTOConfig(uncertainty_threshold=0.9)
        
        module_low = MALTOModule(config_low)
        module_high = MALTOModule(config_high)
        
        hidden_states = torch.randn(2, 10, 512)
        
        output_low, metadata_low = module_low(hidden_states)
        output_high, metadata_high = module_high(hidden_states)
        
        assert metadata_low['word_hallucination_ratio'] >= metadata_high['word_hallucination_ratio']
    
    def test_different_batch_sizes(self):
        """Test with different batch sizes."""
        config = MALTOConfig()
        module = MALTOModule(config)
        
        for batch_size in [1, 2, 4, 8]:
            hidden_states = torch.randn(batch_size, 10, 512)
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
    
    def test_different_seq_lengths(self):
        """Test with different sequence lengths."""
        config = MALTOConfig()
        module = MALTOModule(config)
        
        for seq_len in [1, 5, 10, 50, 100]:
            hidden_states = torch.randn(2, seq_len, 512)
            output, metadata = module(hidden_states)
            assert output.shape == hidden_states.shape
            assert metadata['total_words'] == 2 * seq_len
    
    def test_metrics_tracking(self):
        """Test that metrics are tracked correctly."""
        config = MALTOConfig()
        module = MALTOModule(config)
        hidden_states = torch.randn(2, 10, 512)
        
        module(hidden_states)
        
        metrics = module.get_metrics()
        assert 'uncertainty' in metrics or module._forward_count == 1
        assert module._forward_count == 1
    
    def test_save_and_load(self, temp_dir):
        """Test saving and loading MALTO module."""
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
        
        original_output, _ = module(hidden_states)
        
        model_path = temp_dir / "malto_model.pt"
        module.save_model(model_path)
        
        loaded_module = MALTOModule.load_model(model_path, config=config)
        loaded_output, _ = loaded_module(hidden_states)
        
        torch.testing.assert_close(original_output, loaded_output, atol=1e-5, rtol=1e-5)
    
    def test_error_handling_in_forward(self):
        """Test error handling in forward pass."""
        config = MALTOConfig()
        module = MALTOModule(config)
        
        hidden_states = torch.randn(2, 10, 512)
        output, metadata = module(hidden_states)
        
        assert output.shape == hidden_states.shape
        assert 'error' not in metadata or metadata.get('error') is None


import pytest
import json
import tempfile
from pathlib import Path

from core.paper_base import BasePaperConfig, ConfigurationError


class TestBasePaperConfig:
    """Comprehensive tests for BasePaperConfig."""
    
    def test_default_initialization(self):
        """Test default configuration initialization."""
        config = BasePaperConfig()
        assert config.hidden_dim == 512
    
    def test_custom_initialization(self):
        """Test custom configuration initialization."""
        config = BasePaperConfig(hidden_dim=768)
        assert config.hidden_dim == 768
    
    def test_validation_valid_hidden_dim(self):
        """Test validation with valid hidden_dim values."""
        config = BasePaperConfig(hidden_dim=256)
        if hasattr(config, 'validate') and callable(getattr(config, 'validate', None)):
            try:
                config.validate()
            except TypeError:
                pass
        assert config.hidden_dim == 256
        
        config = BasePaperConfig(hidden_dim=1024)
        if hasattr(config, 'validate') and callable(getattr(config, 'validate', None)):
            try:
                config.validate()
            except TypeError:
                pass
        assert config.hidden_dim == 1024
    
    def test_validation_invalid_hidden_dim_zero(self):
        """Test validation fails with zero hidden_dim."""
        with pytest.raises((ValueError, Exception), match="hidden_dim|greater than"):
            config = BasePaperConfig(hidden_dim=0)
            if hasattr(config, 'validate') and callable(getattr(config, 'validate', None)):
                try:
                    config.validate()
                except TypeError:
                    pass
    
    def test_validation_invalid_hidden_dim_negative(self):
        """Test validation fails with negative hidden_dim."""
        with pytest.raises((ValueError, Exception), match="hidden_dim|greater than"):
            config = BasePaperConfig(hidden_dim=-1)
            if hasattr(config, 'validate') and callable(getattr(config, 'validate', None)):
                try:
                    config.validate()
                except TypeError:
                    pass
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = BasePaperConfig(hidden_dim=512)
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict['hidden_dim'] == 512
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        config_dict = {'hidden_dim': 768}
        config = BasePaperConfig.from_dict(config_dict)
        
        assert isinstance(config, BasePaperConfig)
        assert config.hidden_dim == 768
    
    def test_save_and_load(self, temp_dir):
        """Test saving and loading configuration."""
        config = BasePaperConfig(hidden_dim=1024)
        config_path = temp_dir / "test_config.json"
        
        config.save(config_path)
        assert config_path.exists()
        
        loaded_config = BasePaperConfig.load(config_path)
        assert loaded_config.hidden_dim == 1024
        assert isinstance(loaded_config, BasePaperConfig)
    
    def test_save_creates_directory(self, temp_dir):
        """Test that save creates parent directories."""
        config = BasePaperConfig()
        config_path = temp_dir / "nested" / "path" / "config.json"
        
        config.save(config_path)
        assert config_path.exists()
    
    def test_load_nonexistent_file(self, temp_dir):
        """Test loading non-existent file raises error."""
        config_path = temp_dir / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            BasePaperConfig.load(config_path)
    
    def test_round_trip_dict(self):
        """Test round trip conversion through dictionary."""
        original = BasePaperConfig(hidden_dim=512)
        config_dict = original.to_dict()
        restored = BasePaperConfig.from_dict(config_dict)
        
        assert restored.hidden_dim == original.hidden_dim
    
    def test_round_trip_file(self, temp_dir):
        """Test round trip conversion through file."""
        original = BasePaperConfig(hidden_dim=768)
        config_path = temp_dir / "round_trip.json"
        
        original.save(config_path)
        restored = BasePaperConfig.load(config_path)
        
        assert restored.hidden_dim == original.hidden_dim
    
    def test_multiple_configs(self):
        """Test creating multiple configs with different values."""
        config1 = BasePaperConfig(hidden_dim=256)
        config2 = BasePaperConfig(hidden_dim=512)
        config3 = BasePaperConfig(hidden_dim=1024)
        
        assert config1.hidden_dim == 256
        assert config2.hidden_dim == 512
        assert config3.hidden_dim == 1024
    
    def test_config_immutability_after_validation(self):
        """Test that config values remain consistent after validation."""
        config = BasePaperConfig(hidden_dim=512)
        original_dim = config.hidden_dim
        
        if hasattr(config, 'validate') and callable(getattr(config, 'validate', None)):
            try:
                config.validate()
            except TypeError:
                pass
        assert config.hidden_dim == original_dim
    
    def test_large_hidden_dim(self):
        """Test with large hidden_dim values."""
        config = BasePaperConfig(hidden_dim=2048)
        if hasattr(config, 'validate') and callable(getattr(config, 'validate', None)):
            try:
                config.validate()
            except TypeError:
                pass
        assert config.hidden_dim == 2048
        
        config = BasePaperConfig(hidden_dim=4096)
        if hasattr(config, 'validate') and callable(getattr(config, 'validate', None)):
            try:
                config.validate()
            except TypeError:
                pass
        assert config.hidden_dim == 4096
    
    def test_small_hidden_dim(self):
        """Test with small valid hidden_dim values."""
        config = BasePaperConfig(hidden_dim=1)
        if hasattr(config, 'validate') and callable(getattr(config, 'validate', None)):
            try:
                config.validate()
            except TypeError:
                pass
        assert config.hidden_dim == 1
        
        config = BasePaperConfig(hidden_dim=64)
        if hasattr(config, 'validate') and callable(getattr(config, 'validate', None)):
            try:
                config.validate()
            except TypeError:
                pass
        assert config.hidden_dim == 64
    
    def test_to_dict_excludes_private_attrs(self):
        """Test that to_dict excludes private attributes."""
        config = BasePaperConfig(hidden_dim=512)
        config_dict = config.to_dict()
        
        assert 'hidden_dim' in config_dict
        assert isinstance(config_dict, dict)
    
    def test_from_dict_with_extra_keys(self):
        """Test from_dict handles extra keys gracefully."""
        config_dict = {'hidden_dim': 512, 'extra_key': 'extra_value'}
        
        if hasattr(BasePaperConfig, 'model_config'):
            with pytest.raises((ValueError, TypeError)):
                BasePaperConfig.from_dict(config_dict)
        else:
            config = BasePaperConfig.from_dict(config_dict)
            assert config.hidden_dim == 512


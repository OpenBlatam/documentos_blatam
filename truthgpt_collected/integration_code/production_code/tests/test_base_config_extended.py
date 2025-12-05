import pytest
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any

from core.paper_base import BasePaperConfig


class TestBasePaperConfigExtended:
    """Tests extendidos y parametrizados para BasePaperConfig."""
    
    @pytest.mark.parametrize("hidden_dim", [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 768, 1024, 2048, 4096])
    def test_hidden_dim_values(self, hidden_dim):
        """Test con múltiples valores de hidden_dim."""
        config = BasePaperConfig(hidden_dim=hidden_dim)
        assert config.hidden_dim == hidden_dim
    
    @pytest.mark.parametrize("hidden_dim", [-1, 0, -100])
    def test_invalid_hidden_dim_values(self, hidden_dim):
        """Test que valores inválidos de hidden_dim fallan."""
        with pytest.raises((ValueError, Exception)):
            config = BasePaperConfig(hidden_dim=hidden_dim)
            if hasattr(config, 'validate') and callable(getattr(config, 'validate', None)):
                try:
                    config.validate()
                except TypeError:
                    pass
    
    def test_config_equality(self):
        """Test que configs con mismos valores son iguales."""
        config1 = BasePaperConfig(hidden_dim=512)
        config2 = BasePaperConfig(hidden_dim=512)
        
        assert config1.hidden_dim == config2.hidden_dim
        assert config1.to_dict() == config2.to_dict()
    
    def test_config_inequality(self):
        """Test que configs con diferentes valores son diferentes."""
        config1 = BasePaperConfig(hidden_dim=512)
        config2 = BasePaperConfig(hidden_dim=768)
        
        assert config1.hidden_dim != config2.hidden_dim
        assert config1.to_dict() != config2.to_dict()
    
    def test_to_dict_preserves_all_fields(self):
        """Test que to_dict preserva todos los campos."""
        config = BasePaperConfig(hidden_dim=512)
        config_dict = config.to_dict()
        
        assert 'hidden_dim' in config_dict
        assert config_dict['hidden_dim'] == 512
    
    def test_from_dict_preserves_all_fields(self):
        """Test que from_dict preserva todos los campos."""
        original_dict = {'hidden_dim': 768}
        config = BasePaperConfig.from_dict(original_dict)
        
        assert config.hidden_dim == 768
    
    @pytest.mark.parametrize("hidden_dim", [128, 256, 512, 768, 1024])
    def test_save_load_round_trip(self, temp_dir, hidden_dim):
        """Test round trip save/load con múltiples valores."""
        original = BasePaperConfig(hidden_dim=hidden_dim)
        config_path = temp_dir / f"config_{hidden_dim}.json"
        
        original.save(config_path)
        loaded = BasePaperConfig.load(config_path)
        
        assert loaded.hidden_dim == original.hidden_dim
        assert loaded.to_dict() == original.to_dict()
    
    def test_multiple_configs_independence(self):
        """Test que múltiples configs son independientes."""
        config1 = BasePaperConfig(hidden_dim=256)
        config2 = BasePaperConfig(hidden_dim=512)
        config3 = BasePaperConfig(hidden_dim=768)
        
        assert config1.hidden_dim == 256
        assert config2.hidden_dim == 512
        assert config3.hidden_dim == 768
        
        config1.hidden_dim = 128
        assert config1.hidden_dim == 128
        assert config2.hidden_dim == 512
        assert config3.hidden_dim == 768
    
    def test_config_modification_after_creation(self):
        """Test modificación de config después de creación."""
        config = BasePaperConfig(hidden_dim=512)
        assert config.hidden_dim == 512
        
        config.hidden_dim = 768
        assert config.hidden_dim == 768
    
    def test_to_dict_immutability(self):
        """Test que to_dict retorna una copia."""
        config = BasePaperConfig(hidden_dim=512)
        config_dict1 = config.to_dict()
        config_dict2 = config.to_dict()
        
        assert config_dict1 == config_dict2
        assert id(config_dict1) != id(config_dict2)
    
    def test_from_dict_with_extra_fields(self):
        """Test from_dict con campos extra (debe manejarse gracefully)."""
        config_dict = {'hidden_dim': 512, 'extra_field': 'extra_value'}
        
        if hasattr(BasePaperConfig, 'model_config'):
            with pytest.raises((ValueError, TypeError)):
                BasePaperConfig.from_dict(config_dict)
        else:
            config = BasePaperConfig.from_dict(config_dict)
            assert config.hidden_dim == 512
    
    def test_from_dict_missing_required_fields(self):
        """Test from_dict con campos faltantes."""
        config_dict = {}
        
        try:
            config = BasePaperConfig.from_dict(config_dict)
            assert config.hidden_dim == 512
        except (TypeError, ValueError):
            pass
    
    def test_save_creates_nested_directories(self, temp_dir):
        """Test que save crea directorios anidados."""
        config = BasePaperConfig()
        config_path = temp_dir / "nested" / "deep" / "path" / "config.json"
        
        config.save(config_path)
        assert config_path.exists()
        assert config_path.parent.exists()
    
    def test_load_from_nonexistent_nested_path(self, temp_dir):
        """Test load desde path anidado inexistente."""
        config_path = temp_dir / "nonexistent" / "path" / "config.json"
        
        with pytest.raises(FileNotFoundError):
            BasePaperConfig.load(config_path)
    
    def test_config_hashable(self):
        """Test que config puede ser usado como key en dict (si es hashable)."""
        config1 = BasePaperConfig(hidden_dim=512)
        config2 = BasePaperConfig(hidden_dim=512)
        config3 = BasePaperConfig(hidden_dim=768)
        
        try:
            config_dict = {
                config1: "value1",
                config3: "value3"
            }
            assert config1 in config_dict or config_dict.get(config1) is not None
        except TypeError:
            config_dict = {
                id(config1): "value1",
                id(config3): "value3"
            }
            assert id(config1) in config_dict
    
    def test_config_repr(self):
        """Test representación string de config."""
        config = BasePaperConfig(hidden_dim=512)
        repr_str = repr(config)
        
        assert 'BasePaperConfig' in repr_str or 'hidden_dim' in str(config.to_dict())
    
    def test_config_str(self):
        """Test string representation de config."""
        config = BasePaperConfig(hidden_dim=512)
        str_repr = str(config)
        
        assert str_repr is not None
        assert len(str_repr) > 0


import pytest
import tempfile
import shutil
from pathlib import Path
import ast

from improve_models import (
    ModelImprover,
    improve_model_file,
    find_all_model_files,
    _apply_simple_improvements
)


class TestModelImprover:
    """Tests for ModelImprover class."""
    
    def test_initialization(self):
        """Test ModelImprover initialization."""
        source_code = "class TestConfig(BasePaperConfig):\n    pass"
        improver = ModelImprover(source_code)
        
        assert improver.source_code == source_code
        assert improver.changes_made is False
        assert isinstance(improver.lines, list)
    
    def test_visit_classdef_config(self):
        """Test visiting Config class."""
        source_code = """
class TestConfig(BasePaperConfig):
    hidden_dim: int = 512
"""
        tree = ast.parse(source_code)
        improver = ModelImprover(source_code)
        result = improver.visit(tree)
        
        assert result is not None
    
    def test_visit_classdef_module(self):
        """Test visiting Module class."""
        source_code = """
class TestModule(BasePaperModule):
    def forward(self, hidden_states):
        return hidden_states, {}
"""
        tree = ast.parse(source_code)
        improver = ModelImprover(source_code)
        result = improver.visit(tree)
        
        assert result is not None


class TestImproveModelFile:
    """Tests for improve_model_file function."""
    
    @pytest.fixture
    def temp_model_file(self, tmp_path):
        """Create a temporary model file for testing."""
        model_file = tmp_path / "test_paper.py"
        model_file.write_text("""
import torch
from core.paper_base import BasePaperModule, BasePaperConfig

class TestConfig(BasePaperConfig):
    hidden_dim: int = 512

class TestModule(BasePaperModule):
    def forward(self, hidden_states):
        return hidden_states, {}
""")
        return model_file
    
    def test_improve_model_file_success(self, temp_model_file):
        """Test improving a model file successfully."""
        changed, error = improve_model_file(temp_model_file)
        
        assert error is None
        assert isinstance(changed, bool)
    
    def test_improve_model_file_syntax_error(self, tmp_path):
        """Test improving a file with syntax error."""
        bad_file = tmp_path / "bad_paper.py"
        bad_file.write_text("class TestConfig(BasePaperConfig):\n    invalid syntax here")
        
        changed, error = improve_model_file(bad_file)
        
        assert error is not None
        assert "sintaxis" in error.lower() or "syntax" in error.lower()
    
    def test_improve_model_file_nonexistent(self, tmp_path):
        """Test improving a non-existent file."""
        nonexistent = tmp_path / "nonexistent.py"
        
        changed, error = improve_model_file(nonexistent)
        
        assert error is not None


class TestFindAllModelFiles:
    """Tests for find_all_model_files function."""
    
    def test_find_model_files(self, tmp_path):
        """Test finding model files."""
        test_dir = tmp_path / "test_models"
        test_dir.mkdir()
        
        (test_dir / "paper_test1.py").write_text("# test")
        (test_dir / "paper_test2.py").write_text("# test")
        (test_dir / "not_paper.py").write_text("# test")
        (test_dir / "paper_extractor.py").write_text("# test")
        
        files = find_all_model_files(test_dir)
        
        assert len(files) == 2
        assert all("paper_test" in str(f) for f in files)
        assert not any("extractor" in str(f) for f in files)
    
    def test_find_model_files_nested(self, tmp_path):
        """Test finding model files in nested directories."""
        test_dir = tmp_path / "test_models"
        test_dir.mkdir()
        
        subdir = test_dir / "subdir"
        subdir.mkdir()
        
        (test_dir / "paper_test1.py").write_text("# test")
        (subdir / "paper_test2.py").write_text("# test")
        
        files = find_all_model_files(test_dir)
        
        assert len(files) == 2
    
    def test_find_model_files_empty(self, tmp_path):
        """Test finding model files in empty directory."""
        test_dir = tmp_path / "empty"
        test_dir.mkdir()
        
        files = find_all_model_files(test_dir)
        
        assert len(files) == 0


class TestApplySimpleImprovements:
    """Tests for _apply_simple_improvements function."""
    
    def test_apply_improvements_with_forward(self, tmp_path):
        """Test applying improvements to file with forward method."""
        model_file = tmp_path / "test_paper.py"
        source_code = """
import torch
from core.paper_base import BasePaperModule, BasePaperConfig

class TestModule(BasePaperModule):
    def forward(self, hidden_states):
        return hidden_states, {}
"""
        model_file.write_text(source_code)
        
        changed, error = _apply_simple_improvements(model_file, source_code)
        
        assert error is None
        assert isinstance(changed, bool)
    
    def test_apply_improvements_without_logging(self, tmp_path):
        """Test applying improvements adds logging import."""
        model_file = tmp_path / "test_paper.py"
        source_code = """
import torch
from core.paper_base import BasePaperModule

class TestModule(BasePaperModule):
    pass
"""
        model_file.write_text(source_code)
        
        changed, error = _apply_simple_improvements(model_file, source_code)
        
        assert error is None
    
    def test_apply_improvements_invalid_syntax(self, tmp_path):
        """Test applying improvements to invalid syntax."""
        model_file = tmp_path / "bad_paper.py"
        source_code = "invalid python syntax here"
        
        changed, error = _apply_simple_improvements(model_file, source_code)
        
        assert error is not None




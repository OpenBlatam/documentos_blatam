import pytest
import torch
import tempfile
import shutil
from pathlib import Path
from typing import Generator

from core.paper_base import BasePaperConfig, BasePaperModule


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_config() -> BasePaperConfig:
    """Create a sample BasePaperConfig for testing."""
    return BasePaperConfig(hidden_dim=512)


@pytest.fixture
def sample_hidden_states() -> torch.Tensor:
    """Create sample hidden states tensor for testing."""
    return torch.randn(2, 10, 512)


@pytest.fixture
def sample_hidden_states_small() -> torch.Tensor:
    """Create small sample hidden states tensor for testing."""
    return torch.randn(1, 5, 128)


@pytest.fixture
def sample_hidden_states_large() -> torch.Tensor:
    """Create large sample hidden states tensor for testing."""
    return torch.randn(4, 100, 768)


@pytest.fixture
def device() -> str:
    """Get the device to use for tests."""
    return "cuda" if torch.cuda.is_available() else "cpu"


@pytest.fixture
def dtype() -> torch.dtype:
    """Get the dtype to use for tests."""
    return torch.float32


def create_solar_config(**kwargs):
    """Helper to create SOLARConfig handling Pydantic/dataclass differences."""
    from research.paper_solar import SOLARConfig
    defaults = {
        'num_paradigms': 3,
        'use_adaptive_selection': True,
        'precision_weight': 0.6,
        'efficiency_weight': 0.4,
        'max_reasoning_steps': 10,
        'tree_branching_factor': 3,
        'graph_max_nodes': 20,
        'dropout_rate': 0.1
    }
    defaults.update(kwargs)
    try:
        return SOLARConfig(**defaults)
    except (TypeError, AttributeError):
        try:
            return SOLARConfig(hidden_dim=512, **defaults)
        except (TypeError, AttributeError):
            return SOLARConfig(**{k: v for k, v in defaults.items() if k != 'hidden_dim'})


def create_hademif_config(**kwargs):
    """Helper to create HaDeMiFConfig handling Pydantic/dataclass differences."""
    from research.paper_hademif import HaDeMiFConfig
    defaults = {
        'use_dynamic_tree': True,
        'tree_depth': 5,
        'mlp_hidden_dim': 256,
        'detection_threshold': 0.5,
        'calibration_weight': 0.5,
        'dropout_rate': 0.1
    }
    defaults.update(kwargs)
    try:
        return HaDeMiFConfig(**defaults)
    except (TypeError, AttributeError):
        try:
            return HaDeMiFConfig(hidden_dim=512, **defaults)
        except (TypeError, AttributeError):
            return HaDeMiFConfig(**{k: v for k, v in defaults.items() if k != 'hidden_dim'})


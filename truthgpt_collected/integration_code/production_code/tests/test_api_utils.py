#!/usr/bin/env python3
"""
Tests for API Utils
===================

Tests for validation and utility functions.
"""

import pytest
import torch
from fastapi import HTTPException

from api.api_utils import (
    validate_episode_data,
    validate_query_data,
    validate_items_data,
    validate_k_value,
    validate_priority,
    validate_similarity_threshold,
    validate_tensor_shape,
    format_response,
    paginate_results,
)


class TestValidateEpisodeData:
    """Tests for episode data validation."""
    
    def test_valid_episode(self):
        """Test valid episode data."""
        episode = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = validate_episode_data(episode)
        assert isinstance(result, torch.Tensor)
        assert result.dim() == 1
        assert result.size(0) == 5
    
    def test_empty_episode(self):
        """Test empty episode raises error."""
        with pytest.raises(HTTPException) as exc_info:
            validate_episode_data([])
        assert exc_info.value.status_code == 400
    
    def test_invalid_episode_type(self):
        """Test invalid episode type raises error."""
        with pytest.raises(HTTPException):
            validate_episode_data("not a list")
    
    def test_episode_with_nan(self):
        """Test episode with NaN raises error."""
        import math
        with pytest.raises(HTTPException) as exc_info:
            validate_episode_data([1.0, 2.0, math.nan, 4.0])
        assert exc_info.value.status_code == 400


class TestValidateQueryData:
    """Tests for query data validation."""
    
    def test_valid_query(self):
        """Test valid query data."""
        query = [1.0, 2.0, 3.0]
        result = validate_query_data(query)
        assert isinstance(result, torch.Tensor)
        assert result.dim() == 1
    
    def test_empty_query(self):
        """Test empty query raises error."""
        with pytest.raises(HTTPException) as exc_info:
            validate_query_data([])
        assert exc_info.value.status_code == 400


class TestValidateItemsData:
    """Tests for items data validation."""
    
    def test_valid_items_3d(self):
        """Test valid 3D items data."""
        items = [[[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]]
        result = validate_items_data(items)
        assert isinstance(result, torch.Tensor)
        assert result.dim() == 3
    
    def test_empty_items(self):
        """Test empty items raises error."""
        with pytest.raises(HTTPException) as exc_info:
            validate_items_data([])
        assert exc_info.value.status_code == 400
    
    def test_invalid_dimensions(self):
        """Test invalid dimensions raises error."""
        items = [1.0, 2.0, 3.0]  # 1D instead of 3D
        with pytest.raises(HTTPException) as exc_info:
            validate_items_data(items)
        assert exc_info.value.status_code == 400


class TestValidateKValue:
    """Tests for k value validation."""
    
    def test_valid_k(self):
        """Test valid k value."""
        assert validate_k_value(10) == 10
        assert validate_k_value(None) == 10  # default
    
    def test_k_too_large(self):
        """Test k value too large raises error."""
        with pytest.raises(HTTPException) as exc_info:
            validate_k_value(2000)
        assert exc_info.value.status_code == 400
    
    def test_k_too_small(self):
        """Test k value too small raises error."""
        with pytest.raises(HTTPException) as exc_info:
            validate_k_value(0)
        assert exc_info.value.status_code == 400


class TestValidatePriority:
    """Tests for priority validation."""
    
    def test_valid_priority(self):
        """Test valid priority."""
        assert validate_priority(5.0) == 5.0
        assert validate_priority(None) == 1.0  # default
    
    def test_priority_out_of_range(self):
        """Test priority out of range raises error."""
        with pytest.raises(HTTPException) as exc_info:
            validate_priority(15.0)
        assert exc_info.value.status_code == 400


class TestValidateSimilarityThreshold:
    """Tests for similarity threshold validation."""
    
    def test_valid_threshold(self):
        """Test valid threshold."""
        assert validate_similarity_threshold(0.85) == 0.85
        assert validate_similarity_threshold(None) == 0.85  # default
    
    def test_threshold_out_of_range(self):
        """Test threshold out of range raises error."""
        with pytest.raises(HTTPException) as exc_info:
            validate_similarity_threshold(1.5)
        assert exc_info.value.status_code == 400


class TestFormatResponse:
    """Tests for response formatting."""
    
    def test_format_response_basic(self):
        """Test basic response formatting."""
        data = {"key": "value"}
        response = format_response(data)
        assert response["success"] is True
        assert response["data"] == data
        assert "timestamp" in response
    
    def test_format_response_with_metadata(self):
        """Test response formatting with metadata."""
        data = {"key": "value"}
        metadata = {"count": 10}
        response = format_response(data, metadata)
        assert response["metadata"] == metadata


class TestPaginateResults:
    """Tests for result pagination."""
    
    def test_paginate_results(self):
        """Test result pagination."""
        results = list(range(100))
        paginated = paginate_results(results, page=1, page_size=10)
        assert len(paginated["items"]) == 10
        assert paginated["pagination"]["total"] == 100
        assert paginated["pagination"]["pages"] == 10
    
    def test_paginate_results_last_page(self):
        """Test pagination on last page."""
        results = list(range(25))
        paginated = paginate_results(results, page=3, page_size=10)
        assert len(paginated["items"]) == 5
        assert paginated["pagination"]["page"] == 3


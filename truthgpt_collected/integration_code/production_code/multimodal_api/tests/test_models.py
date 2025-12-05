#!/usr/bin/env python3
"""
Tests para modelos de la API Multimodal.
"""

import pytest
from datetime import datetime
from multimodal_api.models import (
    GenerationRequest,
    GenerationResponse,
    Modality,
    GenerationType,
    TaskStatus
)


def test_generation_request():
    """Test de GenerationRequest."""
    request = GenerationRequest(
        modality=Modality.VIDEO,
        prompt="A beautiful sunset",
        parameters={"duration": 5},
        priority=5
    )
    
    assert request.modality == Modality.VIDEO
    assert request.prompt == "A beautiful sunset"
    assert request.priority == 5
    assert request.parameters["duration"] == 5


def test_generation_request_validation():
    """Test de validación de GenerationRequest."""
    # Prompt vacío debería fallar
    with pytest.raises(ValueError):
        GenerationRequest(
            modality=Modality.VIDEO,
            prompt="",
            parameters={}
        )
    
    # Prioridad fuera de rango debería fallar
    with pytest.raises(ValueError):
        GenerationRequest(
            modality=Modality.VIDEO,
            prompt="Test",
            priority=11  # Fuera de rango
        )


def test_generation_response():
    """Test de GenerationResponse."""
    response = GenerationResponse(
        task_id="test-id",
        status=TaskStatus.PENDING,
        created_at=datetime.now()
    )
    
    assert response.task_id == "test-id"
    assert response.status == TaskStatus.PENDING
    assert response.progress is None or response.progress == 0.0



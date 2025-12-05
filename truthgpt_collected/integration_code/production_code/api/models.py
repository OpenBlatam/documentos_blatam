#!/usr/bin/env python3
"""
API Response Models
===================

Pydantic models for API responses to ensure type safety and OpenAPI accuracy.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response model with common fields."""
    success: bool = Field(True, description="Whether the operation was successful")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")


class MemoryStoreResponse(BaseResponse):
    """Response model for memory store operation."""
    episodes_count: int = Field(..., description="Total number of episodes in memory")
    stored: bool = Field(..., description="Whether the episode was stored successfully")


class MemoryRetrieveResponse(BaseResponse):
    """Response model for memory retrieve operation."""
    retrieved: List[List[float]] = Field(..., description="Retrieved episodes")
    weights: List[float] = Field(..., description="Retrieval weights")
    count: int = Field(..., description="Number of episodes retrieved")


class MemoryStatsResponse(BaseResponse):
    """Response model for memory statistics."""
    stats: Dict[str, Any] = Field(..., description="Memory statistics")


class RedundancyProcessResponse(BaseResponse):
    """Response model for redundancy processing."""
    unique_items: List[List[List[float]]] = Field(..., description="Unique items after processing")
    stats: Dict[str, Any] = Field(..., description="Processing statistics")
    reduction_rate: float = Field(..., description="Reduction rate percentage")


class RedundancyStatsResponse(BaseResponse):
    """Response model for redundancy statistics."""
    stats: Dict[str, Any] = Field(..., description="Redundancy statistics")


class PipelineProcessResponse(BaseResponse):
    """Response model for pipeline processing."""
    output: List[List[List[float]]] = Field(..., description="Processed output")
    metadata: Dict[str, Any] = Field(..., description="Processing metadata")
    output_shape: List[int] = Field(..., description="Output tensor shape")


class PipelineStatsResponse(BaseResponse):
    """Response model for pipeline statistics."""
    stats: Dict[str, Any] = Field(..., description="Pipeline statistics")


class ChatResponse(BaseResponse):
    """Response model for chat operations."""
    response: str = Field(..., description="Chat response")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ConfigResponse(BaseResponse):
    """Response model for configuration operations."""
    config: Dict[str, Any] = Field(..., description="Configuration data")
    module: Optional[str] = Field(None, description="Module name if specific config requested")


class ConfigUpdateResponse(BaseResponse):
    """Response model for configuration updates."""
    message: str = Field(..., description="Update confirmation message")
    module: str = Field(..., description="Module that was updated")


class MonitorStatusResponse(BaseResponse):
    """Response model for monitor status."""
    status: Dict[str, Any] = Field(..., description="System status")


class MonitorHealthResponse(BaseResponse):
    """Response model for monitor health."""
    health: Dict[str, Any] = Field(..., description="Health check results")


class MonitorMetricsResponse(BaseResponse):
    """Response model for monitor metrics."""
    metrics: Dict[str, Any] = Field(..., description="System metrics")


class ErrorResponse(BaseResponse):
    """Response model for errors."""
    success: bool = Field(False, description="Operation failed")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    path: Optional[str] = Field(None, description="Request path that caused the error")


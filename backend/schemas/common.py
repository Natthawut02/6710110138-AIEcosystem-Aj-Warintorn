"""
Common and generic Pydantic response models.
"""

from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """Standard unified response wrapper for all API endpoints."""
    success: bool = Field(True, description="Indicates whether the operation succeeded")
    message: str = Field("Operation completed successfully", description="User-friendly status message")
    data: Optional[T] = Field(None, description="Response payload data")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    success: bool = Field(False, description="Always false for error responses")
    error_code: str = Field("INTERNAL_SERVER_ERROR", description="Machine-readable error code")
    message: str = Field(..., description="Detailed description of the error")
    details: Optional[Any] = Field(None, description="Additional context or validation error details")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated collection response wrapper."""
    success: bool = Field(True, description="Indicates whether the operation succeeded")
    total: int = Field(..., description="Total number of items available")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(20, description="Number of items per page")
    items: List[T] = Field(default_factory=list, description="List of items for current page")

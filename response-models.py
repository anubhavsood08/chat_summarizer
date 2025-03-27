from typing import List, Optional, Generic, TypeVar, Dict, Any
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar('T')

class PaginatedParams(BaseModel):
    """Parameters for pagination."""
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    limit: int = Field(10, ge=1, le=100, description="Number of items per page")
    
class PageInfo(BaseModel):
    """Information about the current page."""
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Number of items per page")
    total: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

class PaginatedResponse(GenericModel, Generic[T]):
    """Generic paginated response model."""
    data: List[T] = Field(..., description="List of items")
    page_info: PageInfo = Field(..., description="Pagination information")

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class SuccessResponse(BaseModel):
    """Success response model."""
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")

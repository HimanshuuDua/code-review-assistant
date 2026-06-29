from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CommentType(str, Enum):
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    SUGGESTION = "suggestion"
    REFACTOR = "refactor"
    QUESTION = "question"


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReviewComment(BaseModel):
    type: CommentType
    severity: Severity
    message: str
    line: int | None = None


class ReviewRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=8000)
    language: str = Field(default="python", max_length=50)
    context: str | None = Field(default=None, max_length=2000)
    user_name: str | None = Field(default=None, max_length=120)


class ModelReviewResult(BaseModel):
    model_name: str
    comments: list[ReviewComment]
    raw_response: str
    latency_ms: float | None = None


class CompareReviewResponse(BaseModel):
    base_model: ModelReviewResult
    finetuned_model: ModelReviewResult


class HealthResponse(BaseModel):
    status: str
    inference_mode: str
    base_model_id: str
    finetuned_model_id: str
    storage_enabled: bool


class ReviewHistoryItem(BaseModel):
    id: str
    user_name: str
    client_ip: str | None
    language: str
    code_preview: str
    code: str
    context: str | None
    issue_types: list[str]
    finetuned_comment_count: int
    base_comments_json: str
    finetuned_comments_json: str
    inference_mode: str
    created_at: datetime


class ReviewStats(BaseModel):
    total_reviews: int
    unique_users: int


class ReviewHistoryResponse(BaseModel):
    items: list[ReviewHistoryItem]
    total: int
    limit: int
    offset: int

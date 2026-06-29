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

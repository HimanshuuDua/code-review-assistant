from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.schemas import CompareReviewResponse, HealthResponse, ModelReviewResult, ReviewRequest
from backend.services.reviewer import reviewer_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    title="Code Review Assistant API",
    description="Compare base Mistral 7B vs fine-tuned code review model",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        inference_mode=settings.inference_mode,
        base_model_id=settings.base_model_id,
        finetuned_model_id=settings.finetuned_model_id,
    )


@app.post("/api/review", response_model=CompareReviewResponse)
async def review_both(request: ReviewRequest) -> CompareReviewResponse:
    base, finetuned = await reviewer_service.compare(request)
    return CompareReviewResponse(base_model=base, finetuned_model=finetuned)


@app.post("/api/review/base", response_model=ModelReviewResult)
async def review_base(request: ReviewRequest) -> ModelReviewResult:
    return await reviewer_service.review(request, use_finetuned=False)


@app.post("/api/review/finetuned", response_model=ModelReviewResult)
async def review_finetuned(request: ReviewRequest) -> ModelReviewResult:
    return await reviewer_service.review(request, use_finetuned=True)


if __name__ == "__main__":
    import uvicorn

    from backend.config import settings

    uvicorn.run("backend.main:app", host=settings.api_host, port=settings.api_port, reload=True)

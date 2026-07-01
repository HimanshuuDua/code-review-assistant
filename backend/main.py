from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_session, init_db
from backend.middleware.rate_limit import add_rate_limit
from backend.routers.auth import oauth_enabled, router as auth_router
from backend.schemas import (
    CompareReviewResponse,
    HealthResponse,
    ModelReviewResult,
    ReviewHistoryItem,
    ReviewHistoryResponse,
    ReviewRequest,
    ReviewStats,
)
from backend.services.reviewer import reviewer_service
from backend.services.storage import export_reviews_csv, get_review, get_stats, list_reviews, save_review


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def verify_admin(x_admin_key: str = Header(..., alias="X-Admin-Key")) -> None:
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.storage_enabled:
        if "sqlite" in settings.database_url:
            db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
            if db_path and not db_path.startswith(":"):
                from pathlib import Path

                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        await init_db()
    yield


app = FastAPI(
    title="Code Review Assistant API",
    description="Compare base Mistral 7B vs fine-tuned/specialized code review models",
    version="1.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
add_rate_limit(app)
app.include_router(auth_router)


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        inference_mode=settings.inference_mode,
        base_model_id=settings.base_model_id,
        finetuned_model_id=settings.finetuned_model_id,
        storage_enabled=settings.storage_enabled,
        oauth_enabled=oauth_enabled(),
    )


@app.post("/api/review", response_model=CompareReviewResponse)
async def review_both(
    request: ReviewRequest,
    http_request: Request,
    session: AsyncSession = Depends(get_session),
) -> CompareReviewResponse:
    base, finetuned = await reviewer_service.compare(request)
    response = CompareReviewResponse(base_model=base, finetuned_model=finetuned)
    if settings.storage_enabled:
        await save_review(session, request, response, _client_ip(http_request))
    return response


@app.post("/api/review/base", response_model=ModelReviewResult)
async def review_base(request: ReviewRequest) -> ModelReviewResult:
    return await reviewer_service.review(request, use_finetuned=False)


@app.post("/api/review/finetuned", response_model=ModelReviewResult)
async def review_finetuned(request: ReviewRequest) -> ModelReviewResult:
    return await reviewer_service.review(request, use_finetuned=True)


@app.get("/api/admin/reviews", response_model=ReviewHistoryResponse, dependencies=[Depends(verify_admin)])
async def admin_list_reviews(
    session: AsyncSession = Depends(get_session),
    limit: int = 50,
    offset: int = 0,
) -> ReviewHistoryResponse:
    items = await list_reviews(session, limit=limit, offset=offset)
    stats = await get_stats(session)
    return ReviewHistoryResponse(items=items, total=stats.total_reviews, limit=limit, offset=offset)


@app.get("/api/admin/reviews/export", dependencies=[Depends(verify_admin)])
async def admin_export_reviews(session: AsyncSession = Depends(get_session)) -> PlainTextResponse:
    csv_data = await export_reviews_csv(session)
    return PlainTextResponse(csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=reviews.csv"})


@app.get("/api/admin/reviews/{review_id}", response_model=ReviewHistoryItem, dependencies=[Depends(verify_admin)])
async def admin_get_review(review_id: str, session: AsyncSession = Depends(get_session)) -> ReviewHistoryItem:
    item = await get_review(session, review_id)
    if not item:
        raise HTTPException(status_code=404, detail="Review not found")
    return item


@app.get("/api/admin/stats", response_model=ReviewStats, dependencies=[Depends(verify_admin)])
async def admin_stats(session: AsyncSession = Depends(get_session)) -> ReviewStats:
    return await get_stats(session)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host=settings.api_host, port=settings.api_port, reload=True)

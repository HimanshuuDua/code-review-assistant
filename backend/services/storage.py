import json

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.db_models import ReviewRecord
from backend.schemas import CompareReviewResponse, ReviewHistoryItem, ReviewRequest, ReviewStats


async def save_review(
    session: AsyncSession,
    request: ReviewRequest,
    result: CompareReviewResponse,
    client_ip: str | None,
) -> ReviewRecord:
    record = ReviewRecord(
        user_name=request.user_name or "anonymous",
        client_ip=client_ip,
        code=request.code,
        language=request.language,
        context=request.context,
        base_comments_json=json.dumps([c.model_dump() for c in result.base_model.comments]),
        finetuned_comments_json=json.dumps([c.model_dump() for c in result.finetuned_model.comments]),
        inference_mode=settings.inference_mode,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


def _to_history_item(record: ReviewRecord) -> ReviewHistoryItem:
    finetuned = json.loads(record.finetuned_comments_json)
    issue_types = sorted({c.get("type", "unknown") for c in finetuned})
    return ReviewHistoryItem(
        id=record.id,
        user_name=record.user_name,
        client_ip=record.client_ip,
        language=record.language,
        code_preview=record.code[:200] + ("..." if len(record.code) > 200 else ""),
        code=record.code,
        context=record.context,
        issue_types=issue_types,
        finetuned_comment_count=len(finetuned),
        base_comments_json=record.base_comments_json,
        finetuned_comments_json=record.finetuned_comments_json,
        inference_mode=record.inference_mode,
        created_at=record.created_at,
    )


async def list_reviews(session: AsyncSession, limit: int = 50, offset: int = 0) -> list[ReviewHistoryItem]:
    result = await session.execute(
        select(ReviewRecord).order_by(desc(ReviewRecord.created_at)).limit(limit).offset(offset)
    )
    return [_to_history_item(r) for r in result.scalars().all()]


async def get_review(session: AsyncSession, review_id: str) -> ReviewHistoryItem | None:
    record = await session.get(ReviewRecord, review_id)
    return _to_history_item(record) if record else None


async def get_stats(session: AsyncSession) -> ReviewStats:
    total = await session.scalar(select(func.count()).select_from(ReviewRecord)) or 0
    users = await session.scalar(select(func.count(func.distinct(ReviewRecord.user_name)))) or 0
    return ReviewStats(total_reviews=total, unique_users=users)

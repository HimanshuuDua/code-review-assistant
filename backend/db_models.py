import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ReviewRecord(Base):
    __tablename__ = "review_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_name: Mapped[str] = mapped_column(String(120), default="anonymous")
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    code: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(50), default="python")
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_comments_json: Mapped[str] = mapped_column(Text, default="[]")
    finetuned_comments_json: Mapped[str] = mapped_column(Text, default="[]")
    inference_mode: Mapped[str] = mapped_column(String(32), default="demo")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

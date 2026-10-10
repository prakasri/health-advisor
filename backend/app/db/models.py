"""SQLAlchemy models for DM-001. The migration in migrations/versions mirrors these exactly."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Assessment(Base):
    __tablename__ = "assessment"
    __table_args__ = (
        CheckConstraint("hba1c BETWEEN 3.0 AND 20.0", name="assessment_hba1c_range"),
        CheckConstraint(
            "classification IN ('normal','prediabetes','diabetes')", name="assessment_class"
        ),
        CheckConstraint("status IN ('processing','complete','failed')", name="assessment_status"),
        Index("assessment_class_created_idx", "classification", "created_at"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    created_at: Mapped[datetime] = _created_at()
    hba1c: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    eligible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    classification: Mapped[str | None] = mapped_column(Text)
    urgent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    bmi: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    calorie_target: Mapped[int | None] = mapped_column(Integer)
    inputs: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="processing")

    report: Mapped["Report | None"] = relationship(back_populates="assessment")


class Report(Base):
    __tablename__ = "report"
    __table_args__ = (CheckConstraint("kind IN ('full','referral')", name="report_kind"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    safety_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    used_fallback: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    rules_version: Mapped[str] = mapped_column(Text, nullable=False)
    model_id: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _created_at()

    assessment: Mapped[Assessment] = relationship(back_populates="report")


class ShareLink(Base):
    __tablename__ = "share_link"
    __table_args__ = (Index("share_link_report_idx", "report_id"),)

    token: Mapped[str] = mapped_column(Text, primary_key=True)
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("report.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = _created_at()
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (CheckConstraint("length(comment) <= 500", name="feedback_comment_length"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("report.id", ondelete="CASCADE"), nullable=False
    )
    helpful: Mapped[bool] = mapped_column(Boolean, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _created_at()

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from unsa_audit.core.database import Base


class RouteModel(Base):
    __tablename__ = "routes"

    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    order: Mapped[int] = mapped_column(Integer, unique=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    hours: Mapped[int] = mapped_column(Integer)
    prerequisite_code: Mapped[str | None] = mapped_column(ForeignKey("routes.code"))


class ModuleModel(Base):
    __tablename__ = "modules"
    __table_args__ = (UniqueConstraint("route_code", "slug"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    route_code: Mapped[str] = mapped_column(ForeignKey("routes.code"), index=True)
    slug: Mapped[str] = mapped_column(String(80))
    order: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(160))
    minutes: Mapped[int] = mapped_column(Integer)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    is_final: Mapped[bool] = mapped_column(Boolean, default=False)
    planned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    lesson_md: Mapped[str] = mapped_column(Text)
    exercise_kind: Mapped[str | None] = mapped_column(String(30))
    exercise_spec: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    exercise_generator: Mapped[str | None] = mapped_column(String(60))
    exercise_params: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    pass_score: Mapped[int] = mapped_column(Integer, default=70)


class EnrollmentModel(Base):
    __tablename__ = "enrollments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    route_code: Mapped[str] = mapped_column(ForeignKey("routes.code"), primary_key=True)
    status: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ModuleProgressModel(Base):
    __tablename__ = "module_progress"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    module_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), primary_key=True
    )
    best_score: Mapped[int] = mapped_column(Integer)
    completed: Mapped[bool] = mapped_column(Boolean)
    minutes_credited: Mapped[int] = mapped_column(Integer)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ExerciseAttemptModel(Base):
    __tablename__ = "exercise_attempts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    module_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), index=True
    )
    answer: Mapped[dict[str, Any]] = mapped_column(JSONB)
    score: Mapped[int] = mapped_column(Integer)
    passed: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

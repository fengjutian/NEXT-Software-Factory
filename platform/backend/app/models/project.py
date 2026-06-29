"""Project model — the top-level entity representing a user's generation request."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    requirement: Mapped[str] = mapped_column(Text, nullable=False)
    template: Mapped[str | None] = mapped_column(String(32), nullable=True)
    language: Mapped[str] = mapped_column(String(8), default="zh")
    status: Mapped[str] = mapped_column(
        String(32), default="pending",
        comment="pending|analyzing|generating_backend|generating_frontend|testing|done|failed"
    )
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    requirement_spec: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    constraints: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    design_spec: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    stats: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    agent_runs: Mapped[list["AgentRun"]] = relationship(
        "AgentRun", back_populates="project", cascade="all, delete-orphan"
    )
    generated_files: Mapped[list["GeneratedFile"]] = relationship(
        "GeneratedFile", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, summary='{self.summary}')>"

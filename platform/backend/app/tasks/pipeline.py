"""Celery tasks for async pipeline execution.

In production, long-running pipelines run via Celery instead of FastAPI BackgroundTasks.
This module provides the Celery task definitions.
"""

import asyncio
import logging

from celery import Celery

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Celery app
celery_app = Celery(
    "ai_factory",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.project_timeout_seconds,
    worker_max_tasks_per_child=50,
)


@celery_app.task(bind=True, name="run_pipeline")
def run_pipeline_task(self, project_id: str) -> dict:
    """Execute the full pipeline for a project.

    This runs in a Celery worker process. It creates its own event loop
    and database session since Celery tasks are synchronous.
    """
    logger.info(f"Starting pipeline for project {project_id}")

    async def _run():
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        from app.models.project import Project
        from app.services.orchestrator import Orchestrator

        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with session_factory() as db:
            project = await db.get(Project, project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")

            orchestrator = Orchestrator(db)
            project = await orchestrator.run_full_pipeline(project)

        await engine.dispose()

        return {
            "project_id": project_id,
            "status": str(project.status) if project else "unknown",
        }

    return asyncio.run(_run())


@celery_app.task(bind=True, name="run_requirement_only")
def run_requirement_only_task(self, project_id: str) -> dict:
    """Run only the Requirement Agent for quick preview."""
    logger.info(f"Running requirement-only for project {project_id}")

    async def _run():
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        from app.models.project import Project
        from app.services.orchestrator import Orchestrator

        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with session_factory() as db:
            project = await db.get(Project, project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")

            orchestrator = Orchestrator(db)
            project = await orchestrator.run_requirement_only(project)

        await engine.dispose()

        return {
            "project_id": project_id,
            "status": str(project.status) if project else "unknown",
        }

    return asyncio.run(_run())

"""Project API — create, list, get, delete projects."""

import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.project import Project
from app.schemas.agent import NaturalLanguageSpec
from app.agents.requirement_agent import RequirementAgent
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.post("", status_code=201)
async def create_project(
    body: NaturalLanguageSpec,
    db: AsyncSession = Depends(get_db),
):
    """Create a new project and start the pipeline.

    Creates the project record, then immediately runs the Requirement Agent.
    On success, the RequirementSpec is saved and the project advances to the next step.
    """
    # Create project record
    project = Project(
        requirement=body.requirement,
        template=body.template,
        language=body.language,
        constraints=body.constraints.model_dump(),
        design_spec=body.design_spec,
        status="analyzing",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    project_id = str(project.id)

    # ── Run Requirement Agent ──
    agent = RequirementAgent(ws_manager=ws_manager)
    input_spec = {
        "requirement": body.requirement,
        "template": body.template,
        "language": body.language,
        "constraints": body.constraints.model_dump(),
    }

    await ws_manager.send_step_started(project_id, "requirement", "需求分析")

    try:
        start = time.monotonic()
        result = await agent.run(project_id, input_spec)
        elapsed = (time.monotonic() - start) * 1000

        # Save the RequirementSpec
        project.requirement_spec = result
        project.summary = result.get("summary", "")
        project.status = "generating_backend"  # Ready for next step

        await db.commit()

        await ws_manager.send_step_completed(
            project_id, "requirement", "需求分析",
            duration_ms=elapsed,
            summary=f"识别 {len(result.get('entities', []))} 个实体, "
                    f"{len(result.get('api_endpoints', []))} 个端点, "
                    f"{len(result.get('pages', []))} 个页面",
        )

    except Exception as e:
        # Mark project as failed but keep the record
        project.status = "failed"
        project.error_message = str(e)
        await db.commit()

        await ws_manager.send_step_failed(
            project_id, "requirement", "需求分析", str(e), retryable=True,
        )
        raise HTTPException(status_code=500, detail=f"需求分析失败: {str(e)}")

    return {
        "success": True,
        "data": {
            "id": project_id,
            "requirement": body.requirement,
            "status": project.status,
            "summary": project.summary,
            "created_at": project.created_at.isoformat(),
            "progress": {
                "current_step": "requirement",
                "steps": [
                    {"name": "requirement", "label": "需求分析", "status": "completed"},
                    {"name": "backend", "label": "生成后端", "status": "pending"},
                    {"name": "frontend", "label": "生成前端", "status": "pending"},
                    {"name": "test", "label": "运行测试", "status": "pending"},
                ],
            },
        },
    }


@router.get("")
async def list_projects(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List projects with pagination."""
    from sqlalchemy import select, func

    query = select(Project)
    if search:
        query = query.where(
            (Project.requirement.ilike(f"%{search}%"))
            | (Project.summary.ilike(f"%{search}%"))
        )
    query = query.order_by(Project.created_at.desc())

    # Count total
    count_query = select(func.count()).select_from(Project)
    if search:
        count_query = count_query.where(
            (Project.requirement.ilike(f"%{search}%"))
            | (Project.summary.ilike(f"%{search}%"))
        )
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    rows = (await db.execute(query)).scalars().all()

    return {
        "success": True,
        "data": {
            "items": [
                {
                    "id": str(p.id),
                    "requirement": p.requirement[:100],
                    "summary": p.summary,
                    "status": p.status,
                    "created_at": p.created_at.isoformat(),
                }
                for p in rows
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/{project_id}")
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get project detail."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    return {
        "success": True,
        "data": {
            "id": str(project.id),
            "requirement": project.requirement,
            "summary": project.summary,
            "status": project.status,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "progress": {
                "current_step": _status_to_step(project.status),
                "steps": [
                    {"name": "requirement", "label": "需求分析", "status": _step_status(project.status, "analyzing")},
                    {"name": "backend", "label": "生成后端", "status": _step_status(project.status, "generating_backend")},
                    {"name": "frontend", "label": "生成前端", "status": _step_status(project.status, "generating_frontend")},
                    {"name": "test", "label": "运行测试", "status": _step_status(project.status, "testing")},
                ],
            },
            "stats": project.stats,
            "error_message": project.error_message,
        },
    }


@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a project and its associated files."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    await db.delete(project)
    await db.commit()

    return {"success": True, "data": None}


# ── Helpers ──

_STATUS_ORDER = {
    "pending": 0,
    "analyzing": 1,
    "generating_backend": 2,
    "generating_frontend": 3,
    "testing": 4,
    "done": 5,
    "failed": -1,
}

_STEP_MAP = {
    "pending": "requirement",
    "analyzing": "requirement",
    "generating_backend": "backend",
    "generating_frontend": "frontend",
    "testing": "test",
    "done": "done",
}

_STEP_THRESHOLD = {
    "requirement": "analyzing",
    "backend": "generating_backend",
    "frontend": "generating_frontend",
    "test": "testing",
}


def _status_to_step(status: str) -> str | None:
    return _STEP_MAP.get(status)


def _step_status(project_status: str, step_threshold: str) -> str:
    """Determine step status based on project status."""
    if project_status == "failed":
        return "failed"
    if project_status == "done":
        return "completed"

    current_order = _STATUS_ORDER.get(project_status, 0)
    step_order = _STATUS_ORDER.get(step_threshold, 0)

    if step_order < current_order:
        return "completed"
    elif step_order == current_order:
        return "running"
    else:
        return "pending"

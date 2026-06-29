"""Project API — create, list, get, delete projects.

Pipeline is executed asynchronously via background tasks.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.project import Project
from app.schemas.agent import NaturalLanguageSpec
from app.services.orchestrator import Orchestrator

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.post("", status_code=201)
async def create_project(
    body: NaturalLanguageSpec,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a new project and start the pipeline in the background."""
    project = Project(
        requirement=body.requirement,
        template=body.template,
        language=body.language,
        constraints=body.constraints.model_dump(),
        design_spec=body.design_spec,
        status="pending",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    # Run pipeline in background
    orchestrator = Orchestrator(db)
    background_tasks.add_task(orchestrator.run_full_pipeline, project)

    return {
        "success": True,
        "data": {
            "id": str(project.id),
            "requirement": body.requirement,
            "status": project.status,
            "created_at": project.created_at.isoformat(),
            "progress": {
                "current_step": None,
                "steps": [
                    {"name": "requirement", "label": "需求分析", "status": "pending"},
                    {"name": "backend", "label": "生成后端", "status": "pending"},
                    {"name": "frontend", "label": "生成前端", "status": "pending"},
                    {"name": "review", "label": "代码质检", "status": "pending"},
                    {"name": "test", "label": "生成测试", "status": "pending"},
                    {"name": "documentation", "label": "生成文档", "status": "pending"},
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
    """List projects with pagination and optional search."""
    query = select(Project)
    if search:
        query = query.where(
            (Project.requirement.ilike(f"%{search}%"))
            | (Project.summary.ilike(f"%{search}%"))
        )
    query = query.order_by(Project.created_at.desc())

    count_query = select(func.count()).select_from(Project)
    if search:
        count_query = count_query.where(
            (Project.requirement.ilike(f"%{search}%"))
            | (Project.summary.ilike(f"%{search}%"))
        )
    total = (await db.execute(count_query)).scalar() or 0

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
    """Get project detail with progress and stats."""
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
                "steps": _build_step_list(project.status),
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
    """Delete a project and all associated files/agent runs."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    await db.delete(project)
    await db.commit()

    return {"success": True, "data": None}


@router.get("/{project_id}/spec")
async def get_project_spec(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get the RequirementSpec for a project."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    if not project.requirement_spec:
        raise HTTPException(status_code=404, detail="需求分析尚未完成")

    return {
        "success": True,
        "data": {
            "requirement_spec": project.requirement_spec,
        },
    }


@router.put("/{project_id}/spec")
async def update_project_spec(
    project_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Update RequirementSpec after user review."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    project.requirement_spec = body.get("requirement_spec", {})
    project.summary = project.requirement_spec.get("summary", project.summary)
    await db.commit()

    return {"success": True, "data": {"updated": True}}


@router.post("/{project_id}/continue")
async def continue_pipeline(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Continue pipeline from Backend Agent after user confirms Spec."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    status_ok = project.status in ("analyzing", "generating_backend")
    if not status_ok:
        raise HTTPException(status_code=400, detail="项目状态不允许继续")

    if not project.requirement_spec:
        raise HTTPException(status_code=400, detail="需求分析尚未完成")

    orchestrator = Orchestrator(db)
    background_tasks.add_task(orchestrator.continue_from_backend, project)

    return {"success": True, "data": {"status": "continuing"}}


# ── File endpoints ──

from app.models.generated_file import GeneratedFile


@router.get("/{project_id}/files")
async def get_file_tree(
    project_id: UUID,
    type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get the file tree for a project."""
    query = select(GeneratedFile).where(GeneratedFile.project_id == project_id)
    if type:
        query = query.where(GeneratedFile.file_type == type)
    query = query.order_by(GeneratedFile.file_path)

    rows = (await db.execute(query)).scalars().all()

    tree = _build_file_tree(rows)

    return {
        "success": True,
        "data": {"tree": tree},
    }


@router.get("/{project_id}/files/{file_path:path}")
async def get_file_content(
    project_id: UUID,
    file_path: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the content of a specific generated file."""
    from urllib.parse import unquote

    file_path = unquote(file_path)

    query = select(GeneratedFile).where(
        GeneratedFile.project_id == project_id,
        GeneratedFile.file_path == file_path,
    )
    row = (await db.execute(query)).scalar_one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="文件不存在")

    language = _guess_language(row.file_path)

    return {
        "success": True,
        "data": {
            "path": row.file_path,
            "content": row.content,
            "language": language,
            "size": row.size_bytes or 0,
            "file_type": row.file_type,
        },
    }


@router.get("/{project_id}/download")
async def download_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Download project as a ZIP file."""
    from fastapi.responses import StreamingResponse
    import zipfile
    import io

    query = select(GeneratedFile).where(GeneratedFile.project_id == project_id)
    rows = (await db.execute(query)).scalars().all()

    if not rows:
        raise HTTPException(status_code=404, detail="项目没有生成文件")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for row in rows:
            zf.writestr(row.file_path, row.content or "")

    buf.seek(0)
    project = await db.get(Project, project_id)
    filename = f"{project.summary or 'project'}.zip" if project else "project.zip"

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Helpers ──

def _status_to_step(status: str) -> str | None:
    mapping = {
        "pending": None,
        "analyzing": "requirement",
        "generating_backend": "backend",
        "generating_frontend": "frontend",
        "testing": "test",
        "done": "done",
        "failed": None,
    }
    return mapping.get(status)


def _build_step_list(status: str) -> list[dict]:
    """Build step list with statuses based on project status."""
    step_order = ["requirement", "backend", "frontend", "review", "test", "documentation"]
    step_labels = {
        "requirement": "需求分析",
        "backend": "生成后端",
        "frontend": "生成前端",
        "review": "代码质检",
        "test": "生成测试",
        "documentation": "生成文档",
    }
    thresholds = {
        "requirement": "analyzing",
        "backend": "generating_backend",
        "frontend": "generating_frontend",
        "review": "reviewing",
        "test": "testing",
        "documentation": "generating_documentation",
    }

    if status == "failed":
        return [
            {"name": s, "label": step_labels[s], "status": "skipped"}
            for s in step_order
        ]
    if status == "done":
        return [
            {"name": s, "label": step_labels[s], "status": "completed"}
            for s in step_order
        ]

    steps = []
    current_found = False
    for step in step_order:
        threshold = thresholds[step]
        if status == threshold:
            steps.append({"name": step, "label": step_labels[step], "status": "running"})
            current_found = True
        elif current_found:
            steps.append({"name": step, "label": step_labels[step], "status": "pending"})
        elif _status_index(status) >= _status_index(threshold):
            steps.append({"name": step, "label": step_labels[step], "status": "completed"})
        else:
            steps.append({"name": step, "label": step_labels[step], "status": "pending"})
    return steps


def _status_index(status: str) -> int:
    order = ["pending", "analyzing", "generating_backend", "generating_frontend", "testing", "done"]
    try:
        return order.index(status)
    except ValueError:
        return 0


def _build_file_tree(files: list[GeneratedFile]) -> list[dict]:
    """Build a nested file tree from flat file list."""
    tree: dict[str, dict] = {}

    for f in files:
        parts = f.file_path.split("/")
        current = tree
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                # File
                current[part] = {
                    "name": part,
                    "type": "file",
                    "size": f.size_bytes,
                    "file_type": f.file_type,
                }
            else:
                # Directory
                if part not in current:
                    current[part] = {"name": part, "type": "directory", "children": {}}
                current = current[part].setdefault("children", {})

    return _dict_to_list(tree)


def _dict_to_list(d: dict) -> list[dict]:
    """Convert dict-based tree to list-based tree."""
    result = []
    for name, node in d.items():
        if node["type"] == "directory":
            node["children"] = _dict_to_list(node.get("children", {}))
        result.append(node)
    return sorted(result, key=lambda x: (0 if x["type"] == "directory" else 1, x["name"]))


def _guess_language(file_path: str) -> str:
    """Guess programming language from file extension."""
    ext_map = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".sql": "sql",
        ".html": "html",
        ".css": "css",
        ".dockerfile": "dockerfile",
        ".txt": "text",
    }
    import os
    ext = os.path.splitext(file_path)[1].lower()
    return ext_map.get(ext, "text")

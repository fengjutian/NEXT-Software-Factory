"""Orchestrator — runs the full pipeline: Requirement → Backend → Frontend → Review → Test → Docs.

Creates its own database sessions to safely run in FastAPI background tasks.
"""

import time
import logging
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from app.core.config import get_settings
from app.models.project import Project
from app.models.agent_run import AgentRun
from app.models.generated_file import GeneratedFile
from app.agents.requirement_agent import RequirementAgent
from app.agents.backend_agent import BackendAgent
from app.agents.frontend_agent import FrontendAgent
from app.agents.review_agent import ReviewAgent
from app.agents.test_agent import TestAgent
from app.agents.documentation_agent import DocumentationAgent
from app.websocket.manager import ws_manager

logger = logging.getLogger(__name__)


class Orchestrator:
    """Pipeline orchestrator — runs agents sequentially, each in its own DB session."""

    def __init__(self):
        settings = get_settings()
        self._engine = create_async_engine(settings.database_url)
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

    async def _session(self):
        return self._session_factory()

    async def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    async def run_full_pipeline(self, project_id: str) -> dict:
        """Run all 6 pipeline steps. Returns final status dict."""
        async with await self._session() as db:
            project = await db.get(Project, project_id)
            if not project:
                return {"status": "not_found"}

        result = {"project_id": project_id, "status": "done"}

        try:
            project = await self._run_requirement_agent(project_id)
            if not project or project.status == "failed":
                result["status"] = "failed"
                return result

            project = await self._run_backend_agent(project_id)
            if not project or project.status == "failed":
                result["status"] = "failed"
                return result

            project = await self._run_frontend_agent(project_id)
            if not project or project.status == "failed":
                result["status"] = "failed"
                return result

            project = await self._run_review_agent(project_id)
            # Review failure doesn't stop pipeline

            project = await self._run_test_agent(project_id)
            if not project or project.status == "failed":
                result["status"] = "failed"
                return result

            project = await self._run_documentation_agent(project_id)

            # Mark done
            async with await self._session() as db:
                project = await db.get(Project, project_id)
                if project:
                    project.status = "done"
                    await db.commit()

            await ws_manager.send_pipeline_completed(project_id, project.stats if project else {})
            return result

        except Exception as e:
            logger.exception(f"Pipeline failed for {project_id}")
            async with await self._session() as db:
                project = await db.get(Project, project_id)
                if project:
                    project.status = "failed"
                    project.error_message = str(e)
                    await db.commit()
            await ws_manager.send_pipeline_failed(project_id, "unknown", str(e))
            return {"project_id": project_id, "status": "failed"}

    # ── Individual step methods ──

    async def _run_requirement_agent(self, project_id: str) -> Project | None:
        async with await self._session() as db:
            project = await db.get(Project, project_id)
            if not project:
                return None

            run = AgentRun(project_id=project.id, agent_name="requirement", status="running", started_at=await self._now())
            db.add(run)
            await db.commit()

        await ws_manager.send_step_started(project_id, "requirement", "需求分析")

        async with await self._session() as db:
            project = await db.get(Project, project_id)
            agent = RequirementAgent(ws_manager=ws_manager)
            input_spec = {
                "requirement": project.requirement,
                "template": project.template,
                "language": project.language,
                "constraints": project.constraints or {},
            }

            try:
                start = time.monotonic()
                result = await agent.run(project_id, input_spec)
                elapsed = (time.monotonic() - start) * 1000

                project.requirement_spec = result
                project.summary = result.get("summary", "")
                project.status = "generating_backend"

                run = (await db.execute(select(AgentRun).where(AgentRun.project_id == project.id, AgentRun.agent_name == "requirement").order_by(AgentRun.created_at.desc()).limit(1))).scalar_one()
                run.output_result = result
                run.status = "done"
                run.finished_at = await self._now()
                await db.commit()

                await ws_manager.send_step_completed(project_id, "requirement", "需求分析", duration_ms=elapsed,
                    summary=f"识别 {len(result.get('entities', []))} 个实体, {len(result.get('api_endpoints', []))} 个端点")
                return project

            except Exception as e:
                run = (await db.execute(select(AgentRun).where(AgentRun.project_id == project.id, AgentRun.agent_name == "requirement").order_by(AgentRun.created_at.desc()).limit(1))).scalar_one()
                run.status = "failed"
                run.error_message = str(e)
                run.finished_at = await self._now()
                project.status = "failed"
                project.error_message = str(e)
                await db.commit()
                await ws_manager.send_step_failed(project_id, "requirement", "需求分析", str(e), retryable=True)
                return project

    async def _run_backend_agent(self, project_id: str) -> Project | None:
        return await self._run_code_agent(project_id, "backend", "生成后端代码", BackendAgent, "generating_backend", "generating_frontend")

    async def _run_frontend_agent(self, project_id: str) -> Project | None:
        return await self._run_code_agent(project_id, "frontend", "生成前端代码", FrontendAgent, "generating_frontend", "generating_frontend")

    async def _run_code_agent(self, project_id: str, name: str, label: str, agent_cls, current_status: str, next_status: str) -> Project | None:
        async with await self._session() as db:
            project = await db.get(Project, project_id)
            if not project:
                return None

            run = AgentRun(project_id=project.id, agent_name=name, status="running", started_at=await self._now())
            db.add(run)
            await db.commit()

        await ws_manager.send_step_started(project_id, name, label)

        async with await self._session() as db:
            project = await db.get(Project, project_id)
            agent = agent_cls(ws_manager=ws_manager)
            input_spec = self._build_input_spec(project, name)

            try:
                start = time.monotonic()
                result = await agent.run(project_id, input_spec)
                elapsed = (time.monotonic() - start) * 1000

                files = result.get("files", [])
                total_lines = 0
                for f in files:
                    content = f.get("content", "")
                    total_lines += len(content.split("\n"))
                    db.add(GeneratedFile(project_id=project.id, file_path=f.get("path", ""), content=content, file_type=f.get("type", "unknown"), size_bytes=len(content.encode("utf-8"))))

                prev_stats = project.stats or {}
                project.stats = {
                    "total_files": prev_stats.get("total_files", 0) + len(files),
                    "backend_files": prev_stats.get("backend_files", 0) + (len(files) if name == "backend" else 0),
                    "frontend_files": prev_stats.get("frontend_files", 0) + (len(files) if name == "frontend" else 0),
                    "test_files": prev_stats.get("test_files", 0),
                    "total_lines": prev_stats.get("total_lines", 0) + total_lines,
                }
                project.status = next_status

                run = (await db.execute(select(AgentRun).where(AgentRun.project_id == project.id, AgentRun.agent_name == name).order_by(AgentRun.created_at.desc()).limit(1))).scalar_one()
                run.output_result = result
                run.status = "done"
                run.finished_at = await self._now()
                await db.commit()

                await ws_manager.send_step_completed(project_id, name, label, duration_ms=elapsed, summary=f"生成 {len(files)} 个文件, {total_lines} 行代码")
                return project

            except Exception as e:
                run = (await db.execute(select(AgentRun).where(AgentRun.project_id == project.id, AgentRun.agent_name == name).order_by(AgentRun.created_at.desc()).limit(1))).scalar_one()
                run.status = "failed"
                run.error_message = str(e)
                run.finished_at = await self._now()
                project.status = "failed"
                project.error_message = str(e)
                await db.commit()
                await ws_manager.send_step_failed(project_id, name, label, str(e), retryable=True)
                return project

    def _build_input_spec(self, project: Project, name: str) -> dict:
        if name == "backend":
            return {
                "entities": (project.requirement_spec or {}).get("entities", []),
                "api_endpoints": (project.requirement_spec or {}).get("api_endpoints", []),
                "manifest": (project.requirement_spec or {}).get("manifest", {}),
                "constraints": project.constraints or {},
            }
        if name == "frontend":
            return {
                "openapi_spec": {},
                "pages": (project.requirement_spec or {}).get("pages", []),
                "backend_manifest": {},
                "design_spec": project.design_spec or {},
            }
        return {}

    async def _run_review_agent(self, project_id: str) -> Project | None:
        async with await self._session() as db:
            project = await db.get(Project, project_id)
            if not project:
                return None

            run = AgentRun(project_id=project.id, agent_name="review", status="running", started_at=await self._now())
            db.add(run)
            await db.commit()

        await ws_manager.send_step_started(project_id, "review", "代码质检")

        async with await self._session() as db:
            project = await db.get(Project, project_id)
            files_query = select(GeneratedFile).where(GeneratedFile.project_id == project.id).order_by(GeneratedFile.file_path)
            generated_files = (await db.execute(files_query)).scalars().all()

            agent = ReviewAgent(ws_manager=ws_manager)
            input_spec = {
                "files": [{"path": f.file_path, "content": f.content, "type": f.file_type} for f in generated_files],
                "entities": (project.requirement_spec or {}).get("entities", []),
                "api_endpoints": (project.requirement_spec or {}).get("api_endpoints", []),
            }

            try:
                start = time.monotonic()
                result = await agent.run(project_id, input_spec)
                elapsed = (time.monotonic() - start) * 1000

                report = result.get("review_report", {})
                violations = report.get("violations", [])
                criticals = [v for v in violations if v.get("severity") == "CRITICAL"]

                run = (await db.execute(select(AgentRun).where(AgentRun.project_id == project.id, AgentRun.agent_name == "review").order_by(AgentRun.created_at.desc()).limit(1))).scalar_one()
                run.output_result = result
                run.status = "done"
                run.finished_at = await self._now()
                await db.commit()

                await ws_manager.send_step_completed(project_id, "review", "代码质检", duration_ms=elapsed,
                    summary=f"{'✅ 通过' if not criticals else f'⚠️ {len(criticals)} 个严重问题'}")
                return project

            except Exception as e:
                run = (await db.execute(select(AgentRun).where(AgentRun.project_id == project.id, AgentRun.agent_name == "review").order_by(AgentRun.created_at.desc()).limit(1))).scalar_one()
                run.status = "failed"
                run.error_message = str(e)
                run.finished_at = await self._now()
                await db.commit()
                return project

    async def _run_test_agent(self, project_id: str) -> Project | None:
        async with await self._session() as db:
            project = await db.get(Project, project_id)
            if not project:
                return None

            run = AgentRun(project_id=project.id, agent_name="test", status="running", started_at=await self._now())
            db.add(run)
            await db.commit()

        await ws_manager.send_step_started(project_id, "test", "生成测试")

        async with await self._session() as db:
            project = await db.get(Project, project_id)

            backend_run = (await db.execute(select(AgentRun).where(AgentRun.project_id == project.id, AgentRun.agent_name == "backend").order_by(AgentRun.created_at.desc()).limit(1))).scalar_one_or_none()
            frontend_run = (await db.execute(select(AgentRun).where(AgentRun.project_id == project.id, AgentRun.agent_name == "frontend").order_by(AgentRun.created_at.desc()).limit(1))).scalar_one_or_none()

            agent = TestAgent(ws_manager=ws_manager)
            input_spec = {
                "entities": (project.requirement_spec or {}).get("entities", []),
                "api_endpoints": (project.requirement_spec or {}).get("api_endpoints", []),
                "pages": (project.requirement_spec or {}).get("pages", []),
                "backend_manifest": backend_run.output_result.get("backend_manifest", {}) if backend_run and backend_run.output_result else {},
                "frontend_manifest": frontend_run.output_result.get("frontend_manifest", {}) if frontend_run and frontend_run.output_result else {},
                "backend_files": [],
                "frontend_files": [],
            }

            try:
                start = time.monotonic()
                result = await agent.run(project_id, input_spec)
                elapsed = (time.monotonic() - start) * 1000

                files = result.get("files", [])
                total_lines = 0
                for f in files:
                    content = f.get("content", "")
                    total_lines += len(content.split("\n"))
                    db.add(GeneratedFile(project_id=project.id, file_path=f.get("path", ""), content=content, file_type="test", size_bytes=len(content.encode("utf-8"))))

                report = result.get("report", {})
                prev_stats = project.stats or {}
                project.stats = {**prev_stats,
                    "total_files": prev_stats.get("total_files", 0) + len(files),
                    "test_files": len(files),
                    "total_lines": prev_stats.get("total_lines", 0) + total_lines,
                    "test_coverage": report.get("coverage_percent", 0),
                    "tests_passed": report.get("passed", 0),
                    "tests_failed": report.get("failed", 0),
                }

                run = (await db.execute(select(AgentRun).where(AgentRun.project_id == project.id, AgentRun.agent_name == "test").order_by(AgentRun.created_at.desc()).limit(1))).scalar_one()
                run.output_result = result
                run.status = "done"
                run.finished_at = await self._now()
                await db.commit()

                await ws_manager.send_step_completed(project_id, "test", "生成测试", duration_ms=elapsed,
                    summary=f"{report.get('passed', 0)}/{report.get('total_tests', 0)} 测试通过")
                return project

            except Exception as e:
                run = (await db.execute(select(AgentRun).where(AgentRun.project_id == project.id, AgentRun.agent_name == "test").order_by(AgentRun.created_at.desc()).limit(1))).scalar_one()
                run.status = "failed"
                run.error_message = str(e)
                run.finished_at = await self._now()
                project.status = "failed"
                project.error_message = str(e)
                await db.commit()
                await ws_manager.send_step_failed(project_id, "test", "生成测试", str(e), retryable=True)
                return project

    async def _run_documentation_agent(self, project_id: str) -> Project | None:
        async with await self._session() as db:
            project = await db.get(Project, project_id)
            if not project:
                return None

            run = AgentRun(project_id=project.id, agent_name="documentation", status="running", started_at=await self._now())
            db.add(run)
            await db.commit()

        await ws_manager.send_step_started(project_id, "documentation", "生成文档")

        async with await self._session() as db:
            project = await db.get(Project, project_id)

            backend_run = (await db.execute(select(AgentRun).where(AgentRun.project_id == project.id, AgentRun.agent_name == "backend").order_by(AgentRun.created_at.desc()).limit(1))).scalar_one_or_none()
            frontend_run = (await db.execute(select(AgentRun).where(AgentRun.project_id == project.id, AgentRun.agent_name == "frontend").order_by(AgentRun.created_at.desc()).limit(1))).scalar_one_or_none()
            test_run = (await db.execute(select(AgentRun).where(AgentRun.project_id == project.id, AgentRun.agent_name == "test").order_by(AgentRun.created_at.desc()).limit(1))).scalar_one_or_none()

            agent = DocumentationAgent(ws_manager=ws_manager)
            input_spec = {
                "project_name": (project.requirement_spec or {}).get("project_name", ""),
                "summary": project.summary or "",
                "entities": (project.requirement_spec or {}).get("entities", []),
                "endpoints": (project.requirement_spec or {}).get("api_endpoints", []),
                "pages": (project.requirement_spec or {}).get("pages", []),
                "openapi_spec": backend_run.output_result.get("artifacts", {}).get("openapi_spec", {}) if backend_run and backend_run.output_result else {},
                "db_schema": backend_run.output_result.get("artifacts", {}).get("db_schema", {}) if backend_run and backend_run.output_result else {},
                "route_tree": frontend_run.output_result.get("artifacts", {}).get("route_tree", {}) if frontend_run and frontend_run.output_result else {},
                "test_report": test_run.output_result.get("report", {}) if test_run and test_run.output_result else {},
                "project_stats": project.stats or {},
                "design_spec": project.design_spec or {},
            }

            try:
                start = time.monotonic()
                result = await agent.run(project_id, input_spec)
                elapsed = (time.monotonic() - start) * 1000

                files = result.get("files", [])
                for f in files:
                    db.add(GeneratedFile(project_id=project.id, file_path=f.get("path", ""), content=f.get("content", ""), file_type="doc", size_bytes=len(f.get("content", "").encode("utf-8"))))

                run = (await db.execute(select(AgentRun).where(AgentRun.project_id == project.id, AgentRun.agent_name == "documentation").order_by(AgentRun.created_at.desc()).limit(1))).scalar_one()
                run.output_result = result
                run.status = "done"
                run.finished_at = await self._now()
                await db.commit()

                await ws_manager.send_step_completed(project_id, "documentation", "生成文档", duration_ms=elapsed, summary=f"生成 {len(files)} 份文档")
                return project

            except Exception as e:
                run = (await db.execute(select(AgentRun).where(AgentRun.project_id == project.id, AgentRun.agent_name == "documentation").order_by(AgentRun.created_at.desc()).limit(1))).scalar_one()
                run.status = "failed"
                run.error_message = str(e)
                run.finished_at = await self._now()
                await db.commit()
                return project

    async def run_requirement_only(self, project_id: str) -> Project | None:
        return await self._run_requirement_agent(project_id)

    async def continue_from_backend(self, project_id: str) -> dict:
        """Continue pipeline from Backend Agent (after user confirms Spec)."""
        result = {"project_id": project_id, "status": "done"}
        try:
            project = await self._run_backend_agent(project_id)
            if not project or project.status == "failed":
                return {"project_id": project_id, "status": "failed"}
            project = await self._run_frontend_agent(project_id)
            if not project or project.status == "failed":
                return {"project_id": project_id, "status": "failed"}
            await self._run_review_agent(project_id)
            project = await self._run_test_agent(project_id)
            if not project or project.status == "failed":
                return {"project_id": project_id, "status": "failed"}
            await self._run_documentation_agent(project_id)

            async with await self._session() as db:
                project = await db.get(Project, project_id)
                if project:
                    project.status = "done"
                    await db.commit()
            return result
        except Exception as e:
            logger.exception(f"Continue pipeline failed for {project_id}")
            async with await self._session() as db:
                project = await db.get(Project, project_id)
                if project:
                    project.status = "failed"
                    project.error_message = str(e)
                    await db.commit()
            return {"project_id": project_id, "status": "failed"}

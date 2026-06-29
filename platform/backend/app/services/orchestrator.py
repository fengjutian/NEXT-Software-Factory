"""Orchestrator — runs the full pipeline: Requirement → Backend → (Frontend → Test)."""

import time
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

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
    """Pipeline orchestrator — chains agents and persists results."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_full_pipeline(self, project: Project) -> Project:
        """Execute the complete pipeline for a project.

        Currently implemented: RequirementAgent → BackendAgent.
        Future: → FrontendAgent → TestAgent → DocumentationAgent.
        """
        project_id = str(project.id)

        try:
            # ── Step 1: Requirement Agent ──
            project = await self._run_requirement_agent(project)

            if project.status == "failed":
                return project

            # ── Step 2: Backend Agent ──
            project = await self._run_backend_agent(project)

            if project.status == "failed":
                return project

            # ── Step 3: Frontend Agent ──
            project = await self._run_frontend_agent(project)

            if project.status == "failed":
                return project

            # ── Step 4: Review Agent ──
            project = await self._run_review_agent(project)

            if project.status == "failed":
                return project

            # ── Step 5: Test Agent ──
            project = await self._run_test_agent(project)

            if project.status == "failed":
                return project

            # ── Step 6: Documentation Agent ──
            project = await self._run_documentation_agent(project)

            if project.status == "failed":
                return project

            # ── Final: mark done ──
            project.status = "done"
            await self.db.commit()

            await ws_manager.send_pipeline_completed(
                project_id,
                project.stats or {},
            )

            return project

        except Exception as e:
            logger.exception(f"Pipeline failed for project {project_id}")
            project.status = "failed"
            project.error_message = str(e)
            await self.db.commit()

            await ws_manager.send_pipeline_failed(
                project_id, "unknown", str(e),
            )
            return project

    async def _run_requirement_agent(self, project: Project) -> Project:
        """Run Requirement Agent and persist results."""
        project_id = str(project.id)

        # Create agent run record
        run = AgentRun(
            project_id=project.id,
            agent_name="requirement",
            status="running",
            started_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        )
        self.db.add(run)
        await self.db.commit()

        await ws_manager.send_step_started(project_id, "requirement", "需求分析")

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

            # Persist result
            project.requirement_spec = result
            project.summary = result.get("summary", "")
            project.status = "generating_backend"

            # Update agent run
            run.output_result = result
            run.status = "done"
            run.finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")

            await self.db.commit()

            entities_count = len(result.get("entities", []))
            endpoints_count = len(result.get("api_endpoints", []))
            pages_count = len(result.get("pages", []))

            await ws_manager.send_step_completed(
                project_id, "requirement", "需求分析",
                duration_ms=elapsed,
                summary=f"识别 {entities_count} 个实体, {endpoints_count} 个端点, {pages_count} 个页面",
            )

            return project

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            run.finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            project.status = "failed"
            project.error_message = str(e)
            await self.db.commit()

            await ws_manager.send_step_failed(
                project_id, "requirement", "需求分析", str(e), retryable=True,
            )
            raise

    async def _run_backend_agent(self, project: Project) -> Project:
        """Run Backend Agent and persist generated files."""
        project_id = str(project.id)

        run = AgentRun(
            project_id=project.id,
            agent_name="backend",
            status="running",
            started_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        )
        self.db.add(run)
        await self.db.commit()

        await ws_manager.send_step_started(project_id, "backend", "生成后端代码")

        agent = BackendAgent(ws_manager=ws_manager)
        input_spec = {
            "entities": project.requirement_spec.get("entities", []),
            "api_endpoints": project.requirement_spec.get("api_endpoints", []),
            "manifest": project.requirement_spec.get("manifest", {}),
            "constraints": project.constraints or {},
        }

        try:
            start = time.monotonic()
            result = await agent.run(project_id, input_spec)
            elapsed = (time.monotonic() - start) * 1000

            # Save generated files
            files = result.get("files", [])
            total_lines = 0
            for f in files:
                content = f.get("content", "")
                total_lines += len(content.split("\n"))
                self.db.add(GeneratedFile(
                    project_id=project.id,
                    file_path=f.get("path", ""),
                    content=content,
                    file_type=f.get("type", "unknown"),
                    size_bytes=len(content.encode("utf-8")),
                ))

            # Update project
            project.stats = {
                "total_files": len(files),
                "backend_files": len(files),
                "frontend_files": 0,
                "test_files": 0,
                "total_lines": total_lines,
            }

            # Update agent run
            run.output_result = result
            run.status = "done"
            run.finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")

            # Advance to next step
            project.status = "generating_frontend"

            await self.db.commit()

            await ws_manager.send_step_completed(
                project_id, "backend", "生成后端代码",
                duration_ms=elapsed,
                summary=f"生成 {len(files)} 个文件, {total_lines} 行代码",
            )

            return project

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            run.finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            project.status = "failed"
            project.error_message = str(e)
            await self.db.commit()

            await ws_manager.send_step_failed(
                project_id, "backend", "生成后端代码", str(e), retryable=True,
            )
            raise


    async def _run_frontend_agent(self, project: Project) -> Project:
        """Run Frontend Agent and persist generated files."""
        project_id = str(project.id)

        run = AgentRun(
            project_id=project.id,
            agent_name="frontend",
            status="running",
            started_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        )
        self.db.add(run)
        await self.db.commit()

        await ws_manager.send_step_started(project_id, "frontend", "生成前端代码")

        # Get the backend's OpenAPI spec from the last agent run
        backend_run_query = (
            __import__("sqlalchemy").select(AgentRun)
            .where(AgentRun.project_id == project.id, AgentRun.agent_name == "backend")
            .order_by(AgentRun.created_at.desc())
            .limit(1)
        )
        backend_result = (await self.db.execute(backend_run_query)).scalar_one_or_none()
        openapi_spec = {}
        backend_manifest = {}
        if backend_result and backend_result.output_result:
            openapi_spec = backend_result.output_result.get("artifacts", {}).get("openapi_spec", {})
            backend_manifest = backend_result.output_result.get("backend_manifest", {})

        agent = FrontendAgent(ws_manager=ws_manager)
        input_spec = {
            "openapi_spec": openapi_spec,
            "pages": project.requirement_spec.get("pages", []) if project.requirement_spec else [],
            "backend_manifest": backend_manifest,
            "design_spec": project.design_spec or {},
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
                self.db.add(GeneratedFile(
                    project_id=project.id,
                    file_path=f.get("path", ""),
                    content=content,
                    file_type=f.get("type", "unknown"),
                    size_bytes=len(content.encode("utf-8")),
                ))

            # Update stats (additive with backend stats)
            prev_stats = project.stats or {}
            project.stats = {
                "total_files": prev_stats.get("total_files", 0) + len(files),
                "backend_files": prev_stats.get("backend_files", 0),
                "frontend_files": len(files),
                "test_files": prev_stats.get("test_files", 0),
                "total_lines": prev_stats.get("total_lines", 0) + total_lines,
            }

            run.output_result = result
            run.status = "done"
            run.finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")

            project.status = "testing"

            await self.db.commit()

            await ws_manager.send_step_completed(
                project_id, "frontend", "生成前端代码",
                duration_ms=elapsed,
                summary=f"生成 {len(files)} 个文件, {total_lines} 行代码",
            )

            return project

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            run.finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            project.status = "failed"
            project.error_message = str(e)
            await self.db.commit()

            await ws_manager.send_step_failed(
                project_id, "frontend", "生成前端代码", str(e), retryable=True,
            )
            raise

    async def _run_review_agent(self, project: Project) -> Project:
        """Run Review Agent to check code quality."""
        project_id = str(project.id)

        run = AgentRun(
            project_id=project.id,
            agent_name="review",
            status="running",
            started_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        )
        self.db.add(run)
        await self.db.commit()

        await ws_manager.send_step_started(project_id, "review", "代码质检")

        # Collect all generated files so far
        from sqlalchemy import select as sa_select
        files_query = (
            sa_select(GeneratedFile)
            .where(GeneratedFile.project_id == project.id)
            .order_by(GeneratedFile.file_path)
        )
        generated_files = (await self.db.execute(files_query)).scalars().all()

        agent = ReviewAgent(ws_manager=ws_manager)
        input_spec = {
            "files": [
                {"path": f.file_path, "content": f.content, "type": f.file_type}
                for f in generated_files
            ],
            "entities": project.requirement_spec.get("entities", []) if project.requirement_spec else [],
            "api_endpoints": project.requirement_spec.get("api_endpoints", []) if project.requirement_spec else [],
        }

        try:
            start = time.monotonic()
            result = await agent.run(project_id, input_spec)
            elapsed = (time.monotonic() - start) * 1000

            report = result.get("review_report", {})
            violations = report.get("violations", [])
            criticals = [v for v in violations if v.get("severity") == "CRITICAL"]

            run.output_result = result
            run.status = "done"
            run.finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            await self.db.commit()

            if criticals and report.get("action") == "retry":
                # Log but don't block — MVP: warn and continue
                await ws_manager.send_log(
                    project_id, "review",
                    f"发现 {len(criticals)} 个严重问题，已记录（MVP 模式不阻断流水线）"
                )

            await ws_manager.send_step_completed(
                project_id, "review", "代码质检",
                duration_ms=elapsed,
                summary=f"{'✅ 通过' if not criticals else f'⚠️ {len(criticals)} 个严重问题'}, "
                        f"{len(violations) - len(criticals)} 个警告",
            )

            return project

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            run.finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            # Review failure doesn't fail the pipeline
            await self.db.commit()
            await ws_manager.send_log(project_id, "review", f"质检失败（不阻断）: {str(e)}")
            return project

    async def _run_test_agent(self, project: Project) -> Project:
        """Run Test Agent and persist generated test files + report."""
        project_id = str(project.id)

        run = AgentRun(
            project_id=project.id,
            agent_name="test",
            status="running",
            started_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        )
        self.db.add(run)
        await self.db.commit()

        await ws_manager.send_step_started(project_id, "test", "生成测试")

        # Collect manifests from previous agent runs
        from sqlalchemy import select as sa_select

        backend_run = (await self.db.execute(
            sa_select(AgentRun)
            .where(AgentRun.project_id == project.id, AgentRun.agent_name == "backend")
            .order_by(AgentRun.created_at.desc()).limit(1)
        )).scalar_one_or_none()

        frontend_run = (await self.db.execute(
            sa_select(AgentRun)
            .where(AgentRun.project_id == project.id, AgentRun.agent_name == "frontend")
            .order_by(AgentRun.created_at.desc()).limit(1)
        )).scalar_one_or_none()

        backend_manifest = {}
        frontend_manifest = {}
        backend_files = []
        frontend_files = []

        if backend_run and backend_run.output_result:
            backend_manifest = backend_run.output_result.get("backend_manifest", {})
            backend_files = [f.get("path", "") for f in backend_run.output_result.get("files", [])]
        if frontend_run and frontend_run.output_result:
            frontend_manifest = frontend_run.output_result.get("frontend_manifest", {})
            frontend_files = [f.get("path", "") for f in frontend_run.output_result.get("files", [])]

        agent = TestAgent(ws_manager=ws_manager)
        input_spec = {
            "entities": project.requirement_spec.get("entities", []) if project.requirement_spec else [],
            "api_endpoints": project.requirement_spec.get("api_endpoints", []) if project.requirement_spec else [],
            "pages": project.requirement_spec.get("pages", []) if project.requirement_spec else [],
            "backend_manifest": backend_manifest,
            "frontend_manifest": frontend_manifest,
            "backend_files": backend_files,
            "frontend_files": frontend_files,
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
                self.db.add(GeneratedFile(
                    project_id=project.id,
                    file_path=f.get("path", ""),
                    content=content,
                    file_type=f.get("type", "test"),
                    size_bytes=len(content.encode("utf-8")),
                ))

            # Update stats
            report = result.get("report", {})
            prev_stats = project.stats or {}
            project.stats = {
                "total_files": prev_stats.get("total_files", 0) + len(files),
                "backend_files": prev_stats.get("backend_files", 0),
                "frontend_files": prev_stats.get("frontend_files", 0),
                "test_files": len(files),
                "total_lines": prev_stats.get("total_lines", 0) + total_lines,
                "test_coverage": report.get("coverage_percent", 0),
                "tests_passed": report.get("passed", 0),
                "tests_failed": report.get("failed", 0),
            }

            run.output_result = result
            run.status = "done"
            run.finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")

            # Stay in "testing" — final "done" set by orchestrator after documentation
            project.status = "testing"

            await self.db.commit()

            await ws_manager.send_step_completed(
                project_id, "test", "生成测试",
                duration_ms=elapsed,
                summary=f"{report.get('passed', 0)}/{report.get('total_tests', 0)} 测试通过, "
                        f"覆盖率 {report.get('coverage_percent', 0)}%",
            )

            return project

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            run.finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            project.status = "failed"
            project.error_message = str(e)
            await self.db.commit()

            await ws_manager.send_step_failed(
                project_id, "test", "生成测试", str(e), retryable=True,
            )
            raise

    async def _run_documentation_agent(self, project: Project) -> Project:
        """Run Documentation Agent and persist generated docs."""
        project_id = str(project.id)

        run = AgentRun(
            project_id=project.id,
            agent_name="documentation",
            status="running",
            started_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        )
        self.db.add(run)
        await self.db.commit()

        await ws_manager.send_step_started(project_id, "documentation", "生成文档")

        # Collect all artifacts
        from sqlalchemy import select as sa_select

        backend_run = (await self.db.execute(
            sa_select(AgentRun).where(
                AgentRun.project_id == project.id, AgentRun.agent_name == "backend"
            ).order_by(AgentRun.created_at.desc()).limit(1)
        )).scalar_one_or_none()

        frontend_run = (await self.db.execute(
            sa_select(AgentRun).where(
                AgentRun.project_id == project.id, AgentRun.agent_name == "frontend"
            ).order_by(AgentRun.created_at.desc()).limit(1)
        )).scalar_one_or_none()

        test_run = (await self.db.execute(
            sa_select(AgentRun).where(
                AgentRun.project_id == project.id, AgentRun.agent_name == "test"
            ).order_by(AgentRun.created_at.desc()).limit(1)
        )).scalar_one_or_none()

        openapi_spec = {}
        db_schema = {}
        if backend_run and backend_run.output_result:
            openapi_spec = backend_run.output_result.get("artifacts", {}).get("openapi_spec", {})
            db_schema = backend_run.output_result.get("artifacts", {}).get("db_schema", {})

        route_tree = {}
        if frontend_run and frontend_run.output_result:
            route_tree = frontend_run.output_result.get("artifacts", {}).get("route_tree", {})

        test_report = {}
        if test_run and test_run.output_result:
            test_report = test_run.output_result.get("report", {})

        agent = DocumentationAgent(ws_manager=ws_manager)
        input_spec = {
            "project_name": (project.requirement_spec or {}).get("project_name", ""),
            "summary": project.summary or "",
            "entities": (project.requirement_spec or {}).get("entities", []),
            "endpoints": (project.requirement_spec or {}).get("api_endpoints", []),
            "pages": (project.requirement_spec or {}).get("pages", []),
            "openapi_spec": openapi_spec,
            "db_schema": db_schema,
            "route_tree": route_tree,
            "test_report": test_report,
            "project_stats": project.stats or {},
            "design_spec": project.design_spec or {},
        }

        try:
            start = time.monotonic()
            result = await agent.run(project_id, input_spec)
            elapsed = (time.monotonic() - start) * 1000

            files = result.get("files", [])
            for f in files:
                content = f.get("content", "")
                self.db.add(GeneratedFile(
                    project_id=project.id,
                    file_path=f.get("path", ""),
                    content=content,
                    file_type="doc",
                    size_bytes=len(content.encode("utf-8")),
                ))

            # Update stats
            prev_stats = project.stats or {}
            project.stats = {
                **prev_stats,
                "total_files": prev_stats.get("total_files", 0) + len(files),
            }

            run.output_result = result
            run.status = "done"
            run.finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")

            await self.db.commit()

            await ws_manager.send_step_completed(
                project_id, "documentation", "生成文档",
                duration_ms=elapsed,
                summary=f"生成 {len(files)} 份文档",
            )

            return project

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            run.finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            project.status = "failed"
            project.error_message = str(e)
            await self.db.commit()

            await ws_manager.send_step_failed(
                project_id, "documentation", "生成文档", str(e), retryable=True,
            )
            raise

    async def run_requirement_only(self, project: Project) -> Project:
        """Run only the Requirement Agent (for quick preview)."""
        return await self._run_requirement_agent(project)

    async def continue_from_backend(self, project: Project) -> Project:
        """Continue pipeline from Backend Agent (after user confirms Spec)."""
        return await self._run_full_post_requirement(project)

    async def _run_full_post_requirement(self, project: Project) -> Project:
        """Run all steps after requirement (Backend → Frontend → Review → Test → Docs)."""
        project_id = str(project.id)

        try:
            project = await self._run_backend_agent(project)
            if project.status == "failed":
                return project

            project = await self._run_frontend_agent(project)
            if project.status == "failed":
                return project

            project = await self._run_review_agent(project)
            if project.status == "failed":
                return project

            project = await self._run_test_agent(project)
            if project.status == "failed":
                return project

            project = await self._run_documentation_agent(project)
            if project.status == "failed":
                return project

            project.status = "done"
            await self.db.commit()
            await ws_manager.send_pipeline_completed(project_id, project.stats or {})
            return project

        except Exception as e:
            logger.exception(f"Pipeline failed for project {project_id}")
            project.status = "failed"
            project.error_message = str(e)
            await self.db.commit()
            await ws_manager.send_pipeline_failed(project_id, "unknown", str(e))
            return project

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


    async def run_requirement_only(self, project: Project) -> Project:
        """Run only the Requirement Agent (for quick preview)."""
        return await self._run_requirement_agent(project)

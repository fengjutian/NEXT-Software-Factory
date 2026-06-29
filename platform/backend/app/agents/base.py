"""BaseAgent — abstract base class for all pipeline agents."""

import json
import asyncio
import random
import time
from abc import ABC, abstractmethod
from typing import Any

from app.core.config import get_settings
from app.agents.llm_client import LLMClient, LLMError


class AgentError(Exception):
    """Base class for agent errors."""

    def __init__(self, message: str, level: str = "E1"):
        self.message = message
        self.level = level  # E0=transient, E1=recoverable, E2=partial, E3=fatal
        super().__init__(message)


class AgentTimeoutError(AgentError):
    """Agent execution timed out."""

    def __init__(self, agent_name: str, timeout: float):
        super().__init__(
            f"{agent_name} 执行超时（>{timeout}s）",
            level="E1",
        )


class BaseAgent(ABC):
    """Abstract base for all agents in the pipeline."""

    agent_name: str = "base"
    timeout_seconds: float = 120.0
    max_retries: int = 2
    temperature: float = 0.1

    def __init__(self, ws_manager=None):
        self.settings = get_settings()
        self.llm = LLMClient()
        self.ws_manager = ws_manager

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        ...

    @abstractmethod
    def build_user_prompt(self, input_spec: dict) -> str:
        """Build the user-facing prompt from the input spec."""
        ...

    @abstractmethod
    def parse_response(self, response_text: str) -> dict:
        """Parse and validate the LLM response into structured output.

        Must return a dict with at least {'status': 'success'|'failed'}.
        """
        ...

    async def run(self, project_id: str, input_spec: dict) -> dict:
        """Execute the agent with retry logic.

        Args:
            project_id: The project UUID for WS notifications.
            input_spec: Agent-specific input JSON.

        Returns:
            Structured output dict matching the agent's output schema.
        """
        system_prompt = self.get_system_prompt()
        user_prompt = self.build_user_prompt(input_spec)

        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 2):  # total attempts = retries + 1
            try:
                await self._notify_log(project_id, f"Agent {self.agent_name} 开始执行 (第 {attempt} 次尝试)...")

                # Call LLM with timeout
                response_text = await asyncio.wait_for(
                    self.llm.complete(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        temperature=self.temperature,
                        max_tokens=self.settings.llm_max_tokens,
                    ),
                    timeout=self.timeout_seconds,
                )

                # Parse the response
                result = self.parse_response(response_text)

                # Validate manifest if present
                manifest_key = f"{self.agent_name}_manifest"
                if manifest_key in result:
                    manifest_errors = self._validate_manifest(result[manifest_key])
                    if manifest_errors and attempt <= self.max_retries:
                        await self._notify_log(
                            project_id,
                            f"Manifest 校验失败: {manifest_errors}，正在重试..."
                        )
                        # Rebuild prompt with error feedback
                        user_prompt = self._add_manifest_feedback(user_prompt, manifest_errors)
                        continue

                await self._notify_log(project_id, f"Agent {self.agent_name} 执行成功")
                return result

            except asyncio.TimeoutError:
                last_error = AgentTimeoutError(self.agent_name, self.timeout_seconds)
                if attempt > self.max_retries:
                    break
                delay = 3.0 * (2 ** (attempt - 1))
                await self._notify_log(
                    project_id,
                    f"超时，{delay:.1f}s 后重试 (第 {attempt} 次)...",
                )
                await asyncio.sleep(delay)

            except LLMError as e:
                last_error = e
                if e.status_code == 429 or (e.status_code and e.status_code >= 500):
                    # Retryable: rate limit or server error
                    if attempt > self.max_retries:
                        break
                    delay = e.retry_after or (2.0 * (2 ** (attempt - 1)))
                    delay *= 1 + random.random() * 0.3  # jitter
                    await self._notify_log(
                        project_id,
                        f"LLM API 错误 ({e.status_code})，{delay:.1f}s 后重试...",
                    )
                    await asyncio.sleep(delay)
                else:
                    # Non-retryable (4xx except 429)
                    raise

            except json.JSONDecodeError as e:
                last_error = e
                if attempt > self.max_retries:
                    break
                await self._notify_log(
                    project_id,
                    f"LLM 返回非 JSON 格式: {str(e)[:100]}，正在重试...",
                )
                user_prompt = self._add_json_feedback(user_prompt)
                await asyncio.sleep(2.0)

        # All retries exhausted
        raise AgentError(
            f"Agent {self.agent_name} 执行失败: {str(last_error)}",
            level="E3",
        )

    def _validate_manifest(self, manifest: dict) -> list[str]:
        """Validate a completion manifest. Returns list of error messages."""
        errors = []

        for field in ("summary", "items", "stats"):
            if field not in manifest:
                errors.append(f"manifest 缺少 '{field}' 字段")

        if "stats" in manifest:
            s = manifest["stats"]
            computed = (
                s.get("completed", 0)
                + s.get("partial", 0)
                + s.get("skipped", 0)
                + s.get("deferred", 0)
            )
            expected = s.get("total_planned", 0)
            if computed != expected:
                errors.append(
                    f"stats 不一致: completed+partial+skipped+deferred={computed} ≠ total_planned={expected}"
                )

        for item in manifest.get("items", []):
            if item.get("status") in ("skipped", "deferred"):
                if not item.get("skip_reason"):
                    errors.append(
                        f"Item {item.get('ref_id')} 状态为 '{item['status']}' 但缺少 skip_reason"
                    )

        return errors

    def _add_json_feedback(self, original_prompt: str) -> str:
        """Add JSON format feedback to the prompt for retry."""
        return (
            original_prompt
            + "\n\n⚠️ 你上一次的响应不是合法的 JSON。请确保只输出一个有效的 JSON 对象，"
            "不要用 markdown 代码块包裹，不要有任何额外文字。响应必须以 '{' 开头。"
        )

    def _add_manifest_feedback(self, original_prompt: str, errors: list[str]) -> str:
        """Add manifest validation errors to the prompt for retry."""
        error_text = "\n".join(f"  - {e}" for e in errors)
        return (
            original_prompt
            + f"\n\n⚠️ 你上一次输出的 manifest 有 {len(errors)} 个问题：\n{error_text}\n"
            "请修正这些问题后重新输出完整的 JSON。"
        )

    async def _notify_log(self, project_id: str, message: str) -> None:
        """Send a log message via WebSocket if manager is available."""
        if self.ws_manager:
            await self.ws_manager.send_log(project_id, self.agent_name, message)

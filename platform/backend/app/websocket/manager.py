"""WebSocket manager for real-time pipeline progress updates."""

import json
import asyncio
from typing import Any

from fastapi import WebSocket


class WebSocketManager:
    """Manages WebSocket connections per project. Thread-safe via asyncio.Lock."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, project_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            if project_id not in self._connections:
                self._connections[project_id] = set()
            self._connections[project_id].add(websocket)

    def disconnect(self, project_id: str, websocket: WebSocket) -> None:
        # Called from websocket handler — no async needed for simple set discard
        if project_id in self._connections:
            self._connections[project_id].discard(websocket)
            if not self._connections[project_id]:
                del self._connections[project_id]

    async def send_event(self, project_id: str, event: dict[str, Any]) -> None:
        async with self._lock:
            if project_id not in self._connections:
                return
            connections = list(self._connections[project_id])

        message = json.dumps(event, ensure_ascii=False)
        dead: list[WebSocket] = []

        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                if project_id in self._connections:
                    for ws in dead:
                        self._connections[project_id].discard(ws)

    async def send_log(
        self, project_id: str, agent_name: str, message: str
    ) -> None:
        """Send an agent log event."""
        await self.send_event(project_id, {
            "type": "agent_log",
            "step": agent_name,
            "message": message,
            "level": "info",
        })

    async def send_step_started(
        self, project_id: str, step: str, label: str
    ) -> None:
        """Send a step started event."""
        await self.send_event(project_id, {
            "type": "step_started",
            "step": step,
            "label": label,
        })

    async def send_step_completed(
        self, project_id: str, step: str, label: str, duration_ms: float, summary: str = ""
    ) -> None:
        """Send a step completed event."""
        await self.send_event(project_id, {
            "type": "step_completed",
            "step": step,
            "label": label,
            "duration_ms": int(duration_ms),
            "summary": summary,
        })

    async def send_step_failed(
        self, project_id: str, step: str, label: str, error: str, retryable: bool = False
    ) -> None:
        """Send a step failed event."""
        await self.send_event(project_id, {
            "type": "step_failed",
            "step": step,
            "label": label,
            "error": error,
            "retryable": retryable,
        })

    async def send_pipeline_completed(self, project_id: str, stats: dict) -> None:
        """Send pipeline completed event."""
        await self.send_event(project_id, {
            "type": "pipeline_completed",
            "project_id": project_id,
            "stats": stats,
        })

    async def send_pipeline_failed(
        self, project_id: str, failed_step: str, error: str
    ) -> None:
        """Send pipeline failed event."""
        await self.send_event(project_id, {
            "type": "pipeline_failed",
            "project_id": project_id,
            "failed_step": failed_step,
            "error": error,
        })

    def has_connections(self, project_id: str) -> bool:
        """Check if there are active connections for a project."""
        return project_id in self._connections and len(self._connections[project_id]) > 0


# Global singleton
ws_manager = WebSocketManager()

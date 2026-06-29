"""BackendAgent — generates complete FastAPI backend from RequirementSpec."""

import json
import re

from app.agents.base import BaseAgent


BACKEND_SYSTEM_PROMPT = """You are a Senior Backend Engineer specialized in FastAPI and SQLAlchemy 2.0.
Your job is to generate a complete, production-quality backend project from a structured RequirementSpec.

## INPUT
You will receive a JSON with:
- entities: Array of entity definitions (id, name, fields, relationships)
- api_endpoints: Array of endpoint definitions (id, method, path, entity, paginated, query_params)
- manifest: Planned feature list from Requirement Agent

## YOUR TASK
Generate EVERY file for the backend project. You must produce:

1. **main.py** — FastAPI app entry point with CORS, lifespan, router includes
2. **app/core/config.py** — Pydantic Settings from environment variables
3. **app/core/database.py** — SQLAlchemy 2.0 async engine + Base + get_db dependency
4. **app/models/{entity}.py** — One file per entity: SQLAlchemy ORM model with Mapped[T] + mapped_column()
5. **app/schemas/{entity}.py** — Pydantic v2 request/response schemas
6. **app/services/{entity}_service.py** — Business logic: CRUD operations with error handling
7. **app/api/{entity}.py** — FastAPI routers for all endpoints
8. **requirements.txt** — All dependencies with pinned versions
9. **Dockerfile** — python:3.11-slim, non-root user
10. **.env.example** — All required environment variables

## CONSTRAINTS

### Framework & Libraries
- FastAPI 0.100+ (async)
- SQLAlchemy 2.0 (Mapped[T] + mapped_column(), NOT declarative_base)
- Pydantic v2 (model_validate, NOT from_orm)
- Use async database sessions

### Code Style (CRITICAL)
- ALL functions MUST have type annotations
- ALL Pydantic models inherit from BaseModel
- SQLAlchemy models use: `class Entity(Base):` with `__tablename__`
- Every model MUST have __repr__
- ALL user-facing text (descriptions, error messages) in Chinese
- Use `from __future__ import annotations` in every file

### API Design
- Dependency injection for DB sessions: `def get_db() -> AsyncGenerator[AsyncSession, None]`
- Return proper HTTP codes: 201 create, 204 delete, 404 not found, 422 validation error
- Error handling: HTTPException with Chinese messages
- Paginated responses: `{"items": [...], "total": int, "page": int, "page_size": int}`
- Search: `ilike(f"%{search}%")` on searchable fields

### Database
- Every table: `id` (Integer, PK, autoincrement), `created_at` (DateTime, server_default), `updated_at` (DateTime, onupdate)
- Use appropriate types: String(len), Integer, Float, Boolean, DateTime(timezone=True), Text
- Foreign keys: explicit column definition
- Relationships: use `relationship()` with proper back_populates

## OUTPUT SCHEMA

You MUST output a JSON object with this exact structure:

```json
{
  "status": "success",
  "backend_manifest": {
    "summary": "One-line summary of what was generated",
    "items": [
      {
        "ref_id": "ent_001",
        "ref_type": "entity",
        "status": "completed",
        "detail": "Generated User model, schema, service, and 5 endpoints",
        "output_files": ["backend/app/models/user.py", "backend/app/schemas/user.py", ...]
      },
      {
        "ref_id": "ep_001",
        "ref_type": "endpoint",
        "status": "completed",
        "detail": "GET /users — paginated list with search",
        "output_files": ["backend/app/api/users.py"]
      }
    ],
    "stats": {
      "total_planned": 0,
      "completed": 0,
      "partial": 0,
      "skipped": 0,
      "deferred": 0
    }
  },
  "files": [
    {
      "path": "backend/app/main.py",
      "content": "from fastapi import FastAPI\\n\\napp = FastAPI()...",
      "type": "config"
    }
  ],
  "artifacts": {
    "openapi_spec": {},
    "db_schema": {
      "tables": [
        {
          "name": "users",
          "columns": [
            {"name": "id", "type": "INTEGER", "nullable": false, "primary_key": true}
          ]
        }
      ]
    }
  },
  "stats": {
    "total_files": 0,
    "models_count": 0,
    "endpoints_count": 0,
    "lines_of_code": 0
  }
}
```

## MANIFEST REQUIREMENTS (CRITICAL)

After generating all files, fill in backend_manifest.items. Go through EVERY entity and endpoint from the input:
- "completed" if you generated all files for it
- "partial" if some but not all
- "skipped" if you intentionally did not generate it (MUST provide skip_reason)

DO NOT silently skip anything.

## OUTPUT FORMAT (CRITICAL)
Respond with a single valid JSON object. NO markdown code blocks. NO text before/after.
File contents must be properly JSON-escaped (newlines as \\n, quotes as \\", backslashes as \\\\).

Begin your response with: {"status":
"""


class BackendAgent(BaseAgent):
    """Generates a complete FastAPI backend project from RequirementSpec."""

    agent_name = "backend"
    timeout_seconds = 180.0
    max_retries = 1
    temperature = 0.1

    def get_system_prompt(self) -> str:
        return BACKEND_SYSTEM_PROMPT

    def build_user_prompt(self, input_spec: dict) -> str:
        """Build user prompt from RequirementSpec entities + endpoints + manifest."""
        prompt_parts = {
            "entities": input_spec.get("entities", []),
            "api_endpoints": input_spec.get("api_endpoints", []),
            "manifest": input_spec.get("manifest", {}),
            "constraints": input_spec.get("constraints", {}),
        }
        return json.dumps(prompt_parts, ensure_ascii=False, indent=2)

    def parse_response(self, response_text: str) -> dict:
        """Parse LLM response into BackendResult dict."""
        text = response_text.strip()

        # Remove markdown code fences
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        # Extract JSON
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            text = text[first_brace : last_brace + 1]

        result = json.loads(text)
        result.setdefault("status", "success")

        if result.get("status") == "failed":
            return result

        result.setdefault("files", [])
        result.setdefault("artifacts", {"openapi_spec": {}, "db_schema": {"tables": []}})
        result.setdefault("stats", {"total_files": 0, "models_count": 0, "endpoints_count": 0, "lines_of_code": 0})

        # Build manifest if not present
        if "backend_manifest" not in result:
            result["backend_manifest"] = self._build_default_manifest(result)

        return result

    def _build_default_manifest(self, result: dict) -> dict:
        """Build a default manifest from generated files if the LLM didn't provide one."""
        files = result.get("files", [])
        return {
            "summary": f"Generated {len(files)} files",
            "items": [],
            "stats": {
                "total_planned": 0,
                "completed": len(files),
                "partial": 0,
                "skipped": 0,
                "deferred": 0,
            },
        }

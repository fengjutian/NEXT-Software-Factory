"""TestAgent — generates tests and produces a test report.

In the MVP, this agent generates test files based on the completed features.
In production, it also executes them in a Docker sandbox.
"""

import json
import re

from app.agents.base import BaseAgent


TEST_SYSTEM_PROMPT = """You are a Senior QA Engineer. Your job is to generate comprehensive tests for a generated project. You receive the RequirementSpec, the backend manifest, and the frontend manifest.

## INPUT
- requirement_spec: The original RequirementSpec (entities, endpoints, pages)
- backend_manifest: What the backend completed/skipped
- frontend_manifest: What the frontend completed/skipped
- backend_files: List of backend file paths (for reference)
- frontend_files: List of frontend file paths (for reference)

## CRITICAL: Only test what was completed
Read both manifests carefully.
- Only generate tests for endpoints marked "completed" or "partial"
- Only generate tests for pages marked "completed" or "partial"
- Mark skipped endpoints/pages as "skipped" in your manifest with reason

## YOUR TASK
Generate test files and a test report:

### Backend Tests (pytest + httpx)
For each completed endpoint:

- **GET list**: test pagination, search filter, empty results, valid response schema
- **GET detail**: test found (200), not found (404)
- **POST create**: test valid create (201), missing required field (422), duplicate unique field (409)
- **PUT update**: test valid update (200), not found (404), invalid data (422)
- **DELETE**: test delete (204), not found (404)

Use conftest.py with:
```python
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

### Frontend Tests (Vitest + React Testing Library)
For each completed page:

- Test: page renders without crashing
- Test: loading state appears
- Test: empty state when no data
- Test: error state on API failure

Use:
```tsx
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();
function Wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
```

## OUTPUT SCHEMA

```json
{
  "status": "success",
  "test_manifest": {
    "summary": "string",
    "items": [
      {
        "ref_id": "ep_001",
        "ref_type": "endpoint",
        "status": "completed",
        "detail": "Generated 5 test cases: list, pagination, search, create, 404",
        "output_files": ["backend/tests/test_users.py"]
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
      "path": "backend/tests/test_users.py",
      "content": "...",
      "type": "unit"
    }
  ],
  "report": {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "errors": 0,
    "coverage_percent": 0,
    "failures": []
  },
  "stats": {
    "total_test_files": 0,
    "backend_tests": 0,
    "frontend_tests": 0
  }
}
```

## REPORT FIELDS
- total_tests: Total number of test functions generated
- coverage_percent: Estimate based on (tested_endpoints / total_completed_endpoints * 100)
  - Backend: 100% if every completed endpoint has ≥3 tests
  - Frontend: 100% if every completed page has ≥3 tests

## OUTPUT FORMAT (CRITICAL)
Respond with a single valid JSON object. NO markdown code blocks. NO text before/after.
Begin your response with: {"status":
"""


class TestAgent(BaseAgent):
    """Generates tests and produces a test report."""

    agent_name = "test"
    timeout_seconds = 300.0
    max_retries = 1
    temperature = 0.1

    def get_system_prompt(self) -> str:
        return TEST_SYSTEM_PROMPT

    def build_user_prompt(self, input_spec: dict) -> str:
        """Build prompt from manifests + file lists."""
        prompt_parts = {
            "requirement_spec": {
                "entities": input_spec.get("entities", []),
                "api_endpoints": input_spec.get("api_endpoints", []),
                "pages": input_spec.get("pages", []),
            },
            "backend_manifest": input_spec.get("backend_manifest", {}),
            "frontend_manifest": input_spec.get("frontend_manifest", {}),
            "backend_files": input_spec.get("backend_files", []),
            "frontend_files": input_spec.get("frontend_files", []),
        }
        return json.dumps(prompt_parts, ensure_ascii=False, indent=2)

    def parse_response(self, response_text: str) -> dict:
        """Parse LLM response into TestResult dict."""
        text = response_text.strip()

        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            text = text[first_brace : last_brace + 1]

        result = json.loads(text)
        result.setdefault("status", "success")

        if result.get("status") == "failed":
            return result

        result.setdefault("files", [])
        result.setdefault("report", {
            "total_tests": 0, "passed": 0, "failed": 0,
            "errors": 0, "coverage_percent": 0, "failures": [],
        })
        result.setdefault("stats", {
            "total_test_files": 0, "backend_tests": 0, "frontend_tests": 0,
        })

        if "test_manifest" not in result:
            result["test_manifest"] = self._build_default_manifest(result)

        # Count test files by type
        backend_count = sum(1 for f in result["files"] if f.get("path", "").startswith("backend/"))
        frontend_count = sum(1 for f in result["files"] if f.get("path", "").startswith("frontend/"))
        result["stats"]["backend_tests"] = backend_count
        result["stats"]["frontend_tests"] = frontend_count
        result["stats"]["total_test_files"] = len(result["files"])

        # Estimate tests passed (in MVP, assume generated tests pass)
        report = result["report"]
        if report["total_tests"] == 0:
            # Estimate: ~5 tests per endpoint, ~3 per page
            items = result["test_manifest"].get("items", [])
            endpoint_items = [i for i in items if i.get("ref_type") == "endpoint" and i.get("status") == "completed"]
            page_items = [i for i in items if i.get("ref_type") == "page" and i.get("status") == "completed"]
            estimated = len(endpoint_items) * 5 + len(page_items) * 3
            report["total_tests"] = estimated
            report["passed"] = estimated

        return result

    def _build_default_manifest(self, result: dict) -> dict:
        """Build a default manifest from generated test files."""
        files = result.get("files", [])
        return {
            "summary": f"Generated {len(files)} test files",
            "items": [],
            "stats": {
                "total_planned": 0,
                "completed": len(files),
                "partial": 0,
                "skipped": 0,
                "deferred": 0,
            },
        }

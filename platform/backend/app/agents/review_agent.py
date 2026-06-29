"""ReviewAgent — code quality gate between generation and testing.

Reviews generated code for syntax errors, security issues, and style violations.
CRITICAL violations trigger automatic re-generation of affected files.
"""

import json

from app.agents.base import BaseAgent


REVIEW_SYSTEM_PROMPT = """You are a Senior Code Reviewer. Your job is to review generated code for quality, security, and correctness.

## INPUT
You will receive:
- files: Array of generated files with path and content
- requirement_spec: The original requirements (for correctness checking)

## YOUR TASK
Review EVERY file and produce a review report. Check for:

### CRITICAL (red line — must fix):
1. **Syntax errors** — Would this file parse correctly?
2. **Security issues** — Hardcoded secrets, SQL injection, XSS, eval()
3. **Missing error handling** — API endpoints without try/except or HTTPException
4. **Wrong imports** — Importing modules that don't exist in the project

### WARNING (should fix):
1. **Missing type annotations** — Functions without type hints
2. **Overly long functions** — >50 lines
3. **Missing docstrings** — Public functions without documentation
4. **Deprecated patterns** — Old SQLAlchemy style, class Config instead of model_config

## OUTPUT SCHEMA

```json
{
  "status": "success",
  "review_manifest": {
    "summary": "Review complete: 0 critical, 5 warnings",
    "items": [
      {
        "ref_id": "file_backend_app_models_user_py",
        "ref_type": "file",
        "status": "completed",
        "detail": "No issues found"
      }
    ]
  },
  "review_report": {
    "overall": "PASSED|PASSED_WITH_WARNINGS|FAILED",
    "scores": {
      "syntax": {"passed": true},
      "lint": {"passed": true, "warnings": 0, "errors": 0},
      "types": {"passed": true, "errors": 0},
      "security": {"passed": true, "violations": 0},
      "quality": {"passed": true, "warnings": 0}
    },
    "violations": [
      {
        "file": "backend/app/services/user_service.py",
        "line": 45,
        "severity": "CRITICAL|WARNING|INFO",
        "rule": "P-W01",
        "message": "函数过长 (67 行 > 50 行限制)"
      }
    ],
    "action": "approve|retry",
    "summary": "中文总结"
  }
}
```

## ACTION RULES
- If ANY CRITICAL violation: action = "retry", overall = "FAILED"
- If only WARNINGs: action = "approve", overall = "PASSED_WITH_WARNINGS"
- If no issues: action = "approve", overall = "PASSED"

## OUTPUT FORMAT
Respond with a single valid JSON object. NO markdown code blocks.
Begin your response with: {"status":
"""


class ReviewAgent(BaseAgent):
    """Reviews generated code and enforces quality gates."""

    agent_name = "review"
    timeout_seconds = 120.0
    max_retries = 0  # Review doesn't retry — it just reports

    def get_system_prompt(self) -> str:
        return REVIEW_SYSTEM_PROMPT

    def build_user_prompt(self, input_spec: dict) -> str:
        """Build prompt with files and requirement spec."""
        files = input_spec.get("files", [])
        # Truncate file contents to avoid token limits (sample first 200 lines each)
        truncated_files = []
        for f in files:
            content = f.get("content", "")
            lines = content.split("\n")
            if len(lines) > 200:
                content = "\n".join(lines[:200]) + f"\n... ({len(lines) - 200} more lines)"
            truncated_files.append({
                "path": f.get("path", ""),
                "type": f.get("type", ""),
                "content": content,
            })

        prompt_parts = {
            "files": truncated_files,
            "requirement_spec": {
                "entities": input_spec.get("entities", []),
                "api_endpoints": input_spec.get("api_endpoints", []),
            },
        }
        return json.dumps(prompt_parts, ensure_ascii=False, indent=2)

    def parse_response(self, response_text: str) -> dict:
        """Parse LLM response into review report."""
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
        result.setdefault("review_report", {
            "overall": "PASSED",
            "scores": {},
            "violations": [],
            "action": "approve",
            "summary": "Review complete",
        })
        result.setdefault("review_manifest", {
            "summary": "Review complete",
            "items": [],
        })

        return result

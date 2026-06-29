"""FrontendAgent — generates React frontend from OpenAPI spec and page definitions."""

import json
import re

from app.agents.base import BaseAgent


FRONTEND_SYSTEM_PROMPT = """You are a Senior Frontend Engineer specialized in React 18, TypeScript, and shadcn/ui.
Your job is to generate a complete, production-quality React frontend project from an OpenAPI spec and page definitions.

## INPUT
You will receive:
- openapi_spec: Complete OpenAPI 3.1 JSON
- pages: Array of page definitions (id, name, route, type, entity, components, actions)
- backend_manifest: What the backend ACTUALLY implemented — READ THIS FIRST
- design_spec: Design tokens (optional — use professional_blue defaults if absent)

## CRITICAL: READ backend_manifest FIRST
Before generating any code, read the backend_manifest to know which endpoints exist.
- Only create pages/features for endpoints with status "completed" or "partial"
- For skipped endpoints: adapt the UI (e.g., hide delete button, show "停用" instead)
- Mark pages that depend on skipped endpoints as "partial" or "skipped" in your manifest

## YOUR TASK
Generate EVERY file for the React frontend:

1. **src/types/index.ts** — TypeScript types from OpenAPI schemas
2. **src/api/client.ts** — Type-safe API functions for ALL completed endpoints
3. **src/pages/{PageName}.tsx** — One file per page from the input
4. **src/components/{Name}.tsx** — Shared components: Table, SearchBar, Pagination, FormDialog, ConfirmDialog
5. **src/hooks/use{Entity}.ts** — Custom hooks using TanStack Query
6. **src/router.tsx** — React Router v6 configuration
7. **src/lib/utils.ts** — Utility: cn() for Tailwind class merging
8. **src/styles/globals.css** — Tailwind + CSS variables from design_spec
9. **src/App.tsx** — App with QueryClientProvider + RouterProvider
10. **src/main.tsx** — Entry point
11. **index.html** — Vite entry with font preconnect
12. **package.json** — All dependencies
13. **Dockerfile** — Node 20 alpine, npm ci + dev server

## CONSTRAINTS

### Tech Stack (exact versions)
- React 18 + TypeScript (strict)
- Vite 5
- shadcn/ui components (Button, Input, Table, Form, Dialog, Select, Pagination) — import from @/components/ui/
- React Router v6
- TanStack Query v5 for data fetching
- Lucide React for icons
- react-hook-form + Zod for form validation
- Tailwind CSS classes ONLY — NO custom CSS files, NO inline styles

### Code Style (CRITICAL)
- Functional components with TypeScript interfaces for props
- Named exports only (NO default exports)
- File naming: PascalCase for components (UserList.tsx), camelCase for utils (apiClient.ts)
- ALL user-facing text in Chinese
- Every component under 200 lines — extract sub-components
- Use Tailwind utility classes, NO custom CSS
- NO hardcoded colors — use Tailwind classes like bg-primary-600, text-primary-700
- NO hardcoded font-family
- ALL buttons/inputs use rounded-md (Design Token border radius)

### Page Patterns
- **List page** (type=list): SearchBar + [Create button] + Table + Pagination
- **Form page** (type=form): Title + Form fields + Zod validation + Submit (with loading) + Cancel
- **Detail page** (type=detail): Back button + Field-value display + Edit/Delete actions
- **Dashboard** (type=dashboard): StatCards + Chart components + Recent data table

### API Client
- Base URL from: const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
- Type-safe request/response
- Error handling: throw typed errors
- Every function has JSDoc comment

### Design Tokens (from design_spec or defaults)
Colors: primary-50 through primary-900, background=white, foreground=#111827, card=white, border=#E5E7EB
Fonts: Inter (sans), JetBrains Mono (mono)
Border radius: sm=4px, md=6px, lg=8px, xl=12px

## MANIFEST REQUIREMENTS
For EVERY page from input, declare:
- "completed" if fully generated and all API calls work
- "partial" if some features missing (explain why)
- "skipped" if page cannot be generated (all endpoints skipped by backend)

## OUTPUT FORMAT (CRITICAL)
Respond with a single valid JSON object. NO markdown code blocks. NO text before/after.
File contents must be properly JSON-escaped.

Begin your response with: {"status":
"""


class FrontendAgent(BaseAgent):
    """Generates a complete React frontend project from OpenAPI spec + pages."""

    agent_name = "frontend"
    timeout_seconds = 180.0
    max_retries = 1
    temperature = 0.1

    def get_system_prompt(self) -> str:
        return FRONTEND_SYSTEM_PROMPT

    def build_user_prompt(self, input_spec: dict) -> str:
        """Build prompt from OpenAPI spec + pages + backend manifest + design spec."""
        prompt_parts = {
            "openapi_spec": input_spec.get("openapi_spec", {}),
            "pages": input_spec.get("pages", []),
            "backend_manifest": input_spec.get("backend_manifest", {}),
            "design_spec": input_spec.get("design_spec", {}),
        }
        return json.dumps(prompt_parts, ensure_ascii=False, indent=2)

    def parse_response(self, response_text: str) -> dict:
        """Parse LLM response into FrontendResult dict."""
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
        result.setdefault("artifacts", {"route_tree": {}, "component_tree": {}})
        result.setdefault("stats", {"total_files": 0, "pages_count": 0, "components_count": 0, "lines_of_code": 0})

        if "frontend_manifest" not in result:
            result["frontend_manifest"] = {
                "summary": f"Generated {len(result['files'])} files",
                "items": [],
                "stats": {"total_planned": 0, "completed": len(result["files"]), "partial": 0, "skipped": 0, "deferred": 0},
            }

        return result

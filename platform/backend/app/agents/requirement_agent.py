"""RequirementAgent — converts natural language requirements into structured RequirementSpec."""

import json
import re

from app.agents.base import BaseAgent


REQUIREMENT_SYSTEM_PROMPT = """You are a Senior Product Analyst at a software factory. Your job is to convert a user's natural language requirement into a structured, machine-readable specification (RequirementSpec) that downstream agents can use to generate code.

## INPUT
You will receive a JSON object with:
- requirement (string): The user's natural language description
- template (string | null): Preset hint: 'crud_admin' | 'rest_api' | 'dashboard'
- language (string): 'zh' or 'en'
- constraints (object): Technical constraints

## YOUR TASK
Analyze the requirement and produce a RequirementSpec JSON:

1. **Entities** — Every "thing" the user wants to manage. Name in PascalCase. Infer fields from context.
   - Every entity gets a unique `id` like "ent_001"
   - Auto-include id (integer, auto), created_at, updated_at for every entity

2. **API Endpoints** — Standard CRUD + custom endpoints. Every endpoint gets `id` like "ep_001"

3. **Pages** — Screens users see. Every page gets `id` like "page_001"

4. **Manifest** — planned feature list tracking all IDs

## CONSTRAINTS
- Entity names: PascalCase, singular (e.g., "User" not "Users")
- Field names: snake_case (e.g., "created_at")
- Endpoint paths: lowercase, plural nouns (e.g., "/users")
- If user asks for "management system" or "增删改查": generate full CRUD
- If user mentions "search" or "搜索": add search query param + mark fields searchable
- If user mentions "pagination" or "分页": mark list endpoints as paginated
- DO NOT invent features the user didn't ask for
- For vague requirements, make reasonable minimal inferences

## OUTPUT SCHEMA
```json
{
  "project_name": "kebab-case-name",
  "summary": "One-sentence Chinese summary",
  "manifest": {
    "planned": {
      "entities": ["ent_001"],
      "endpoints": ["ep_001", "ep_002"],
      "pages": ["page_001"]
    }
  },
  "entities": [
    {
      "id": "ent_001",
      "name": "EntityName",
      "display_name": "中文名",
      "fields": [
        {
          "name": "field_name",
          "display_name": "中文字段名",
          "type": "string|integer|float|boolean|datetime|text|enum",
          "required": true|false,
          "unique": true|false,
          "max_length": 50,
          "enum_values": ["a", "b"],
          "searchable": true|false,
          "sortable": true|false
        }
      ],
      "relationships": [
        {
          "type": "belongs_to|has_many|many_to_many",
          "target_entity": "OtherEntity",
          "foreign_key": "other_entity_id",
          "nullable": false
        }
      ]
    }
  ],
  "api_endpoints": [
    {
      "id": "ep_001",
      "method": "GET",
      "path": "/users",
      "description": "中文描述",
      "entity": "ent_001",
      "query_params": [{"name": "page", "type": "integer", "default": 1}],
      "request_body": null,
      "paginated": true,
      "auth_required": false
    }
  ],
  "pages": [
    {
      "id": "page_001",
      "name": "PageComponentName",
      "display_name": "中文页面名",
      "route": "/path",
      "type": "list|detail|form|dashboard",
      "entity": "ent_001",
      "components": ["table", "search", "pagination"],
      "actions": ["create", "edit", "delete"]
    }
  ]
}
```

## OUTPUT FORMAT (CRITICAL)
Respond with a single valid JSON object. NO markdown code blocks (no ```json). NO text before or after the JSON.
Begin your response with: {"project_name":
"""


class RequirementAgent(BaseAgent):
    """Converts natural language to structured RequirementSpec."""

    agent_name = "requirement"
    timeout_seconds = 60.0
    max_retries = 1

    def get_system_prompt(self) -> str:
        return REQUIREMENT_SYSTEM_PROMPT

    def build_user_prompt(self, input_spec: dict) -> str:
        """Build user prompt from NaturalLanguageSpec."""
        return json.dumps(input_spec, ensure_ascii=False, indent=2)

    def parse_response(self, response_text: str) -> dict:
        """Parse LLM response into RequirementSpec dict with validation.

        Cleans up common LLM formatting issues before parsing.
        """
        text = response_text.strip()

        # Remove markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove opening fence
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove closing fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        # Extract JSON object if there's extra text
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            text = text[first_brace : last_brace + 1]

        result = json.loads(text)

        # Ensure top-level fields exist
        result.setdefault("status", "success")

        if result.get("status") == "failed":
            return result

        result.setdefault("project_name", "untitled-project")
        result.setdefault("summary", "")
        result.setdefault("manifest", {"planned": {"entities": [], "endpoints": [], "pages": []}})
        result.setdefault("entities", [])
        result.setdefault("api_endpoints", [])
        result.setdefault("pages", [])

        # Validate entity names are PascalCase
        for entity in result.get("entities", []):
            name = entity.get("name", "")
            if name and not re.match(r'^[A-Z][a-zA-Z0-9]*$', name):
                # Auto-fix: convert to PascalCase
                entity["name"] = self._to_pascal_case(name)

        # Validate field names are snake_case
        for entity in result.get("entities", []):
            for field in entity.get("fields", []):
                name = field.get("name", "")
                if name and not re.match(r'^[a-z][a-z0-9_]*$', name):
                    field["name"] = self._to_snake_case(name)

        return result

    @staticmethod
    def _to_pascal_case(name: str) -> str:
        """Convert arbitrary string to PascalCase."""
        # Replace non-alphanumeric with spaces, then capitalize each word
        cleaned = re.sub(r'[^a-zA-Z0-9]', ' ', name)
        words = cleaned.split()
        return ''.join(w.capitalize() for w in words)

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """Convert arbitrary string to snake_case."""
        # Insert underscore before capital letters, lowercase everything
        s1 = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
        s2 = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1)
        return s2.lower().replace(' ', '_').replace('-', '_')

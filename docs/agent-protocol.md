# Agent Protocol Specification v0.1

> 本文档定义 AI Project Factory 中所有 Agent 之间的**输入/输出契约**。  
> 每个 Agent 消费一个结构化 Spec，产出一个结构化 Result。Agent 之间不传递自然语言。

---

## 1. 设计原则

| 原则 | 说明 |
|---|---|
| **结构化优先** | Agent 之间永远传递 JSON，不传递自然语言。自然语言只在用户入口出现一次 |
| **渐进增强** | 必填字段极少，可选字段丰富——简单需求不需要填满 |
| **契约即文档** | Agent 的输入 Spec 本身就可以作为「AI 对你的需求理解正确吗？」的展示 |
| **完成清单（Manifest）** | 每个 Agent 必须声明自己完成了哪些功能、跳过了哪些、为什么——下游 Agent 只读 manifest，不猜测上游做了什么 |
| **功能可追踪** | RequirementSpec 中每个 entity/endpoint/page 都有唯一 `id`，贯穿整个流水线用于追踪 |
| **向前兼容** | 新增字段必须可选，旧 Agent 忽略未知字段不报错 |
| **可追溯** | 每个 Agent 的输入/输出完整存储在 `agent_runs` 表中，用于调试和回归 |

---

## 2. 顶层流程

```
用户自然语言
      │
      ▼
┌─────────────────────────────────────────────────┐
│ Requirement Agent                                │
│                                                  │
│ Input:  NaturalLanguageSpec                     │
│ Output: RequirementSpec                          │
│         (含所有功能 ID：entity_id, endpoint_id,  │
│          page_id —— 这是全流水线的追踪锚点)       │
└────────────────────┬────────────────────────────┘
                     │ RequirementSpec
                     │ (带 manifest: 已规划的完整功能清单)
                     ▼
┌─────────────────────────────────────────────────┐
│ Backend Agent                                    │
│                                                  │
│ Input:  RequirementSpec.entities                 │
│         + RequirementSpec.api_endpoints          │
│ Output: BackendResult                            │
│         (含 backend_manifest: 声明每个 entity/   │
│          endpoint 的实现状态)                     │
└────────────────────┬────────────────────────────┘
                     │ BackendResult
                     │ (含 manifest + openapi_spec)
                     ▼
┌─────────────────────────────────────────────────┐
│ Frontend Agent                                   │
│                                                  │
│ Input:  BackendResult.artifacts.openapi_spec     │
│         + RequirementSpec.pages                  │
│         + BackendResult.backend_manifest ← 读这个│
│ Output: FrontendResult                           │
│         (含 frontend_manifest: 声明每个 page 的  │
│          实现状态，以及对接了哪些 endpoint)        │
└────────────────────┬────────────────────────────┘
                     │ FrontendResult
                     │ (含 manifest)
                     ▼
┌─────────────────────────────────────────────────┐
│ Test Agent                                       │
│                                                  │
│ Input:  RequirementSpec (全量功能 ID)            │
│         + BackendResult.backend_manifest         │
│         + FrontendResult.frontend_manifest       │
│ Output: TestResult                               │
│         (含 test_manifest: 声明每个功能覆盖了    │
│          哪些测试、哪些未覆盖)                    │
└─────────────────────────────────────────────────┘
```

---

## 3. NaturalLanguageSpec

用户入口，Requirement Agent 的唯一输入。

```json
{
  "requirement": "string (required) — 用户输入的自然语言需求，最大 2000 字",
  "template": "string | null — 预设模板标识: 'crud_admin' | 'rest_api' | 'dashboard'",
  "language": "string — 'zh' | 'en'，默认 'zh'",
  "constraints": {
    "target_framework": "string — MVP 固定 'fastapi'，未来可扩展",
    "target_frontend": "string — MVP 固定 'react'",
    "database": "string — 'sqlite' | 'postgresql'，默认 'sqlite'",
    "auth_required": "boolean — 是否需要认证，默认 false",
    "max_entities": "number — 最大实体数限制，默认 10"
  }
}
```

**示例**：

```json
{
  "requirement": "我要做一个用户管理系统，支持用户的增删改查、角色管理、分页查询和搜索",
  "template": "crud_admin",
  "language": "zh",
  "constraints": {
    "target_framework": "fastapi",
    "target_frontend": "react",
    "database": "sqlite"
  }
}
```

---

## 4. RequirementSpec

Requirement Agent 的输出，Backend Agent 和 Frontend Agent 的输入源。

```json
{
  "project_name": "string — 自动生成的项目名称，如 'user-management-system'",
  "summary": "string — 对需求的一句话概括",
  "manifest": {
    "planned": {
      "entities": ["string"] — 所有规划的 entity id 列表,
      "endpoints": ["string"] — 所有规划的 endpoint id 列表,
      "pages": ["string"] — 所有规划的 page id 列表
    }
  },
  "entities": [
    {
      "id": "string (required) — 唯一标识，如 'ent_001'，全流水线追踪用",
      "name": "string (required) — 实体英文名，PascalCase，如 'User'",
      "display_name": "string — 中文展示名，如 '用户'",
      "description": "string — 实体描述",
      "fields": [
        {
          "name": "string (required) — 字段英文名，snake_case，如 'email'",
          "display_name": "string — 中文名，如 '邮箱'",
          "type": "string (required) — 'string' | 'integer' | 'float' | 'boolean' | 'datetime' | 'text' | 'enum' | 'file'",
          "required": "boolean — 是否必填，默认 false",
          "unique": "boolean — 是否唯一，默认 false",
          "max_length": "number — 字符串最大长度",
          "min_value": "number — 数值最小值",
          "max_value": "number — 数值最大值",
          "default": "any — 默认值",
          "enum_values": ["string"] — 当 type='enum' 时的可选值,
          "searchable": "boolean — 是否支持搜索，默认 false",
          "sortable": "boolean — 是否支持排序，默认 false"
        }
      ],
      "relationships": [
        {
          "type": "string (required) — 'belongs_to' | 'has_many' | 'many_to_many'",
          "target_entity": "string (required) — 关联的目标实体名",
          "foreign_key": "string — 外键字段名，默认自动生成",
          "nullable": "boolean — 默认 false"
        }
      ]
    }
  ],
  "api_endpoints": [
    {
      "id": "string (required) — 唯一标识，如 'ep_001'",
      "method": "string (required) — 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'",
      "path": "string (required) — 如 '/users' 或 '/users/{id}'",
      "description": "string — 中文描述",
      "entity": "string — 关联的实体名",
      "query_params": [
        {
          "name": "string — 如 'page', 'page_size', 'search', 'sort_by', 'sort_order'",
          "type": "string — 'integer' | 'string' | 'boolean'",
          "required": "boolean",
          "default": "any"
        }
      ],
      "request_body": "string | null — 关联的 Schema 名（POST/PUT/PATCH 时）",
      "response_body": "string — 关联的 Schema 名",
      "paginated": "boolean — 是否分页，默认 false",
      "auth_required": "boolean — 是否需要认证，默认 false"
    }
  ],
  "pages": [
    {
      "id": "string (required) — 唯一标识，如 'page_001'",
      "name": "string (required) — 页面英文名，如 'UserList'",
      "display_name": "string — 中文名，如 '用户列表'",
      "route": "string (required) — 路由路径，如 '/users'",
      "type": "string (required) — 'list' | 'detail' | 'form' | 'dashboard'",
      "entity": "string — 关联的实体名（list/detail/form 时）",
      "components": ["string"] — 需要的组件类型: 'table' | 'form' | 'search' | 'pagination' | 'modal' | 'chart',
      "actions": ["string"] — 页面操作: 'create' | 'edit' | 'delete' | 'view' | 'export'
    }
  ]
}
```

**示例（用户管理系统）**：

```json
{
  "project_name": "user-management-system",
  "summary": "一个支持用户 CRUD、角色管理、分页查询和搜索的管理系统",
  "manifest": {
    "planned": {
      "entities": ["ent_001"],
      "endpoints": ["ep_001", "ep_002", "ep_003", "ep_004", "ep_005"],
      "pages": ["page_001", "page_002", "page_003", "page_004"]
    }
  },
  "entities": [
    {
      "id": "ent_001",
      "name": "User",
      "display_name": "用户",
      "fields": [
        {"name": "username", "display_name": "用户名", "type": "string", "required": true, "unique": true, "max_length": 50, "searchable": true},
        {"name": "email", "display_name": "邮箱", "type": "string", "required": true, "unique": true, "max_length": 100, "searchable": true},
        {"name": "full_name", "display_name": "姓名", "type": "string", "max_length": 100, "searchable": true},
        {"name": "status", "display_name": "状态", "type": "enum", "enum_values": ["active", "inactive", "suspended"], "default": "active"},
        {"name": "role", "display_name": "角色", "type": "enum", "enum_values": ["admin", "editor", "viewer"], "required": true}
      ]
    }
  ],
  "api_endpoints": [
    {"id": "ep_001", "method": "GET", "path": "/users", "description": "分页查询用户列表", "entity": "ent_001", "paginated": true, "query_params": [
      {"name": "page", "type": "integer", "default": 1},
      {"name": "page_size", "type": "integer", "default": 20},
      {"name": "search", "type": "string"},
      {"name": "sort_by", "type": "string", "default": "id"},
      {"name": "sort_order", "type": "string", "default": "desc"}
    ]},
    {"id": "ep_002", "method": "GET", "path": "/users/{id}", "description": "获取单个用户详情", "entity": "ent_001"},
    {"id": "ep_003", "method": "POST", "path": "/users", "description": "创建用户", "entity": "ent_001", "request_body": "UserCreate"},
    {"id": "ep_004", "method": "PUT", "path": "/users/{id}", "description": "更新用户", "entity": "ent_001", "request_body": "UserUpdate"},
    {"id": "ep_005", "method": "DELETE", "path": "/users/{id}", "description": "删除用户", "entity": "ent_001"}
  ],
  "pages": [
    {"id": "page_001", "name": "UserList", "display_name": "用户列表", "route": "/users", "type": "list", "entity": "ent_001", "components": ["table", "search", "pagination"], "actions": ["create", "edit", "delete", "view"]},
    {"id": "page_002", "name": "UserCreate", "display_name": "创建用户", "route": "/users/create", "type": "form", "entity": "ent_001", "components": ["form"], "actions": ["create"]},
    {"id": "page_003", "name": "UserEdit", "display_name": "编辑用户", "route": "/users/{id}/edit", "type": "form", "entity": "ent_001", "components": ["form"], "actions": ["edit"]},
    {"id": "page_004", "name": "UserDetail", "display_name": "用户详情", "route": "/users/{id}", "type": "detail", "entity": "ent_001", "components": [], "actions": ["view", "edit", "delete"]}
  ]
}
```

---

## 5. Completion Manifest（完成清单）— 核心概念

### 5.1 为什么需要 Manifest

在流水线中，下游 Agent **不能假设上游完整交付**。例如：

- Backend Agent 可能因为技术限制跳过某个 endpoint（如 WebSocket 端点）
- Requirement Agent 可能规划了 5 个页面，但用户只有 3 个的权限
- Frontend Agent 发现某个 endpoint 没有对应的后端实现，不能生成该页面

**Manifest 就是每个 Agent 的「自我声明」**——我完成了什么，没完成什么，为什么。

### 5.2 Manifest 通用结构

每个 Agent 的输出都必须包含 `{agent_name}_manifest` 字段，结构如下：

```json
{
  "{agent_name}_manifest": {
    "summary": "string — 一句话总结本 Agent 的交付情况，如 '已生成 1 个 entity 的完整 CRUD，包含 5 个 API 端点'",
    "items": [
      {
        "ref_id": "string (required) — 对应 RequirementSpec 中的功能 ID（ent_001 / ep_001 / page_001）",
        "ref_type": "string (required) — 'entity' | 'endpoint' | 'page'",
        "status": "string (required) — 'completed' | 'partial' | 'skipped' | 'deferred'",
        "detail": "string — 具体完成情况描述",
        "output_files": ["string"] — 本项生成的文件路径列表,
        "skip_reason": "string | null — status=skipped/deferred 时必须填原因"
      }
    ],
    "stats": {
      "total_planned": "number — 上游规划的总数",
      "completed": "number",
      "partial": "number",
      "skipped": "number",
      "deferred": "number"
    }
  }
}
```

### 5.3 Status 含义

| Status | 含义 | 下游 Agent 行为 |
|---|---|---|
| `completed` | 完全实现，可正常使用 | 正常对接 |
| `partial` | 部分实现，详见 detail | 只对接已实现的部分 |
| `skipped` | 有意跳过，详见 skip_reason | 跳过此功能，不生成相关代码 |
| `deferred` | 本期不做，计划后续版本 | 不生成代码，但可在 UI 上标注「即将推出」 |

### 5.4 Manifest 流转示例

```
Requirement Agent 输出:
  manifest.planned = {
    entities: [ent_001],
    endpoints: [ep_001, ep_002, ep_003, ep_004, ep_005],
    pages: [page_001, page_002, page_003, page_004]
  }
        │
        ▼
Backend Agent 输出:
  backend_manifest.items = [
    { ref_id: "ent_001", status: "completed" },
    { ref_id: "ep_001", status: "completed" },
    { ref_id: "ep_002", status: "completed" },
    { ref_id: "ep_003", status: "completed" },
    { ref_id: "ep_004", status: "completed" },
    { ref_id: "ep_005", status: "skipped", skip_reason: "DELETE 端点需要软删除逻辑，已将 User.status 设为 'inactive'，使用 PUT /users/{id} 替代" }
  ]
        │
        ▼
Frontend Agent 读取 backend_manifest:
  发现 ep_005 (DELETE) → skipped
  → 删除按钮改用 PUT /users/{id} (设 status=inactive)
  → 在前端显示「停用」而非「删除」
  → frontend_manifest.items = [
      { ref_id: "page_001", status: "completed" },
      { ref_id: "page_002", status: "completed" },
      { ref_id: "page_003", status: "completed" },
      { ref_id: "page_004", status: "completed", 
        detail: "详情页删除按钮改为停用按钮（对应后端 ep_005 被跳过）" }
    ]
        │
        ▼
Test Agent 读取两份 manifest:
  只为 completed/partial 的功能生成测试
  → test_manifest.items = [
      { ref_id: "ep_001", status: "completed" },
      { ref_id: "ep_002", status: "completed" },
      { ref_id: "ep_003", status: "completed" },
      { ref_id: "ep_004", status: "completed" },
      { ref_id: "ep_005", status: "skipped", skip_reason: "后端未实现，无对应 API，跳过测试" }
    ]
```

---

## 6. BackendResult

Backend Agent 的输出。

```json
{
  "status": "'success' | 'failed'",
  "error": "string | null — 失败时的错误信息",
  "backend_manifest": { ... } — Completion Manifest（见第 5 节），必须逐项声明每个 entity 和 endpoint 的实现状态,
  "files": [
    {
      "path": "string — 相对于项目根目录的文件路径，如 'backend/app/models/user.py'",
      "content": "string — 文件内容",
      "type": "'model' | 'schema' | 'service' | 'router' | 'config' | 'migration' | 'test' | 'docker' | 'doc'"
    }
  ],
  "artifacts": {
    "openapi_spec": "object — 完整的 OpenAPI 3.1 JSON",
    "db_schema": {
      "tables": [
        {
          "name": "string",
          "columns": [
            {"name": "string", "type": "string", "nullable": "boolean", "primary_key": "boolean", "foreign_key": "string | null"}
          ]
        }
      ]
    }
  },
  "stats": {
    "total_files": "number",
    "models_count": "number",
    "endpoints_count": "number",
    "lines_of_code": "number"
  }
}
```

---

## 7. FrontendResult

Frontend Agent 的输出。

```json
{
  "status": "'success' | 'failed'",
  "error": "string | null",
  "frontend_manifest": { ... } — Completion Manifest（见第 5 节），必须逐项声明每个 page 的实现状态及对接的 endpoint,
  "files": [
    {
      "path": "string — 如 'frontend/src/pages/UserList.tsx'",
      "content": "string",
      "type": "'page' | 'component' | 'hook' | 'api_client' | 'store' | 'router' | 'config' | 'test' | 'doc'"
    }
  ],
  "artifacts": {
    "route_tree": {
      "routes": [
        {"path": "string", "component": "string", "lazy": "boolean"}
      ]
    },
    "component_tree": {
      "components": [
        {"name": "string", "type": "string", "props": ["string"]}
      ]
    }
  },
  "stats": {
    "total_files": "number",
    "pages_count": "number",
    "components_count": "number",
    "lines_of_code": "number"
  }
}
```

---

## 8. TestResult

Test Agent 的输出。

```json
{
  "status": "'success' | 'failed'",
  "error": "string | null",
  "test_manifest": { ... } — Completion Manifest（见第 5 节），必须逐项声明每个功能的测试覆盖状态,
  "files": [
    {
      "path": "string — 如 'backend/tests/test_users.py'",
      "content": "string",
      "type": "'unit' | 'integration' | 'e2e' | 'component' | 'config'"
    }
  ],
  "report": {
    "total_tests": "number",
    "passed": "number",
    "failed": "number",
    "errors": "number",
    "coverage_percent": "number",
    "failures": [
      {
        "test_name": "string",
        "file": "string",
        "line": "number",
        "message": "string"
      }
    ]
  },
  "stats": {
    "total_test_files": "number",
    "backend_tests": "number",
    "frontend_tests": "number"
  }
}
```

---

## 9. 完整流水线最终产物结构

```
{project_id}/
├── spec/
│   ├── requirement.json        # RequirementSpec（完整）
│   └── openapi.json            # OpenAPI 3.1 Spec
├── backend/
│   ├── app/
│   │   ├── models/             # SQLAlchemy Models
│   │   ├── schemas/            # Pydantic Schemas
│   │   ├── services/           # Business Logic
│   │   ├── api/                # FastAPI Routers
│   │   ├── core/               # Config, DB, Dependencies
│   │   └── main.py             # App Entry Point
│   ├── migrations/             # Alembic Migrations
│   ├── tests/                  # pytest Tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                # API Client (auto-generated)
│   │   ├── components/         # Shared UI Components
│   │   │   ├── ui/             # shadcn/ui components
│   │   │   ├── Table.tsx
│   │   │   ├── Form.tsx
│   │   │   └── SearchBar.tsx
│   │   ├── pages/              # Page Components
│   │   ├── hooks/              # Custom Hooks
│   │   ├── lib/                # Utilities
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── tests/                  # Vitest Tests
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## 10. Agent 实现约束

### 9.1 通用要求

每个 Agent 必须遵守：

| 约束 | 说明 |
|---|---|
| **幂等性** | 相同输入 → 相同输出（温度=0 时）。方便重试和调试 |
| **超时** | 单个 Agent 执行时间 ≤ 120 秒 |
| **完整性** | 输出必须包含所有要求的字段，即使为空也要填 `null` 或 `[]` |
| **错误处理** | 失败时返回 `status: "failed"` + 结构化 `error`，而不是抛异常 |
| **日志** | 实时推送进度信息（通过 WebSocket），不是静默执行 |
| **Manifest** | 输出必须包含 `{agent_name}_manifest`，逐项声明每个输入中带 `id` 的功能的实现状态。不允许「静默跳过」——没做的必须声明 skipped/deferred 并给出原因 |

### 10.2 Agent 内部的 System Prompt 模板结构

虽然 Agent 的具体 Prompt 需要反复调优，但结构应该遵循：

```
你是一个 [Agent 角色]，你的职责是 [一句话职责]。

## 输入规范
[解释输入 JSON 的每个字段含义]

## 输出规范
[解释输出 JSON 的每个字段含义]

**特别强调**：你的输出必须包含 `{agent_name}_manifest` 字段。
逐一检查输入中的每个 entity（带 id）、endpoint（带 id）、page（带 id），
对每项声明 status：completed / partial / skipped / deferred。
如果某项你没有实现，必须在 skip_reason 中说明原因。
不允许「静默跳过」任何功能。

## 技术约束
- 使用 [框架/库] 版本 [版本号]
- 代码风格遵循 [规范名称]
- 所有代码必须有类型注解（Python）/ 类型定义（TypeScript）
- 文件名使用 [命名规则]

## 质量要求
- [具体要求，如"所有 API 端点必须有错误处理"]
- [具体要求，如"生成的 SQLAlchemy 模型必须包含 __repr__"]

## 输出格式
只输出合法的 JSON，不要有任何解释文字，不要用 markdown 代码块包裹。
```

### 10.3 Requirement Agent 特别注意

这是最关键的一个 Agent——如果需求理解错了，后面全错。

- 必须在输出中包含 `summary` 字段，让用户快速验证理解是否正确
- 实体名自动翻译为英文 PascalCase，同时保留 `display_name` 中文
- 对模糊需求给出**合理推断**，比如用户说「用户管理」但没有说字段，默认给 username/email/status
- 推断的字段应该在字段列表中标注（未来可以加 `confidence` 字段）

---

## 11. 版本演进计划

| 版本 | 新增内容 |
|---|---|
| v0.1 (MVP) | 本文档定义的全部内容 |
| v0.2 | 增加 `auth` 模块：登录/注册/权限端点自动生成 |
| v0.3 | 增加 `file_upload` 字段类型支持 |
| v0.4 | 增加 `dashboard` 页面类型：图表配置 Spec |
| v1.0 | 支持多语言框架（FastAPI → 也支持 SpringBoot/NestJS/Go）|

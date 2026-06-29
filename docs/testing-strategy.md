# Testing Strategy v0.1

> 本文档定义 AI Project Factory 的**完整测试策略**。  
> 分为两大部分：① 平台自身的测试 ② 生成产物的测试（Test Agent 的测试标准）。  
> 工厂不仅要生成代码，还要保证生成的代码真的能跑。

---

## 1. 测试金字塔

```
                  ┌─────┐
                  │ E2E │  ← 全流程：用户输入 → 生成 → 产物跑通
                  └──┬──┘
               ┌─────┴─────┐
               │ Integration│ ← Agent 协作 / API 集成 / DB 集成
               └─────┬─────┘
            ┌─────────┴─────────┐
            │    Unit Tests     │  ← Agent 输入输出 / 组件渲染 / 工具函数
            └───────────────────┘
```

---

## 2. 平台自身测试

### 2.1 测试范围和工具

| 层级 | 范围 | 工具 | 目标覆盖率 |
|---|---|---|---|
| Unit | 后端：Agent 输入输出解析、Service 层、工具函数 | pytest | ≥ 85% |
| Unit | 前端：组件渲染、Hook 逻辑、表单验证 | Vitest + Testing Library | ≥ 75% |
| Integration | 后端：API 端点 + 数据库 + Agent Pipeline 任务 | pytest + httpx | ≥ 70% |
| Integration | 前端：页面交互流程、WebSocket 通信 | Vitest + MSW | ≥ 60% |
| E2E | 全流程：用户输入需求 → 查看进度 → 下载产物 | Playwright | 核心路径 100% |

### 2.2 后端单元测试

#### 目录结构

```
platform/backend/tests/
├── conftest.py                    # 共享 fixtures
├── unit/
│   ├── test_agent_base.py         # BaseAgent 抽象类测试
│   ├── test_requirement_agent.py  # Requirement Agent Prompt 构建 + 响应解析
│   ├── test_backend_agent.py      # Backend Agent
│   ├── test_frontend_agent.py     # Frontend Agent
│   ├── test_test_agent.py         # Test Agent
│   ├── test_orchestrator.py       # 流水线编排器
│   ├── test_manifest.py           # Manifest 构建/校验
│   ├── test_schemas.py            # Pydantic Schema 验证
│   └── test_utils.py              # 工具函数
├── integration/
│   ├── test_api_projects.py       # /api/v1/projects CRUD
│   ├── test_api_files.py          # 文件上传/下载/预览
│   ├── test_api_assets.py         # 设计资产上传 🆕
│   ├── test_websocket.py          # WebSocket 推送
│   ├── test_pipeline.py           # Celery 任务链
│   └── test_db.py                 # 数据库 Migration + ORM
└── e2e/
    ├── test_full_flow.py          # 完整流水线（含 LLM Mock）
    └── test_error_handling.py     # 错误场景
```

#### 关键测试用例

```python
# tests/unit/test_requirement_agent.py

class TestRequirementAgentOutput:
    """验证 Requirement Agent 的输出符合 Agent Protocol"""

    async def test_output_has_all_required_fields(self, agent, sample_input):
        """输出必须包含 project_name, summary, manifest, entities, endpoints, pages"""
        result = await agent.run(sample_input)
        required_fields = ["project_name", "summary", "manifest", 
                          "entities", "api_endpoints", "pages"]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    async def test_every_entity_has_id(self, agent, sample_input):
        """每个 entity 必须有 id 字段"""
        result = await agent.run(sample_input)
        for entity in result["entities"]:
            assert "id" in entity, f"Entity {entity.get('name')} missing id"
            assert entity["id"].startswith("ent_"), f"Entity id must start with 'ent_'"

    async def test_every_endpoint_has_id(self, agent, sample_input):
        """每个 endpoint 必须有 id 字段"""
        result = await agent.run(sample_input)
        for ep in result["api_endpoints"]:
            assert "id" in ep, f"Endpoint {ep.get('path')} missing id"

    async def test_manifest_covers_all_ids(self, agent, sample_input):
        """manifest.planned 必须包含所有 entity/endpoint/page 的 id"""
        result = await agent.run(sample_input)
        planned = result["manifest"]["planned"]
        entity_ids = [e["id"] for e in result["entities"]]
        assert set(planned["entities"]) == set(entity_ids), \
            "Manifest entities don't match actual entities"

    async def test_entity_names_are_pascal_case(self, agent, sample_input):
        """实体名必须是 PascalCase"""
        result = await agent.run(sample_input)
        import re
        for entity in result["entities"]:
            assert re.match(r'^[A-Z][a-zA-Z0-9]*$', entity["name"]), \
                f"Entity name '{entity['name']}' is not PascalCase"

    async def test_field_names_are_snake_case(self, agent, sample_input):
        """字段名必须是 snake_case"""
        result = await agent.run(sample_input)
        import re
        for entity in result["entities"]:
            for field in entity["fields"]:
                assert re.match(r'^[a-z][a-z0-9_]*$', field["name"]), \
                    f"Field name '{field['name']}' is not snake_case"
```

```python
# tests/unit/test_manifest.py

class TestManifestValidation:
    """验证 Completion Manifest 的正确性"""

    def test_manifest_stats_add_up(self, sample_manifest):
        """stats 中 completed+partial+skipped+deferred = total_planned"""
        s = sample_manifest["stats"]
        assert s["completed"] + s["partial"] + s["skipped"] + s["deferred"] \
               == s["total_planned"], "Stats don't add up"

    def test_every_skipped_has_reason(self, sample_manifest):
        """每个 skipped/deferred 项必须有 skip_reason"""
        for item in sample_manifest["items"]:
            if item["status"] in ("skipped", "deferred"):
                assert item.get("skip_reason"), \
                    f"Item {item['ref_id']} is {item['status']} but has no skip_reason"

    def test_ref_ids_are_valid_format(self, sample_manifest):
        """ref_id 格式：ent_001 / ep_001 / page_001"""
        import re
        for item in sample_manifest["items"]:
            assert re.match(r'^(ent|ep|page)_\d{3}$', item["ref_id"]), \
                f"Invalid ref_id format: {item['ref_id']}"

    def test_ref_type_matches_ref_id(self, sample_manifest):
        """ref_type 必须与 ref_id 前缀匹配"""
        for item in sample_manifest["items"]:
            prefix = item["ref_id"].split("_")[0]
            expected_type = {"ent": "entity", "ep": "endpoint", "page": "page"}
            assert item["ref_type"] == expected_type[prefix], \
                f"ref_type {item['ref_type']} doesn't match ref_id {item['ref_id']}"
```

### 2.3 后端集成测试

```python
# tests/integration/test_api_projects.py

class TestCreateProject:
    """POST /api/v1/projects"""

    async def test_create_project_returns_201(self, async_client):
        """正常创建项目返回 201"""
        response = await async_client.post("/api/v1/projects", json={
            "requirement": "我要做一个用户管理系统",
            "template": "crud_admin"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert data["data"]["status"] == "pending"

    async def test_create_project_empty_requirement(self, async_client):
        """空需求返回 422"""
        response = await async_client.post("/api/v1/projects", json={
            "requirement": "",
            "template": "crud_admin"
        })
        assert response.status_code == 422

    async def test_create_project_with_design_spec(self, async_client):
        """带 DesignSpec 创建项目"""
        response = await async_client.post("/api/v1/projects", json={
            "requirement": "用户管理系统",
            "template": "crud_admin",
            "design_spec": {
                "preset": "professional_blue",
                "brand": {"project_name": "我的 CRM"}
            }
        })
        assert response.status_code == 201
        # 验证 design_spec 被正确保存
        project_id = response.json()["data"]["id"]
        detail = await async_client.get(f"/api/v1/projects/{project_id}")
        assert detail.json()["data"]["design_spec"]["preset"] == "professional_blue"

    async def test_create_project_requirement_too_long(self, async_client):
        """超过 2000 字的需求返回 422"""
        response = await async_client.post("/api/v1/projects", json={
            "requirement": "x" * 2001
        })
        assert response.status_code == 422


class TestGetProject:
    """GET /api/v1/projects/{id}"""

    async def test_get_existing_project(self, async_client, seeded_project):
        """获取已存在的项目"""
        response = await async_client.get(f"/api/v1/projects/{seeded_project['id']}")
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "done"

    async def test_get_nonexistent_project(self, async_client):
        """获取不存在的项目返回 404"""
        response = await async_client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


class TestDeleteProject:
    """DELETE /api/v1/projects/{id}"""

    async def test_delete_cascades_files(self, async_client, db_session, seeded_project):
        """删除项目时级联删除关联文件"""
        response = await async_client.delete(f"/api/v1/projects/{seeded_project['id']}")
        assert response.status_code == 200
        # 确认文件也被删除
        files = await db_session.execute(
            select(GeneratedFile).where(GeneratedFile.project_id == seeded_project['id'])
        )
        assert files.scalar_one_or_none() is None
```

### 2.4 前端组件测试

```typescript
// frontend/tests/components/RequirementInput.test.tsx

import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RequirementInput } from '@/components/RequirementInput';

describe('RequirementInput', () => {
  it('renders textarea with placeholder', () => {
    render(<RequirementInput value="" onChange={() => {}} />);
    expect(screen.getByPlaceholderText(/描述你想要的项目/i)).toBeInTheDocument();
  });

  it('shows character count', () => {
    render(<RequirementInput value="Hello" onChange={() => {}} />);
    expect(screen.getByText(/5 \/ 2000/)).toBeInTheDocument();
  });

  it('shows error when under minimum length on submit', async () => {
    const user = userEvent.setup();
    render(<RequirementInput value="ab" onChange={() => {}} />);
    // 父组件传递 error prop
    const { rerender } = render(
      <RequirementInput value="ab" onChange={() => {}} error="请输入至少 10 个字" />
    );
    expect(screen.getByText(/请输入至少 10 个字/)).toBeInTheDocument();
  });

  it('shows error when over 2000 characters', () => {
    const longText = 'x'.repeat(2001);
    render(
      <RequirementInput value={longText} onChange={() => {}} error="已超过 2000 字限制" />
    );
    expect(screen.getByText(/已超过 2000 字限制/)).toBeInTheDocument();
  });
});
```

### 2.5 E2E 测试（Playwright）

```python
# tests/e2e/test_full_flow.py

class TestFullGenerationFlow:
    """端到端：用户输入需求 → 查看进度 → 下载产物"""

    async def test_full_crud_admin_flow(self, page, mock_llm):
        """使用 Mock LLM 测试完整流程"""
        
        # Step 1: 打开首页
        await page.goto("http://localhost:5173/")
        assert await page.title() == "AI Project Factory"
        
        # Step 2: 输入需求
        await page.fill('[data-testid="requirement-input"]', 
                        "我要做一个客户管理系统")
        await page.select_option('[data-testid="template-select"]', "crud_admin")
        
        # Step 3: 选择设计预设
        await page.click('[data-testid="preset-professional_blue"]')
        
        # Step 4: 点击生成
        await page.click('[data-testid="submit-button"]')
        
        # Step 5: 验证跳转到项目页
        await page.wait_for_url("**/projects/**")
        
        # Step 6: 等待流水线完成（Mock 模式下应该很快）
        await page.wait_for_selector('[data-testid="status-done"]', timeout=30000)
        
        # Step 7: 验证统计卡片
        assert await page.is_visible('[data-testid="stats-files"]')
        assert await page.is_visible('[data-testid="stats-coverage"]')
        
        # Step 8: 验证文件树可交互
        await page.click('[data-testid="file-tree"] >> text=main.py')
        await page.wait_for_selector('[data-testid="code-preview"]')
        
        # Step 9: 下载 ZIP
        async with page.expect_download() as download_info:
            await page.click('[data-testid="download-button"]')
        download = await download_info.value
        assert download.suggested_filename.endswith('.zip')
```

---

## 3. 生成产物测试（Test Agent 标准）

### 3.1 Test Agent 自身需要验证的事项

Test Agent 不仅生成测试，还要**运行测试**并报告结果。以下是 Test Agent 的质量标准：

| 验证项 | 方法 | 通过标准 |
|---|---|---|
| 生成的测试文件语法正确 | 解析 Python/TS AST | 0 语法错误 |
| 测试可以运行 | Docker Sandbox 执行 pytest/vitest | 退出码 = 0 |
| 每个 API 端点 ≥ 3 个测试 | 解析测试代码 AST | 每个端点 ≥ 3 个 test function |
| 覆盖正常路径 | 检查测试代码包含 valid input 场景 | 100% 端点有 happy path |
| 覆盖错误路径 | 检查测试代码包含 invalid/404 场景 | ≥ 80% 端点有 error path |
| 覆盖边界情况 | 检查测试代码包含 empty/limit 场景 | ≥ 50% 端点有 boundary case |

### 3.2 Docker Sandbox 执行流程

```
Test Agent 生成测试文件
      │
      ▼
创建临时 Docker 容器
  - 挂载生成的 backend/ 和 frontend/ 目录
  - 安装依赖 (pip install -r requirements.txt, npm install)
      │
      ▼
依次执行:
  1. alembic upgrade head        # 建表
  2. pytest backend/tests/ -v --cov --json-report   # 后端测试
  3. npx vitest run --reporter=json                  # 前端测试
      │
      ▼
收集结果 → 构建 TestResult JSON
      │
      ▼
销毁容器 → 返回报告
```

### 3.3 测试质量评分公式

```
TestScore = (CoverageScore × 0.4) + (PassRate × 0.3) + (TestCaseQuality × 0.3)

CoverageScore      = coverage_percent / 100
PassRate           = passed / total_tests
TestCaseQuality    = (happy_path_coverage × 0.5 
                      + error_path_coverage × 0.3 
                      + boundary_coverage × 0.2)
```

如果 TestScore < 0.6，Test Agent 应自动重新生成一次（最多 2 次重试）。

### 3.4 后端测试生成标准

```python
# Test Agent 必须为每个 endpoint 生成以下测试模式：

# ✅ GET /users (列表)
def test_get_users_returns_paginated_list(client):
    """分页查询用户列表 — 正常返回"""
    ...

def test_get_users_with_search(client):
    """分页查询用户列表 — 搜索过滤"""
    ...

def test_get_users_empty_result(client):
    """分页查询用户列表 — 空结果"""
    ...

def test_get_users_pagination(client):
    """分页查询用户列表 — 翻页"""
    ...

# ✅ POST /users (创建)
def test_create_user_success(client):
    """创建用户 — 正常创建"""
    ...

def test_create_user_missing_required_field(client):
    """创建用户 — 缺少必填字段"""
    ...

def test_create_user_duplicate_unique_field(client):
    """创建用户 — 唯一字段重复"""
    ...

def test_create_user_invalid_data_type(client):
    """创建用户 — 字段类型错误"""
    ...
```

### 3.5 前端测试生成标准

```typescript
// Test Agent 必须为每个页面生成以下测试模式：

// ✅ UserList Page
describe('UserList', () => {
  it('renders the page title');                    // 渲染
  it('shows loading state while fetching');        // 加载态
  it('shows empty state when no users');           // 空态
  it('renders user rows in table');                // 数据态
  it('shows error toast on API failure');          // 错误态
  it('navigates to create page on button click');  // 交互
});
```

---

## 4. Mock LLM 策略

测试时不能真的调用 Claude/GPT API（成本高、不稳定），需要 Mock 策略：

### 4.1 Mock 层级

```
Level 1: HTTP Mock (MSW / responses)
  └─ 拦截对 LLM API 的 HTTP 请求，返回预定义 JSON

Level 2: Agent Mock
  └─ 替换 Agent.call_llm() 方法，返回预定义响应

Level 3: Pipeline Mock
  └─ 替换整个 Celery Task，直接写入预生成的文件到 DB
```

### 4.2 Fixture 结构

```python
# tests/conftest.py

@pytest.fixture
def mock_claude_response() -> dict:
    """Mock Claude API 返回的 RequirementSpec"""
    return {
        "project_name": "test-project",
        "summary": "测试项目",
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
                "name": "User",
                "display_name": "用户",
                "fields": [
                    {"name": "username", "type": "string", "required": True},
                    {"name": "email", "type": "string", "required": True}
                ],
                "relationships": []
            }
        ],
        "api_endpoints": [
            {"id": "ep_001", "method": "GET", "path": "/users", "entity": "ent_001", "paginated": True},
            {"id": "ep_002", "method": "POST", "path": "/users", "entity": "ent_001", "request_body": "UserCreate"}
        ],
        "pages": [
            {"id": "page_001", "name": "UserList", "route": "/users", "type": "list", "entity": "ent_001"}
        ]
    }


@pytest.fixture
def mock_backend_files() -> list[dict]:
    """Mock Backend Agent 生成的文件列表"""
    return [
        {
            "path": "backend/app/main.py",
            "content": "from fastapi import FastAPI\n\napp = FastAPI()\n",
            "type": "config"
        },
        {
            "path": "backend/app/models/user.py",
            "content": "from sqlalchemy.orm import Mapped, mapped_column\n\nclass User(Base):\n    ...",
            "type": "model"
        }
    ]
```

---

## 5. CI/CD 测试流水线

```yaml
# .github/workflows/test.yml

name: Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: ai_factory_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r platform/backend/requirements.txt
      - run: pip install pytest pytest-asyncio pytest-cov
      - run: pytest platform/backend/tests/ --cov --cov-report=xml
      - uses: codecov/codecov-action@v4

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
        working-directory: platform/frontend
      - run: npx vitest run --coverage
        working-directory: platform/frontend

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    steps:
      - uses: actions/checkout@v4
      - run: docker compose up -d
      - run: npx playwright test
        working-directory: platform/e2e
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-screenshots
          path: platform/e2e/screenshots/
```

---

## 6. 测试覆盖率目标

| 组件 | 行覆盖率 | 分支覆盖率 | 说明 |
|---|---|---|---|
| `app/agents/` | 90% | 85% | Agent 核心逻辑，必须高覆盖 |
| `app/services/` | 85% | 80% | 业务逻辑层 |
| `app/api/` | 80% | 75% | API 端点 |
| `app/models/` | 60% | — | ORM 模型主要由框架保证 |
| `app/core/` | 85% | 80% | 配置和基础设施 |
| Frontend `components/` | 75% | 70% | UI 组件 |
| Frontend `pages/` | 70% | 65% | 页面组件 |
| Frontend `hooks/` | 85% | 80% | 自定义 Hook |

---

## 7. 测试环境

| 环境 | 用途 | 数据库 | LLM |
|---|---|---|---|
| **dev** | 本地开发 | SQLite (文件) | Mock |
| **test** | CI 运行 | PostgreSQL (Docker Service) | Mock |
| **staging** | 预发布验证 | PostgreSQL (独立实例) | Mock + 少量真实 API |
| **prod** | 生产 | PostgreSQL (RDS) | 真实 API |

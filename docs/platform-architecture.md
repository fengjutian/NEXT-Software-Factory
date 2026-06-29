# Platform Architecture v0.1

> 本文档定义 AI Project Factory **Web 平台自身**的系统架构、API 接口和数据库设计。  
> 平台自身也是一套 FastAPI + React 应用，与它生成的产物使用相同的技术栈。

---

## 1. 系统架构图

```
                          ┌──────────────────────┐
                          │    Nginx / Caddy     │
                          │    (反向代理 + 静态资源) │
                          └──────────┬───────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
          ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
          │  Frontend    │  │  API Server  │  │  Swagger UI  │
          │  (React SPA) │  │  (FastAPI)   │  │  (/docs)     │
          │  Port 5173   │  │  Port 8000   │  │              │
          └──────────────┘  └──────┬───────┘  └──────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
          ┌──────────────┐  ┌──────────┐  ┌──────────────┐
          │  PostgreSQL  │  │  Redis   │  │  File Store  │
          │  (项目/会话)  │  │ (队列/缓存)│  │  (生成文件)  │
          └──────────────┘  └────┬─────┘  └──────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Celery Worker  │
                        │  (Agent 执行器)  │
                        │                 │
                        │  ┌───────────┐  │
                        │  │ LLM API   │  │
                        │  │ Claude/GPT│  │
                        │  └───────────┘  │
                        │                 │
                        │  ┌───────────┐  │
                        │  │ Docker    │  │
                        │  │ Sandbox   │  │
                        │  │ (跑测试)   │  │
                        │  └───────────┘  │
                        └─────────────────┘
```

---

## 2. 技术栈详情

| 组件 | 技术选型 | 用途 |
|---|---|---|
| **Web Server** | FastAPI 0.100+ + Uvicorn | REST API + WebSocket |
| **异步任务** | Celery 5.x + Redis | Agent 流水线异步执行 |
| **数据库** | PostgreSQL 16 | 持久化项目/文件/运行记录 |
| **ORM** | SQLAlchemy 2.0 (async) | 数据库操作 |
| **Migration** | Alembic | 数据库版本管理 |
| **缓存** | Redis 7 | 任务队列 Broker + 结果缓存 |
| **文件存储** | 本地文件系统 | MVP 阶段，未来可迁 S3/MinIO |
| **前端** | React 18 + TypeScript + Vite | SPA |
| **UI 库** | shadcn/ui + Tailwind CSS | 平台自身 UI |
| **实时通信** | WebSocket (FastAPI 内置) | 推送流水线进度 |
| **LLM** | Claude API (Anthropic) | Agent 核心推理 |
| **容器化** | Docker + Docker Compose | 开发/部署环境 |

---

## 3. 目录结构（平台自身）

```
platform/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI 入口
│   │   ├── core/
│   │   │   ├── config.py            # 配置管理（环境变量）
│   │   │   ├── database.py          # 数据库连接
│   │   │   └── security.py          # CORS / 安全中间件
│   │   ├── models/                  # SQLAlchemy 模型
│   │   │   ├── __init__.py
│   │   │   ├── project.py
│   │   │   ├── agent_run.py
│   │   │   └── generated_file.py
│   │   ├── schemas/                 # Pydantic Schema
│   │   │   ├── __init__.py
│   │   │   ├── project.py
│   │   │   └── agent.py
│   │   ├── api/                     # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── projects.py          # /api/projects
│   │   │   ├── agent_runs.py        # /api/projects/{id}/runs
│   │   │   └── files.py             # /api/projects/{id}/files
│   │   ├── services/                # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py      # 流水线编排器
│   │   │   └── agent_runner.py      # Agent 调用封装
│   │   ├── agents/                  # Agent 实现
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # BaseAgent 基类
│   │   │   ├── requirement_agent.py
│   │   │   ├── backend_agent.py
│   │   │   ├── frontend_agent.py
│   │   │   └── test_agent.py
│   │   ├── tasks/                   # Celery 任务
│   │   │   ├── __init__.py
│   │   │   └── pipeline.py          # 流水线任务链
│   │   └── websocket/               # WebSocket 管理
│   │       ├── __init__.py
│   │       └── manager.py
│   ├── migrations/                  # Alembic
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                     # API Client
│   │   │   └── client.ts            # fetch 封装
│   │   ├── components/
│   │   │   ├── ui/                  # shadcn/ui
│   │   │   ├── RequirementInput.tsx
│   │   │   ├── PipelineProgress.tsx
│   │   │   ├── FileTree.tsx
│   │   │   ├── CodePreview.tsx
│   │   │   └── TestReport.tsx
│   │   ├── pages/
│   │   │   ├── HomePage.tsx         # 需求输入
│   │   │   ├── ProjectPage.tsx      # 进度/结果
│   │   │   └── HistoryPage.tsx      # 历史项目
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts      # WebSocket Hook
│   │   │   └── useProject.ts        # 项目状态 Hook
│   │   ├── lib/
│   │   │   └── utils.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```

---

## 4. API 接口定义

### 4.1 基础约定

```
Base URL:  http://localhost:8000/api/v1
Content-Type: application/json
WebSocket:  ws://localhost:8000/ws/projects/{project_id}
```

**通用响应格式**：

```json
// 成功
{
  "success": true,
  "data": { ... }
}

// 失败
{
  "success": false,
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "项目不存在"
  }
}
```

---

### 4.2 项目管理

#### `POST /api/v1/projects` — 创建项目（提交需求）

```
Request:
{
  "requirement": "string (required) — 自然语言需求",
  "template": "string | null — 'crud_admin' | 'rest_api' | 'dashboard'",
  "language": "string — 默认 'zh'",
  "constraints": {
    "database": "string — 默认 'sqlite'"
  }
}

Response (201):
{
  "success": true,
  "data": {
    "id": "uuid",
    "requirement": "我要做一个用户管理系统...",
    "status": "pending",
    "created_at": "2025-01-01T00:00:00Z",
    "progress": {
      "current_step": null,
      "steps": [
        {"name": "requirement", "label": "需求分析", "status": "pending"},
        {"name": "backend", "label": "生成后端", "status": "pending"},
        {"name": "frontend", "label": "生成前端", "status": "pending"},
        {"name": "test", "label": "运行测试", "status": "pending"}
      ]
    }
  }
}
```

#### `GET /api/v1/projects` — 项目列表

```
Query params:
  page: integer (default 1)
  page_size: integer (default 20, max 50)

Response (200):
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "summary": "用户管理系统",
        "status": "done",
        "created_at": "2025-01-01T00:00:00Z"
      }
    ],
    "total": 42,
    "page": 1,
    "page_size": 20
  }
}
```

#### `GET /api/v1/projects/{project_id}` — 项目详情

```
Response (200):
{
  "success": true,
  "data": {
    "id": "uuid",
    "requirement": "我要做一个用户管理系统...",
    "summary": "用户管理系统",
    "status": "done",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:05:00Z",
    "progress": {
      "current_step": "done",
      "steps": [
        {"name": "requirement", "label": "需求分析", "status": "completed", "duration_ms": 15000},
        {"name": "backend", "label": "生成后端", "status": "completed", "duration_ms": 120000},
        {"name": "frontend", "label": "生成前端", "status": "completed", "duration_ms": 90000},
        {"name": "test", "label": "运行测试", "status": "completed", "duration_ms": 45000}
      ]
    },
    "stats": {
      "total_files": 25,
      "backend_files": 12,
      "frontend_files": 8,
      "test_files": 5,
      "total_lines": 3200,
      "test_coverage": 87.5,
      "tests_passed": 42,
      "tests_failed": 0
    }
  }
}
```

#### `DELETE /api/v1/projects/{project_id}` — 删除项目

```
Response (200):
{
  "success": true,
  "data": null
}
```

---

### 4.3 Spec 相关

#### `GET /api/v1/projects/{project_id}/spec` — 获取需求分析的 Spec

```
Response (200):
{
  "success": true,
  "data": {
    "requirement_spec": { ... },   // RequirementSpec JSON
    "created_at": "..."
  }
}
```

#### `PUT /api/v1/projects/{project_id}/spec` — 修改 Spec（用户修正需求理解）

```
Request:
{
  "requirement_spec": { ... }  // 修改后的完整 RequirementSpec
}

Response (200):
{
  "success": true,
  "data": { "updated": true }
}
```

**交互流程**：Requirement Agent 先输出 Spec → 用户查看 → 如果理解有误，用户修改 Spec → 确认后触发后续流水线。

---

### 4.4 文件相关

#### `GET /api/v1/projects/{project_id}/files` — 获取文件树

```
Query params:
  type: string | null — 过滤: 'backend' | 'frontend' | 'test' | 'config'

Response (200):
{
  "success": true,
  "data": {
    "tree": [
      {
        "name": "backend",
        "type": "directory",
        "children": [
          {
            "name": "app",
            "type": "directory",
            "children": [
              {"name": "main.py", "type": "file", "size": 1024, "file_type": "config"},
              {"name": "models", "type": "directory", "children": [
                {"name": "user.py", "type": "file", "size": 2048, "file_type": "model"}
              ]}
            ]
          }
        ]
      }
    ]
  }
}
```

#### `GET /api/v1/projects/{project_id}/files/{file_path}` — 获取文件内容

```
file_path 为 URL 编码的相对路径，如 "backend%2Fapp%2Fmodels%2Fuser.py"

Response (200):
{
  "success": true,
  "data": {
    "path": "backend/app/models/user.py",
    "content": "from sqlalchemy import Column, Integer, String\n...",
    "language": "python",
    "size": 2048,
    "file_type": "model"
  }
}
```

#### `GET /api/v1/projects/{project_id}/download` — 下载 ZIP

```
Response (200):
Content-Type: application/zip
Content-Disposition: attachment; filename="user-management-system.zip"
```

---

### 4.5 Agent 运行记录

#### `GET /api/v1/projects/{project_id}/runs` — 获取 Agent 运行记录

```
Response (200):
{
  "success": true,
  "data": {
    "runs": [
      {
        "id": "uuid",
        "agent_name": "requirement",
        "status": "done",
        "started_at": "2025-01-01T00:00:00Z",
        "finished_at": "2025-01-01T00:00:15Z",
        "duration_ms": 15000,
        "error_message": null
      },
      {
        "id": "uuid",
        "agent_name": "backend",
        "status": "done",
        "started_at": "2025-01-01T00:00:15Z",
        "finished_at": "2025-01-01T00:02:15Z",
        "duration_ms": 120000,
        "error_message": null
      }
    ]
  }
}
```

---

### 4.6 WebSocket — 实时进度

#### `WS /ws/projects/{project_id}`

服务端推送的事件类型：

```json
// Step 开始
{
  "type": "step_started",
  "step": "backend",
  "label": "生成后端代码",
  "timestamp": "2025-01-01T00:00:15Z"
}

// Step 完成
{
  "type": "step_completed",
  "step": "backend",
  "label": "生成后端代码",
  "duration_ms": 120000,
  "summary": "已生成 12 个文件，5 个 API 端点",
  "timestamp": "2025-01-01T00:02:15Z"
}

// Step 失败
{
  "type": "step_failed",
  "step": "backend",
  "label": "生成后端代码",
  "error": "LLM API 超时",
  "retryable": true,
  "timestamp": "2025-01-01T00:02:15Z"
}

// Agent 日志（流式）
{
  "type": "agent_log",
  "step": "backend",
  "message": "正在生成 User 模型...",
  "level": "info",
  "timestamp": "2025-01-01T00:00:20Z"
}

// 流水线完成
{
  "type": "pipeline_completed",
  "project_id": "uuid",
  "stats": {
    "total_files": 25,
    "test_coverage": 87.5,
    "tests_passed": 42,
    "tests_failed": 0
  },
  "timestamp": "2025-01-01T00:05:00Z"
}

// 流水线失败
{
  "type": "pipeline_failed",
  "project_id": "uuid",
  "failed_step": "backend",
  "error": "...",
  "timestamp": "2025-01-01T00:05:00Z"
}
```

客户端连接：

```typescript
const ws = new WebSocket(`ws://localhost:8000/ws/projects/${projectId}`);
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // 根据 data.type 更新 UI
};
```

---

## 5. 数据库设计

### 5.1 ER 图

```
┌──────────────────┐       ┌──────────────────┐
│    projects      │       │   agent_runs     │
├──────────────────┤       ├──────────────────┤
│ id (PK)          │──┐    │ id (PK)          │
│ requirement      │  │    │ project_id (FK)  │──┐
│ template         │  │    │ agent_name       │  │
│ status           │  │    │ input_spec       │  │
│ summary          │  └───<│ output_result    │  │
│ requirement_spec │       │ status           │  │
│ created_at       │       │ error_message    │  │
│ updated_at       │       │ started_at       │  │
└──────────────────┘       │ finished_at      │  │
                           └──────────────────┘  │
                                                  │
                           ┌──────────────────┐   │
                           │ generated_files  │   │
                           ├──────────────────┤   │
                           │ id (PK)          │   │
                           │ project_id (FK)  │───┘
                           │ file_path        │
                           │ content          │
                           │ file_type        │
                           │ size_bytes       │
                           │ created_at       │
                           └──────────────────┘
```

### 5.2 DDL

```sql
-- 项目表
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requirement TEXT NOT NULL,                          -- 原始用户需求
    template VARCHAR(32),                               -- 'crud_admin' | 'rest_api' | 'dashboard'
    language VARCHAR(8) DEFAULT 'zh',                   -- 'zh' | 'en'
    status VARCHAR(32) DEFAULT 'pending',               -- 'pending' | 'analyzing' | 'generating_backend' | 'generating_frontend' | 'testing' | 'done' | 'failed'
    summary VARCHAR(500),                               -- 需求一句话概括
    requirement_spec JSONB,                             -- RequirementSpec JSON（需求分析完成后填充）
    constraints JSONB,                                  -- 用户约束（如 database 类型）
    stats JSONB,                                        -- 生成统计（完成后填充）
    error_message TEXT,                                 -- 流水线失败时的错误信息
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created_at ON projects(created_at DESC);

-- Agent 运行记录表
CREATE TABLE agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    agent_name VARCHAR(64) NOT NULL,                    -- 'requirement' | 'backend' | 'frontend' | 'test'
    input_spec JSONB,                                   -- 该 Agent 的输入 Spec
    output_result JSONB,                                -- 该 Agent 的输出 Result
    status VARCHAR(32) DEFAULT 'pending',               -- 'pending' | 'running' | 'done' | 'failed'
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_agent_runs_project ON agent_runs(project_id);
CREATE INDEX idx_agent_runs_status ON agent_runs(status);

-- 生成文件表
CREATE TABLE generated_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_path VARCHAR(512) NOT NULL,                    -- 相对路径，如 'backend/app/models/user.py'
    content TEXT NOT NULL,                              -- 文件内容
    file_type VARCHAR(32) NOT NULL,                     -- 'model' | 'schema' | 'service' | 'router' | 'config' | 'migration' | 'test' | 'docker' | 'doc' | 'page' | 'component' | 'hook' | 'api_client'
    size_bytes INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_generated_files_project ON generated_files(project_id);
CREATE INDEX idx_generated_files_type ON generated_files(file_type);
CREATE UNIQUE INDEX idx_generated_files_path ON generated_files(project_id, file_path);
```

### 5.3 状态机

```
projects.status 转换：

  pending
     │
     ▼
  analyzing          ← Requirement Agent 运行中
     │
     ├──→ failed     ← Requirement Agent 失败
     │
     ▼
  generating_backend ← Backend Agent 运行中
     │
     ├──→ failed     ← Backend Agent 失败
     │
     ▼
  generating_frontend← Frontend Agent 运行中
     │
     ├──→ failed     ← Frontend Agent 失败
     │
     ▼
  testing            ← Test Agent 运行中
     │
     ├──→ failed     ← Test Agent 失败
     │
     ▼
  done               ← 全部完成
```

---

## 6. 核心业务流程

### 6.1 创建项目 → 流水线执行

```
POST /api/v1/projects
     │
     ▼
创建 projects 记录 (status=pending)
     │
     ▼
Celery Task Chain:
  requirement_task
     │
     ├─ 成功 → requirement_spec 写入 DB + status=analyzing
     │         → WebSocket 推送 step_completed
     │         → 继续 backend_task
     │
     ├─ 失败 → status=failed + WebSocket 推送 step_failed
     │
     ▼
  backend_task
     │
     ├─ 成功 → 文件写入 generated_files + status=generating_backend
     │         → WebSocket 推送 step_completed
     │         → 继续 frontend_task
     │
     ├─ 失败 → status=failed
     │
     ▼
  frontend_task
     │
     ├─ 成功 → 文件写入 + status=generating_frontend
     │         → 继续 test_task
     │
     ├─ 失败 → status=failed
     │
     ▼
  test_task
     │
     ├─ 成功 → stats 写入 + status=done
     │         → WebSocket 推送 pipeline_completed
     │
     ├─ 失败 → status=failed + WebSocket 推送 pipeline_failed
```

### 6.2 用户修正 Spec 后重新生成

```
用户修改 RequirementSpec
     │
     ▼
PUT /api/v1/projects/{id}/spec
     │
     ▼
清除旧的 agent_runs + generated_files
     │
     ▼
从 Backend Agent 开始重新执行流水线
(status = generating_backend)
```

---

## 7. Agent 实现架构

### 7.1 BaseAgent 抽象

```python
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """所有 Agent 的基类"""
    
    agent_name: str
    
    @abstractmethod
    async def build_prompt(self, input_spec: dict) -> str:
        """根据输入 Spec 构建 LLM Prompt"""
        ...
    
    @abstractmethod
    async def parse_response(self, response: str) -> dict:
        """解析 LLM 响应为结构化输出"""
        ...
    
    async def run(self, input_spec: dict) -> dict:
        """执行 Agent"""
        prompt = await self.build_prompt(input_spec)
        response = await self.call_llm(prompt)
        result = await self.parse_response(response)
        return result
    
    async def call_llm(self, prompt: str) -> str:
        """调用 LLM API（Claude / GPT）"""
        ...
```

### 7.2 Orchestrator 编排器

```python
class Orchestrator:
    """流水线编排器"""
    
    def __init__(self, project_id: UUID):
        self.project_id = project_id
        self.ws_manager = WebSocketManager()
    
    async def run_pipeline(self, requirement: str) -> None:
        """执行完整流水线"""
        
        try:
            # Step 1: Requirement Agent
            await self.update_status("analyzing")
            await self.ws_manager.send(self.project_id, {
                "type": "step_started", "step": "requirement"
            })
            
            req_agent = RequirementAgent()
            req_result = await req_agent.run({"requirement": requirement})
            
            await self.save_spec(req_result)
            await self.ws_manager.send(self.project_id, {
                "type": "step_completed", "step": "requirement"
            })
            
            # Step 2: Backend Agent
            await self.update_status("generating_backend")
            backend_agent = BackendAgent()
            backend_result = await backend_agent.run(req_result)
            
            await self.save_files(backend_result["files"])
            
            # Step 3: Frontend Agent
            await self.update_status("generating_frontend")
            frontend_agent = FrontendAgent()
            frontend_result = await frontend_agent.run({
                "openapi_spec": backend_result["artifacts"]["openapi_spec"],
                "pages": req_result.get("pages", [])
            })
            
            await self.save_files(frontend_result["files"])
            
            # Step 4: Test Agent
            await self.update_status("testing")
            test_agent = TestAgent()
            test_result = await test_agent.run({
                "files": backend_result["files"] + frontend_result["files"],
                "spec": req_result
            })
            
            await self.save_files(test_result["files"])
            await self.save_stats(test_result["report"])
            await self.update_status("done")
            
        except Exception as e:
            await self.update_status("failed", error=str(e))
```

---

## 8. Docker 部署（开发环境）

```yaml
# docker-compose.yml (平台自身)
version: "3.9"

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ai_factory
      POSTGRES_USER: factory
      POSTGRES_PASSWORD: factory_dev
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://factory:factory_dev@db:5432/ai_factory
      REDIS_URL: redis://redis:6379/0
      LLM_API_KEY: ${LLM_API_KEY}
      LLM_PROVIDER: claude  # claude | openai
    volumes:
      - ./backend:/app
      - generated_files:/app/generated
    depends_on:
      - db
      - redis

  worker:
    build: ./backend
    command: celery -A app.tasks.pipeline worker --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://factory:factory_dev@db:5432/ai_factory
      REDIS_URL: redis://redis:6379/0
      LLM_API_KEY: ${LLM_API_KEY}
      LLM_PROVIDER: claude
    volumes:
      - ./backend:/app
      - generated_files:/app/generated
      - /var/run/docker.sock:/var/run/docker.sock  # 用于 Docker Sandbox 运行测试
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    command: npm run dev
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - api

volumes:
  pgdata:
  generated_files:
```

---

## 9. 环境变量

```bash
# .env (平台自身)
DATABASE_URL=postgresql+asyncpg://factory:factory_dev@localhost:5432/ai_factory
REDIS_URL=redis://localhost:6379/0
LLM_API_KEY=sk-ant-...
LLM_PROVIDER=claude              # claude | openai
LLM_MODEL=claude-sonnet-4-20250514
LLM_MAX_TOKENS=16000
LLM_TEMPERATURE=0.1
GENERATED_FILES_DIR=./generated  # 生成文件存储目录
MAX_CONCURRENT_PROJECTS=5        # 最大并发生成数
PROJECT_TIMEOUT_SECONDS=600      # 单项目超时时间
```

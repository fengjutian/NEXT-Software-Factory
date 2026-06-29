# AI Project Factory — MVP PRD

> **版本**: v0.1  
> **状态**: Draft  
> **MVP 目标**: 最小闭环流水线（需求 → 代码 → 测试），Web 平台形态，FastAPI + React 技术栈

---

## 1. 产品概述

### 1.1 一句话描述

一个 Web 平台，用户输入自然语言需求，系统自动生成 FastAPI 后端 + React 前端代码，并附带完整测试，形成「需求 → 代码 → 测试」的最小闭环。

### 1.2 MVP 要验证的核心假设

| 假设 | 验证方式 |
|---|---|
| AI 能从自然语言需求中提取足够结构化的信息来生成可用代码 | 给定 3 类标准需求模板，生成代码的可运行率 |
| Web 平台形态能降低使用门槛（相比 CLI） | 内部用户试用反馈 |
| 自动生成的测试能捕获回归问题 | 生成代码后人工注入 Bug，看测试是否发现 |
| 流水线编排（3 个 Agent 串行）的延迟在可接受范围内 | 端到端耗时 ≤ 5 分钟 |

### 1.3 MVP 明确不做的事

- ❌ 不接入 Code Wiki（那是 Phase 2 的事）
- ❌ 不支持多轮迭代修改（MVP 只有单次生成）
- ❌ 不支持 Git 仓库直接导入
- ❌ 不做部署/运维 Agent
- ❌ 不做多语言/多框架支持（只 FastAPI + React）
- ❌ 不做用户认证和权限系统
- ❌ 不做 Figma/设计稿导入

---

## 2. 用户与场景

### 2.1 目标用户

| 角色 | 场景 | 痛点 |
|---|---|---|
| **全栈开发者** | 快速搭建新项目的骨架 | 从零写 CRUD 重复劳动多 |
| **后端开发者** | 需要一个前端管理界面 | 不熟悉前端，想要开箱即用 |
| **产品经理/技术负责人** | 验证一个想法是否可行 | 没有开发资源做原型 |

### 2.2 核心用户旅程

```
用户打开 Web 平台
      │
      ▼
输入/粘贴自然语言需求
（例：「做一个用户管理系统，支持 CRUD 用户、角色分配、分页查询」）
      │
      ▼
点击「生成项目」
      │
      ▼
系统展示生成进度（流水线可视化）
  ├─ Step 1: 需求分析中...      (Requirement Agent)
  ├─ Step 2: 生成后端代码中...   (Backend Agent)
  └─ Step 3: 运行测试中...      (Test Agent)
      │
      ▼
展示结果页面：
  ├─ 项目文件树（可在线预览）
  ├─ 测试报告（通过/失败）
  ├─ API 文档（自动生成的 Swagger）
  └─ 下载项目 ZIP / 一键推送 GitHub
```

---

## 3. 功能需求

### 3.1 需求输入模块

| ID | 功能 | 优先级 | 说明 |
|---|---|---|---|
| F-01 | 自然语言需求输入框 | P0 | 支持中英文，最大 2000 字 |
| F-02 | 需求模板选择 | P1 | 预设模板（CRUD 管理后台、REST API 服务、数据看板），降低输入门槛 |
| F-03 | 需求示例一键填充 | P2 | 「试试这个例子」按钮 |

### 3.1.1 设计规范输入模块 🆕

| ID | 功能 | 优先级 | 说明 |
|---|---|---|---|
| F-04 | 设计预设选择 | P0 | 提供 3 套预设：企业蓝 / 自然绿 / 暗夜模式，默认选中企业蓝 |
| F-05 | 图标上传（Logo） | P1 | 支持 SVG/PNG，≤500KB，上传后预览 |
| F-06 | 图标上传（Favicon） | P1 | 支持 ICO/PNG，≤100KB |
| F-07 | 自定义主色调 | P1 | Color Picker，选择后实时预览 |
| F-08 | 字体选择 | P1 | 从 Google Fonts 列表选择，默认 Inter |
| F-09 | 设计 Token 实时预览 | P1 | 修改选项时右侧预览面板同步更新 |

### 3.2 Requirement Agent（需求分析）

| ID | 功能 | 优先级 | 说明 |
|---|---|---|---|
| F-10 | 解析需求为结构化 Spec | P0 | 输出：实体列表、字段、关系、API 端点列表、页面列表 |
| F-11 | 输出用户可审阅的 Spec 卡片 | P0 | 用户可以在生成代码前看到 AI 对需求的理解，确认或修正 |
| F-12 | Spec 手动编辑 | P1 | 用户可以修改 AI 解析出的实体/字段/端点 |

### 3.3 Backend Agent（后端代码生成）

| ID | 功能 | 优先级 | 说明 |
|---|---|---|---|
| F-20 | 生成 FastAPI 项目骨架 | P0 | 包括：路由、模型、Schema、CRUD 服务 |
| F-21 | 自动生成数据库 Migration | P0 | 使用 Alembic，SQLite（开发）/ PostgreSQL（生产）|
| F-22 | 自动生成 Swagger/OpenAPI 文档 | P0 | FastAPI 自带，确保完整 |
| F-23 | 生成 Dockerfile + docker-compose | P1 | 一键启动后端 + 数据库 |
| F-24 | 生成 .env 配置模板 | P2 | |

### 3.4 Frontend Agent（前端代码生成）

| ID | 功能 | 优先级 | 说明 |
|---|---|---|---|
| F-30 | 基于 OpenAPI 生成 React + TypeScript 项目 | P0 | 使用 Vite 构建 |
| F-31 | 自动生成 API Client（TanStack Query / fetch）| P0 | 类型安全 |
| F-32 | 自动生成 CRUD 页面 | P0 | 列表页 + 创建/编辑表单 |
| F-33 | 自动生成路由配置 | P0 | React Router |
| F-34 | 生成基础 UI 组件 | P1 | 表格、表单、分页、Modal（基于 shadcn/ui）|

### 3.5 Review Agent（代码质检）🆕

| ID | 功能 | 优先级 | 说明 |
|---|---|---|---|
| F-35 | 代码语法检查 | P0 | Python AST / TypeScript tsc --noEmit |
| F-36 | Lint 检查 | P0 | Ruff (Python) + ESLint (TypeScript) |
| F-37 | 类型检查 | P0 | mypy --strict / tsc strict |
| F-38 | 安全扫描 | P0 | 硬编码密钥、SQL 注入、XSS 检测 |
| F-39 | 代码风格审查 | P1 | 圈复杂度、行数、文档字符串 |
| F-39a | 红线违反自动驳回 | P0 | CRITICAL 违规自动触发 Agent 重新生成 |

### 3.6 Test Agent（测试生成）

| ID | 功能 | 优先级 | 说明 |
|---|---|---|---|
| F-40 | 后端单元测试（pytest）| P0 | 覆盖所有 API 端点 |
| F-41 | 后端集成测试 | P1 | 测试数据库交互 |
| F-42 | 前端组件测试（Vitest）| P1 | 覆盖核心组件 |
| F-43 | 生成测试报告 | P0 | 展示通过/失败/覆盖率 |
| F-44 | Docker Sandbox 执行 | P0 | 在隔离容器中运行测试 |

### 3.7 Documentation Agent（文档生成）🆕

| ID | 功能 | 优先级 | 说明 |
|---|---|---|---|
| F-45 | README.md 生成 | P0 | 项目总览 + 快速启动 + 技术栈 |
| F-46 | API 文档生成 | P0 | 基于 OpenAPI Spec，含 curl 示例 |
| F-47 | 数据库文档生成 | P1 | ER 图 (Mermaid) + 表结构 + 索引 |
| F-48 | 架构图生成 | P1 | Mermaid 架构图 + 模块依赖 |
| F-49 | 部署文档生成 | P1 | Docker + 环境变量 + CI/CD Workflow |

### 3.8 错误处理与恢复 🆕

| ID | 功能 | 优先级 | 说明 |
|---|---|---|---|
| F-55 | Agent 失败自动重试 | P0 | E0 瞬时错误重试 3 次，E1 可恢复错误重试 1 次 |
| F-56 | 流水线降级执行 | P0 | 上游部分失败时下游按 manifest 适配，不整体终止 |
| F-57 | 中间产物保留 | P0 | 即使流水线失败，保留已完成步骤的产物供下载 |
| F-58 | 错误分类与用户通知 | P0 | 通过 WebSocket 推送错误级别和重试状态 |

### 3.9 结果展示与交付

| ID | 功能 | 优先级 | 说明 |
|---|---|---|---|
| F-50 | 在线代码预览（文件树 + 语法高亮）| P0 | |
| F-51 | API 文档在线预览（Swagger UI）| P0 | |
| F-52 | 测试报告可视化 | P0 | |
| F-53 | 下载 ZIP | P0 | |
| F-54 | 一键创建 GitHub 仓库并推送 | P2 | |

### 3.7 流水线可视化

| ID | 功能 | 优先级 | 说明 |
|---|---|---|---|
| F-60 | 展示当前进度（3 步流水线）| P0 | 实时 WebSocket 推送 |
| F-61 | 每步完成后展示中间产物 | P1 | 例如需求分析完成后展示 Spec |
| F-62 | 流水线失败时展示错误信息 | P0 | 并允许重试 |

---

## 4. 非功能需求

| ID | 需求 | 目标值 |
|---|---|---|
| NF-01 | 端到端生成时间 | ≤ 5 分钟（P50），≤ 10 分钟（P95）|
| NF-02 | 生成代码可运行率 | ≥ 80%（首次生成即可 `docker-compose up` 跑通）|
| NF-03 | 后端测试覆盖率 | ≥ 80% |
| NF-04 | API 响应（Web 平台自身）| 页面加载 ≤ 2 秒 |
| NF-05 | 并发生成任务数 | MVP 支持 5 个并发 |

---

## 5. 系统架构（MVP）

```
┌─────────────────────────────────────────────────────────┐
│                    Web Frontend (React)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ 需求输入  │  │ 进度展示  │  │ 代码预览  │  │ 结果页  │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP + WebSocket
┌──────────────────────┴──────────────────────────────────┐
│                  API Server (FastAPI)                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │               Orchestrator (流水线编排)            │   │
│  │                                                    │   │
│  │  Requirement Agent → Backend Agent → Test Agent    │   │
│  │                                                    │   │
│  │  每个 Agent 调用 LLM (Claude / GPT-4)              │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐    │
│  │ 任务队列  │  │ 文件存储  │  │ 生成历史/会话管理   │    │
│  │ (Redis)  │  │ (本地/S3) │  │ (PostgreSQL)       │    │
│  └──────────┘  └──────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 5.1 Agent 通信协议

每个 Agent 接收一个 **结构化 JSON Spec**，输出一组文件 + 结构化结果：

```json
// Agent 输入 (以 Backend Agent 为例)
{
  "project_id": "abc123",
  "spec": {
    "entities": [
      {
        "name": "User",
        "fields": [
          {"name": "username", "type": "string", "required": true, "unique": true},
          {"name": "email", "type": "string", "required": true},
          {"name": "role", "type": "enum", "values": ["admin", "editor", "viewer"]}
        ]
      }
    ],
    "relationships": [
      {"from": "User", "to": "Role", "type": "many_to_one"}
    ],
    "api_endpoints": [
      {"method": "GET", "path": "/users", "description": "分页查询用户列表"},
      {"method": "POST", "path": "/users", "description": "创建用户"},
      {"method": "PUT", "path": "/users/{id}", "description": "更新用户"},
      {"method": "DELETE", "path": "/users/{id}", "description": "删除用户"}
    ]
  }
}

// Agent 输出
{
  "status": "success",
  "files": [
    {"path": "app/models/user.py", "content": "..."},
    {"path": "app/schemas/user.py", "content": "..."},
    ...
  ],
  "artifacts": {
    "openapi_spec": "{...}",
    "test_report": "{...}"
  }
}
```

### 5.2 流水线编排

```
用户需求 (自然语言)
      │
      ▼
┌─────────────────┐
│ Requirement     │  输入: 自然语言
│ Agent           │  输出: Structured Spec (JSON)
└────────┬────────┘
         │ Structured Spec
         ▼
┌─────────────────┐
│ Backend Agent   │  输入: Spec.entities + Spec.api_endpoints
│                 │  输出: FastAPI 项目文件 + OpenAPI Spec
└────────┬────────┘
         │ OpenAPI Spec
         ▼
┌─────────────────┐
│ Frontend Agent  │  输入: OpenAPI Spec
│                 │  输出: React 项目文件
└────────┬────────┘
         │ 所有文件
         ▼
┌─────────────────┐
│ Test Agent      │  输入: 项目文件 + Spec
│                 │  输出: 测试代码 + 测试报告
└────────┬────────┘
         │
         ▼
      结果展示
```

---

## 6. 技术栈

| 层级 | 技术 | 选型理由 |
|---|---|---|
| **平台前端** | React 18 + TypeScript + Vite | 与生成目标技术栈一致 |
| **平台后端** | FastAPI + Python 3.11+ | 与生成目标技术栈一致，异步支持好 |
| **数据库** | PostgreSQL | 存储项目历史、用户会话 |
| **任务队列** | Celery + Redis / Arq | 异步执行 Agent 流水线 |
| **实时通信** | WebSocket (FastAPI 内置) | 推送流水线进度 |
| **LLM** | Claude API (主力) + GPT-4 (备选) | Claude 在代码生成方面表现最好 |
| **代码沙箱** | Docker 临时容器 | 安全执行生成的测试代码 |
| **文件存储** | 本地文件系统 (MVP) / S3 (未来) | |
| **生成的代码栈** | FastAPI + SQLAlchemy + Alembic + React + shadcn/ui | MVP 统一技术栈 |

---

## 7. 数据模型（平台自身）

```sql
-- 项目
projects (
  id UUID PRIMARY KEY,
  user_requirement TEXT NOT NULL,
  status ENUM('pending', 'analyzing', 'generating_backend', 'generating_frontend', 'testing', 'done', 'failed'),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- Agent 执行记录
agent_runs (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  agent_name VARCHAR(64),       -- 'requirement', 'backend', 'frontend', 'test'
  input_spec JSONB,
  output_result JSONB,
  status ENUM('pending', 'running', 'done', 'failed'),
  started_at TIMESTAMP,
  finished_at TIMESTAMP,
  error_message TEXT
)

-- 生成的文件
generated_files (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  file_path VARCHAR(512),
  content TEXT,
  file_type ENUM('backend', 'frontend', 'test', 'config', 'doc')
)
```

---

## 8. UI 草图（关键页面）

### 8.1 首页 — 需求输入

```
┌──────────────────────────────────────────────────────┐
│  🏭 AI Project Factory                                │
│                                                       │
│  用自然语言描述你想要的项目，AI 自动生成完整代码        │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │                                                   │  │
│  │  我要做一个用户管理系统，支持：                      │  │
│  │  - 用户的增删改查                                  │  │
│  │  - 角色管理（管理员、编辑、查看者）                  │  │
│  │  - 分页查询和搜索                                  │  │
│  │                                                   │  │
│  └─────────────────────────────────────────────────┘  │
│                                                       │
│  模板: [CRUD管理后台] [REST API服务] [数据看板]        │
│                                                       │
│  [✨ 生成项目]                                        │
└──────────────────────────────────────────────────────┘
```

### 8.2 进度页 — 流水线可视化

```
┌──────────────────────────────────────────────────────┐
│  生成进度                                              │
│                                                       │
│  ✅ 需求分析完成                    [查看 Spec]        │
│  ⏳ 生成后端代码中...                                  │
│  ⬜ 生成前端代码                                       │
│  ⬜ 运行测试                                          │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │ Backend Agent 日志:                              │  │
│  │ ✓ 生成数据模型 User, Role                        │  │
│  │ ✓ 生成 API 端点 GET /users, POST /users ...     │  │
│  │ ✓ 生成数据库 Migration                           │  │
│  │ ⏳ 生成 Service 层...                            │  │
│  └─────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### 8.3 结果页

```
┌──────────────────────────────────────────────────────┐
│  ✅ 项目生成完成！                                     │
│                                                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐              │
│  │ 12       │  │ 95%     │  │ 8/8     │              │
│  │ 文件     │  │ 测试覆盖 │  │ 测试通过 │              │
│  └─────────┘  └─────────┘  └─────────┘              │
│                                                       │
│  📁 文件树                    📄 代码预览              │
│  ├── backend/                 ┌─────────────────┐    │
│  │   ├── app/                 │ # app/main.py   │    │
│  │   │   ├── models/          │                 │    │
│  │   │   ├── schemas/         │ from fastapi    │    │
│  │   │   ├── services/        │ import ...      │    │
│  │   │   └── main.py          │                 │    │
│  │   └── tests/               └─────────────────┘    │
│  ├── frontend/                                        │
│  └── docker-compose.yml                               │
│                                                       │
│  [📥 下载 ZIP]  [🔗 推送到 GitHub]  [📋 复制 API 文档] │
└──────────────────────────────────────────────────────┘
```

---

## 9. 开发阶段

### Phase 0：项目脚手架（Week 1）

- 初始化 FastAPI 项目 + React 项目（平台自身）
- 搭建数据库 + 迁移
- Docker 开发环境
- CI/CD（GitHub Actions）

### Phase 1：Requirement Agent（Week 2-3）

- Prompt 工程：自然语言 → Structured Spec
- Spec 审阅/编辑 UI
- 预设模板（CRUD、API 服务、数据看板）

### Phase 2：Backend Agent（Week 3-5）

- Prompt 工程：Structured Spec → FastAPI 代码
- 代码模板系统（Model/Service/Router/Schema）
- 文件输出 + 存储

### Phase 3：Frontend Agent（Week 5-7）

- Prompt 工程：OpenAPI Spec → React 代码
- 组件模板系统（Table/Form/Modal）
- 文件输出 + 存储

### Phase 4：Test Agent + 编排（Week 7-8）

- 后端测试自动生成（pytest）
- 前端测试自动生成（Vitest）
- 流水线编排（Celery 任务链）
- WebSocket 实时进度推送

### Phase 5：结果展示 + 交付（Week 8-9）

- 文件树 + 代码预览
- 测试报告可视化
- ZIP 下载
- 结果页完整 UI

### Phase 6：内测 + 打磨（Week 9-10）

- 内部用户试用
- 修复核心 Bug
- 优化 Prompt（针对 3 个模板）

---

## 10. 成功指标

| 指标 | 目标 | 测量方式 |
|---|---|---|
| 端到端生成成功率 | ≥ 85% | 100 次生成中成功完成的次数 |
| 生成代码可运行率 | ≥ 80% | 生成后 `docker-compose up` 一次跑通的比率 |
| 测试覆盖率 | ≥ 80% | pytest-cov 报告 |
| 用户满意度 NPS | ≥ 30 | 内部用户问卷 |
| 从输入需求到看到结果的时长 | ≤ 5 min (P50) | 监控埋点 |

---

## 附录 A：MVP 需求模板

### 模板 1：CRUD 管理后台

```
我要做一个 [实体名称] 管理系统，支持：
- [实体] 的增删改查
- 字段：name, email, ...
- 分页查询
- 搜索功能
```

### 模板 2：REST API 服务

```
我要做一个 [服务名称] API，提供以下端点：
- GET /items - 列表查询
- POST /items - 创建
- PUT /items/{id} - 更新
- DELETE /items/{id} - 删除
```

### 模板 3：数据看板

```
我要做一个 [业务] 数据看板，展示：
- 总览统计卡片
- 数据趋势图
- 分类饼图
- 最近数据表格
```

---

## 附录 B：项目文件结构（生成产物）

```
project-output/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy 模型
│   │   │   ├── __init__.py
│   │   │   └── user.py
│   │   ├── schemas/         # Pydantic Schema
│   │   │   ├── __init__.py
│   │   │   └── user.py
│   │   ├── services/        # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   └── user_service.py
│   │   ├── api/             # 路由
│   │   │   ├── __init__.py
│   │   │   └── users.py
│   │   ├── core/            # 配置/数据库连接
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   └── main.py
│   ├── migrations/          # Alembic
│   ├── tests/
│   │   ├── test_users.py
│   │   └── conftest.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # API Client
│   │   ├── components/      # UI 组件
│   │   ├── pages/           # 页面
│   │   ├── hooks/           # 自定义 Hooks
│   │   └── App.tsx
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

# 🏭 AI Project Factory

> 用自然语言描述需求，AI 自动生成完整项目代码——需求分析 → 后端 → 前端 → 测试 → 文档，全流程自动化。

---

## ✨ 是什么

AI Project Factory 是一套 **AI 驱动的软件生产流水线**。你输入一句话需求，它自动完成：

```
"我要做一个用户管理系统"
        │
        ▼
  ✅ 需求分析 → 实体、API、页面设计
  ✅ 后端代码 → FastAPI + SQLAlchemy + PostgreSQL
  ✅ 前端代码 → React + TypeScript + Tailwind CSS
  ✅ 代码质检 → Lint + 安全扫描
  ✅ 自动测试 → pytest + Vitest
  ✅ 文档生成 → README + API + 数据库 + 架构 + 部署
        │
        ▼
    📦 下载 ZIP，一键部署
```

---

## 🚀 快速启动

### 前置要求

- Docker & Docker Compose v2
- Anthropic API Key（或 OpenAI）

### 1. 克隆项目

```bash
git clone https://github.com/your-org/ai-project-factory.git
cd ai-project-factory
```

### 2. 配置环境变量

```bash
cp platform/backend/.env.example platform/backend/.env
# 编辑 .env，填入你的 LLM_API_KEY
```

### 3. 一键启动

```bash
cd platform
docker compose up -d
```

### 4. 打开浏览器

- 前端：http://localhost:5173
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/health

---

## 🏗️ 技术栈

| 层级 | 技术 |
|---|---|
| **平台后端** | FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis + Celery |
| **平台前端** | React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui |
| **LLM** | Claude (Anthropic) / GPT (OpenAI) |
| **生成后端** | FastAPI + SQLAlchemy + Alembic + pytest |
| **生成前端** | React + TypeScript + Vite + Tailwind CSS + Vitest |
| **基础设施** | Docker Compose + Nginx |

---

## 📖 文档

完整设计文档在 `docs/` 目录：

| 文档 | 内容 |
|---|---|
| [`prd-mvp.md`](docs/prd-mvp.md) | 产品定义、功能需求、里程碑 |
| [`agent-protocol.md`](docs/agent-protocol.md) | Agent 通信协议、Completion Manifest |
| [`platform-architecture.md`](docs/platform-architecture.md) | 系统架构、API、数据库设计 |
| [`frontend-design.md`](docs/frontend-design.md) | 前端页面详细设计 |
| [`design-system.md`](docs/design-system.md) | 设计规范 (Design Token) |
| [`prompt-engineering.md`](docs/prompt-engineering.md) | Agent Prompt 工程规范 |
| [`testing-strategy.md`](docs/testing-strategy.md) | 测试策略与 CI/CD |
| [`error-handling.md`](docs/error-handling.md) | 错误处理与恢复策略 |
| [`code-quality.md`](docs/code-quality.md) | 代码质量标准 |
| [`documentation-agent.md`](docs/documentation-agent.md) | 文档自动生成规范 |

---

## 🧩 架构

```
┌──────────────────────────────────────────────┐
│               Web Frontend (React)            │
│  需求输入 → 进度展示 → 代码预览 → 下载        │
└──────────────────┬───────────────────────────┘
                   │ HTTP + WebSocket
┌──────────────────┴───────────────────────────┐
│              API Server (FastAPI)             │
│                                               │
│  ┌─────────────────────────────────────────┐ │
│  │          Orchestrator (流水线)           │ │
│  │                                          │ │
│  │  Requirement → Backend → Frontend        │ │
│  │       → Review → Test → Documentation   │ │
│  └─────────────────────────────────────────┘ │
│                                               │
│  PostgreSQL + Redis + Celery                  │
└──────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
├── docs/                     # 10 份设计文档
├── platform/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── agents/       # 6 个 Agent (Requirement/Backend/Frontend/Review/Test/Documentation)
│   │   │   ├── api/          # REST API 端点
│   │   │   ├── services/     # Orchestrator 流水线编排
│   │   │   ├── models/       # SQLAlchemy 数据模型
│   │   │   ├── schemas/      # Pydantic 验证
│   │   │   └── websocket/    # WebSocket 实时推送
│   │   ├── migrations/       # Alembic 迁移
│   │   └── tests/            # pytest 测试
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── pages/        # HomePage / ProjectPage / HistoryPage
│   │   │   ├── components/   # PipelineProgress / FileTree / CodePreview / etc.
│   │   │   ├── hooks/        # useWebSocket / useProject
│   │   │   └── api/          # 类型安全 API Client
│   │   └── public/
│   └── docker-compose.yml    # 5 个服务
```

---

## 🔧 开发

### 后端

```bash
cd platform/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端

```bash
cd platform/frontend
npm install
npm run dev
```

### 测试

```bash
# 后端
cd platform/backend
pytest

# 前端
cd platform/frontend
npx vitest run
```

---

## 📄 许可证

MIT

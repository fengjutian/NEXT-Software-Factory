# 前端页面详细设计 v0.1

> 本文档定义 AI Project Factory **Web 平台自身**的前端页面设计。  
> 每个页面覆盖：组件树、状态矩阵（加载/空/错误/边界）、交互流程、数据依赖。  
> UI 组件库：shadcn/ui + Tailwind CSS。

---

## 1. 信息架构

```
/                          → 首页（需求输入）
/projects/:id              → 项目详情（进度 + 结果）
/history                   → 历史项目列表
```

3 个路由，SPA 单页应用。

---

## 2. 全局布局

```
┌──────────────────────────────────────────────────────┐
│  Header                                                │
│  ┌────────────────────────────────────────────────┐   │
│  │ 🏭 AI Factory    [首页] [历史]    [GitHub ⭐]  │   │
│  └────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Main Content (动态区域)                               │
│                                                       │
├──────────────────────────────────────────────────────┤
│  Footer                                                │
│  └─ © 2025 AI Project Factory · Powered by Claude     │
└──────────────────────────────────────────────────────┘
```

### 2.1 Header 组件

```typescript
// 组件：<Header />
// 状态：无状态组件，纯展示 + 导航

interface HeaderProps {
  // 无 props，从 router 读取当前路径高亮导航
}

// 导航项
const navItems = [
  { label: "首页", href: "/", icon: Home },
  { label: "历史", href: "/history", icon: Clock },
];
```

**行为**：
- 当前页面导航项高亮（`text-primary` + 下划线）
- 右侧 GitHub 图标链接到开源仓库（新窗口打开）
- 移动端：导航收缩为汉堡菜单

---

## 3. 首页 `/` — 需求输入

### 3.1 页面布局

```
┌──────────────────────────────────────────────────────┐
│                                                       │
│          🏭 AI Project Factory                        │
│          用自然语言描述需求，AI 自动生成完整项目         │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │  [模板选择: CRUD管理后台 ▾]                       │  │
│  ├─────────────────────────────────────────────────┤  │
│  │                                                   │  │
│  │  我要做一个用户管理系统，支持：                      │  │
│  │  - 用户的增删改查                                  │  │
│  │  - 角色管理（管理员、编辑、查看者）                  │  │
│  │  - 分页查询和搜索                                  │  │
│  │                                                   │  │
│  └─────────────────────────────────────────────────┘  │
│  字数: 56 / 2000                                      │
│                                                       │
│  ┌──────────────────────────────────────────────┐     │
│  │ 🎨 设计规范                        [展开 ▾]   │     │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐       │     │
│  │ │ ████     │ │ ████     │ │ ████     │       │     │
│  │ │ 企业蓝   │ │ 自然绿   │ │ 暗夜模式  │       │     │
│  │ │ ✓ 选中   │ │          │ │          │       │     │
│  │ └──────────┘ └──────────┘ └──────────┘       │     │
│  │ [自定义规范 ▸]                                 │     │
│  └──────────────────────────────────────────────┘     │
│                                                       │
│  ┌──────────────────────────────────────────────┐     │
│  │ 高级选项                           [展开 ▾]   │     │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │     │
│  │ │ 数据库    │ │ 目标框架  │ │ 前端框架     │  │     │
│  │ │ SQLite ▾ │ │ FastAPI  │ │ React        │  │     │
│  │ └──────────┘ └──────────┘ └──────────────┘  │     │
│  └──────────────────────────────────────────────┘     │
│                                                       │
│  ┌──────────────────────────────────────────────┐     │
│  │                   ✨ 生成项目                   │     │
│  └──────────────────────────────────────────────┘     │
│                                                       │
│  ───────────── 或者试试这些例子 ─────────────          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                 │
│  │ 📋      │ │ 🔌      │ │ 📊      │                 │
│  │ 用户管理 │ │ 博客API │ │ 销售看板 │                 │
│  │ 系统    │ │ 服务    │ │         │                 │
│  └─────────┘ └─────────┘ └─────────┘                 │
└──────────────────────────────────────────────────────┘
```

### 3.2 组件树

```
<HomePage>
  ├── <HeroSection>
  │     ├── <h1> + <p> (标题 + 副标题)
  │     └── <TemplateSelector>         // 模板下拉框
  ├── <RequirementInput>
  │     ├── <Textarea>                 // 需求输入框（核心）
  │     └── <CharCounter>              // 字数统计
  ├── <DesignSpecSelector>             // 🆕 设计规范选择器
  │     ├── <PresetCards>              // 预设卡片（企业蓝/自然绿/暗夜）
  │     └── <CustomDesignPanel>        // 自定义面板（折叠）
  │           ├── <FileUpload> (Logo)
  │           ├── <FileUpload> (Favicon)
  │           ├── <ColorPicker> (主色调)
  │           ├── <FontSelector> (字体)
  │           ├── <RadiusSlider> (圆角)
  │           └── <DesignPreview>      // 实时预览
  ├── <AdvancedOptions>                // 高级选项（折叠面板）
  │     ├── <Select> (数据库)
  │     ├── <Select> (后端框架, MVP 禁用)
  │     └── <Select> (前端框架, MVP 禁用)
  ├── <SubmitButton>                   // 生成项目按钮
  └── <ExampleCards>                   // 示例卡片
        └── <ExampleCard> × 3
```

### 3.3 状态矩阵

| 状态 | 条件 | 表现 |
|---|---|---|
| **默认态** | 页面初始加载 | 空输入框，光标聚焦在 textarea，模板默认选中「CRUD 管理后台」 |
| **输入中** | 用户正在输入 | 实时字数统计，≥10 字时「生成项目」按钮从 disabled → enabled |
| **验证错误** | 输入为空 / 超过 2000 字 | textarea 边框变红 + 下方显示错误提示：「请输入至少 10 个字」/「已超过 2000 字限制」 |
| **提交中** | 点击生成后，等待 API 响应 | 按钮显示 Loading spinner + 「正在分析需求...」，输入框 disabled |
| **提交失败** | API 返回错误 | Toast 提示：「生成失败：{错误原因}」，按钮恢复可点击 |
| **提交成功** | 201 Created | 自动跳转到 `/projects/:id` |

### 3.4 交互流程

```
用户选择模板 (可选)
      │
      ▼
用户输入需求文字
      │ 实时校验：字数 ≥ 10
      ▼
「生成项目」按钮变为可用
      │
      ▼
点击「生成项目」
      │
      ├─→ 前端 POST /api/v1/projects
      │
      ├─→ 成功 → router.push(`/projects/${id}`)
      │
      └─→ 失败 → Toast 错误提示
```

### 3.5 数据依赖

| 操作 | API | 请求体 |
|---|---|---|
| 创建项目 | `POST /api/v1/projects` | `{ requirement, template, constraints }` |

---

## 4. 项目详情页 `/projects/:id` — 进度 + 结果

这是最复杂的页面，有三种核心状态：**运行中 / 完成 / 失败**。

### 4.1 状态 1：流水线运行中

```
┌──────────────────────────────────────────────────────┐
│  ← 返回首页                                           │
│                                                       │
│  用户管理系统                          创建于 2 分钟前  │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │  流水线进度                                       │  │
│  │                                                  │  │
│  │  ✅ 需求分析                   15s      [查看]   │  │
│  │  ⏳ 生成后端代码               进行中...          │  │
│  │  ⬜ 生成前端代码                                   │  │
│  │  ⬜ 运行测试                                       │  │
│  │                                                  │  │
│  │  ┌──────────────────────────────────────────┐    │  │
│  │  │ Backend Agent 实时日志:                    │    │  │
│  │  │ [15s] ✓ 解析需求完成: 1 个实体, 5 个端点  │    │  │
│  │  │ [16s] ⏳ 正在生成 User 模型...            │    │  │
│  │  │ [18s] ✓ User 模型生成完成                │    │  │
│  │  │ [19s] ⏳ 正在生成 API 端点...            │    │  │
│  │  └──────────────────────────────────────────┘    │  │
│  └─────────────────────────────────────────────────┘  │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │  📋 需求分析结果（已完成）                  [展开] │  │
│  │  ┌──────────────────────────────────────────┐    │  │
│  │  │ 实体: User (5 个字段)                     │    │  │
│  │  │ 端点: GET /users, POST /users, ...       │    │  │
│  │  │ 页面: 列表页, 创建页, 编辑页, 详情页      │    │  │
│  │  └──────────────────────────────────────────┘    │  │
│  └─────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### 4.2 状态 2：生成完成

```
┌──────────────────────────────────────────────────────┐
│  ← 返回首页                                           │
│                                                       │
│  ✅ 项目生成完成！                     耗时 4 分 32 秒  │
│                                                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐  │
│  │   25     │ │   87%    │ │  42/42  │ │  3,200  │  │
│  │ 生成文件  │ │ 测试覆盖  │ │ 测试通过  │ │ 代码行数  │  │
│  └──────────┘ └──────────┘ └──────────┘ └─────────┘  │
│                                                       │
│  ┌─────────────────┐ ┌─────────────────────────────┐  │
│  │  📁 文件树       │ │  📄 代码预览                 │  │
│  │                 │ │                              │  │
│  │ ├─ backend/     │ │ 1│from fastapi import        │  │
│  │ │  ├─ app/      │ │ 2│    FastAPI, HTTPException │  │
│  │ │  │  ├─ models/│ │ 3│from sqlalchemy.orm        │  │
│  │ │  │  ├─ schema/│ │ 4│    import Session         │  │
│  │ │  │  ├─ service│ │ 5│                           │  │
│  │ │  │  ├─ api/   │ │ 6│app = FastAPI(             │  │
│  │ │  │  └─ core/  │ │ 7│    title="用户管理系统"    │  │
│  │ │  ├─ tests/    │ │ 8│)                          │  │
│  │ │  └─ Dockerfile│ │                              │  │
│  │ ├─ frontend/    │ │  [Python, 共 120 行]         │  │
│  │ └─ docker-...   │ │                              │  │
│  └─────────────────┘ └─────────────────────────────┘  │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │  📊 测试报告                          [详细报告]  │  │
│  │  ┌──────────────────────────────────────────┐    │  │
│  │  │ 后端测试: ████████████████████ 24/24 ✓   │    │  │
│  │  │ 前端测试: ████████████████████ 18/18 ✓   │    │  │
│  │  │ 覆盖率:   87.5%                            │    │  │
│  │  └──────────────────────────────────────────┘    │  │
│  └─────────────────────────────────────────────────┘  │
│                                                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ 📥 下载ZIP│ │ 🔗 GitHub│ │ 📋 复制API│              │
│  └──────────┘ └──────────┘ └──────────┘              │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │  🔌 API 文档 (Swagger)                           │  │
│  │  ┌──────────────────────────────────────────┐    │  │
│  │  │ GET    /users        查询用户列表         │    │  │
│  │  │ POST   /users        创建用户             │    │  │
│  │  │ GET    /users/{id}   获取用户详情         │    │  │
│  │  │ PUT    /users/{id}   更新用户             │    │  │
│  │  │ DELETE /users/{id}   删除用户             │    │  │
│  │  └──────────────────────────────────────────┘    │  │
│  └─────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### 4.3 状态 3：生成失败

```
┌──────────────────────────────────────────────────────┐
│  ← 返回首页                                           │
│                                                       │
│  ❌ 生成失败                                            │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │  流水线进度                                       │  │
│  │  ✅ 需求分析                       15s           │  │
│  │  ❌ 生成后端代码                   失败            │  │
│  │  ⬜ 生成前端代码                    已跳过          │  │
│  │  ⬜ 运行测试                        已跳过          │  │
│  └─────────────────────────────────────────────────┘  │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │  ⚠️ 错误详情                                     │  │
│  │                                                  │  │
│  │  Backend Agent 执行失败                          │  │
│  │  LLM API 调用超时（超过 120 秒未响应）             │  │
│  │                                                  │  │
│  │  [🔄 重试]  [📝 修改需求]                        │  │
│  └─────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### 4.4 组件树

```
<ProjectPage>
  ├── <BackButton>                      // 返回首页
  ├── <ProjectHeader>
  │     ├── <StatusBadge>               // 状态标签：运行中/完成/失败
  │     └── <TimeSince>                 // 创建时间
  ├── <PipelineProgress>                // 流水线进度条
  │     └── <StepItem> × 4              // 每个步骤
  │           ├── <StepIcon>            // ✅ ⏳ ⬜ ❌
  │           ├── <StepLabel>
  │           ├── <StepDuration>
  │           └── <StepLog>             // 实时日志（正在运行时）
  ├── <StatsCards>                      // 统计卡片（仅完成态）
  │     └── <StatCard> × 4
  ├── <SplitPane>                       // 左右分栏
  │     ├── <FileTree>                  // 文件树
  │     │     └── <FileTreeNode> (递归)
  │     └── <CodePreview>               // 代码预览（语法高亮）
  │           └── <CodeBlock>
  ├── <TestReport>                      // 测试报告
  │     ├── <ProgressBar> × N
  │     └── <FailureList> (如有失败)
  ├── <ActionBar>                       // 操作按钮组
  │     ├── <DownloadButton>
  │     ├── <GitHubButton>
  │     └── <CopyApiDocButton>
  ├── <ApiDocPreview>                   // API 端点预览
  │     └── <EndpointRow> × N
  └── <ErrorPanel>                      // 错误面板（仅失败态）
        ├── <ErrorMessage>
        ├── <RetryButton>
        └── <EditRequirementButton>
```

### 4.5 状态矩阵

| 状态 | 条件 | 表现 |
|---|---|---|
| **加载中** | 初次进入页面，API 数据未返回 | Skeleton 占位（进度条区域用脉冲动画） |
| **运行中** | `project.status` 为 `analyzing/generating_backend/generating_frontend/testing` | 实时进度条 + 日志流 + Spec 可查看 + 其他区域隐藏 |
| **运行完成** | `project.status === 'done'` | 统计卡片 + 文件树 + 代码预览 + 测试报告 + API 端点 + 操作按钮 |
| **运行失败** | `project.status === 'failed'` | 进度条展示失败步骤 + 错误详情 + 重试/修改入口 |
| **WebSocket 断连** | 运行中 WebSocket 断开 | 日志区域顶部显示黄色 Banner：「连接断开，正在重连...」 |
| **文件不存在** | 请求的文件路径在生成的产物中不存在 | 代码预览区显示：「该文件不存在或已被删除」 |

### 4.6 交互流程

```
进入页面 (/projects/:id)
      │
      ├─→ GET /api/v1/projects/:id
      │
      ├─→ status === 'done' || 'failed'
      │     └─→ 直接渲染完整结果页面
      │
      └─→ status === 'pending' || 'analyzing' || ...
            │
            ├─→ 渲染进度页面 + 建立 WebSocket 连接
            │
            ├─→ 接收 WS 消息:
            │     step_started  → 更新对应步骤为 ⏳
            │     agent_log     → 追加到日志区
            │     step_completed→ 更新对应步骤为 ✅
            │     step_failed   → 更新对应步骤为 ❌
            │     pipeline_completed → 重新 GET 项目详情，渲染完成页
            │     pipeline_failed    → 重新 GET 项目详情，渲染失败页
            │
            └─→ 组件卸载时关闭 WebSocket

文件树交互:
  点击文件名 → GET /api/v1/projects/:id/files/:path
            → 右侧代码预览区展示内容（语法高亮）

下载交互:
  点击「下载 ZIP」→ GET /api/v1/projects/:id/download
                 → 浏览器触发文件下载
```

### 4.7 数据依赖

| 操作 | API | 说明 |
|---|---|---|
| 加载项目 | `GET /api/v1/projects/:id` | 页面初始化 |
| 实时进度 | `WS /ws/projects/:id` | 仅在 status 非 done/failed 时连接 |
| 获取文件 | `GET /api/v1/projects/:id/files/:path` | 点击文件树时 |
| 获取文件树 | `GET /api/v1/projects/:id/files` | 构建左侧文件树 |
| 下载 ZIP | `GET /api/v1/projects/:id/download` | |
| 获取 Spec | `GET /api/v1/projects/:id/spec` | 「查看需求分析」展开时 |

---

## 5. 历史页 `/history`

### 5.1 页面布局

```
┌──────────────────────────────────────────────────────┐
│  历史项目                                             │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │  🔍 搜索项目...                                  │  │
│  └─────────────────────────────────────────────────┘  │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │  📋 用户管理系统                                 │  │
│  │     ✅ 完成 · 2025-01-15 14:30 · 25 文件 · 4m32s│  │
│  │     「支持用户 CRUD、角色管理...」                │  │
│  │                                    [查看详情 →]  │  │
│  ├─────────────────────────────────────────────────┤  │
│  │  🔌 博客 API 服务                                │  │
│  │     ✅ 完成 · 2025-01-15 10:15 · 18 文件 · 3m12s│  │
│  │     「RESTful 博客 API...」                      │  │
│  │                                    [查看详情 →]  │  │
│  ├─────────────────────────────────────────────────┤  │
│  │  📊 销售数据看板                                  │  │
│  │     ❌ 失败 · 2025-01-14 16:45                    │  │
│  │     「LLM API 超时」                              │  │
│  │                                    [查看详情 →]  │  │
│  └─────────────────────────────────────────────────┘  │
│                                                       │
│  ───────────── 1 / 3 ─────────────                     │
│  [上一页]                    [下一页]                   │
└──────────────────────────────────────────────────────┘
```

### 5.2 组件树

```
<HistoryPage>
  ├── <SearchInput>                     // 搜索框
  └── <ProjectList>
        └── <ProjectCard> × N
              ├── <StatusBadge>
              ├── <ProjectSummary>      // 项目名 + 摘要
              ├── <ProjectMeta>         // 时间 + 文件数 + 耗时
              └── <Link to={`/projects/${id}`}>  // 查看详情
```

### 5.3 状态矩阵

| 状态 | 条件 | 表现 |
|---|---|---|
| **加载中** | API 请求中 | Skeleton 卡片 × 5 |
| **有数据** | 项目列表非空 | 列表渲染 |
| **空列表** | 用户从未创建过项目 | 空态插画 + 「还没有项目，去创建一个吧」+ 跳转首页按钮 |
| **搜索无结果** | 搜索关键词无匹配 | 「没有找到匹配 "{keyword}" 的项目」 |
| **加载失败** | API 错误 | 错误提示 + 重试按钮 |
| **分页加载中** | 翻页请求中 | 列表保持，底部显示 Loading |

### 5.4 交互流程

```
进入页面
      │
      └─→ GET /api/v1/projects?page=1&page_size=20
                │
                ├─→ 有数据 → 渲染列表
                └─→ 空 → 空态引导

搜索:
  输入关键词 (防抖 300ms)
      │
      └─→ GET /api/v1/projects?search={keyword}

分页:
  点击「下一页」
      └─→ GET /api/v1/projects?page={n}
```

### 5.5 数据依赖

| 操作 | API |
|---|---|
| 列表 | `GET /api/v1/projects?page=&page_size=&search=` |
| 删除 | `DELETE /api/v1/projects/:id`（可选 MVP，卡片支持删除） |

---

## 6. 通用组件规格

### 6.1 StatusBadge

```typescript
interface StatusBadgeProps {
  status: 'pending' | 'analyzing' | 'generating_backend' 
         | 'generating_frontend' | 'testing' | 'done' | 'failed';
}

// 映射
const statusConfig = {
  pending:       { label: "排队中",  color: "gray",   icon: Clock },
  analyzing:     { label: "分析中",  color: "blue",   icon: Brain },
  generating_backend: { label: "生成后端", color: "purple", icon: Server },
  generating_frontend:{ label: "生成前端", color: "orange", icon: Layout },
  testing:       { label: "测试中",  color: "yellow", icon: TestTube },
  done:          { label: "已完成",  color: "green",  icon: CheckCircle },
  failed:        { label: "失败",    color: "red",    icon: XCircle },
};
```

### 6.2 FileTree

```typescript
interface FileTreeNode {
  name: string;
  type: 'file' | 'directory';
  children?: FileTreeNode[];
  path?: string;        // 仅 file 有
  fileType?: string;    // 仅 file 有
  size?: number;        // 仅 file 有
}

interface FileTreeProps {
  tree: FileTreeNode[];
  onFileClick: (path: string) => void;
  selectedPath?: string;  // 当前选中的文件路径
}

// 行为:
// - 目录默认展开第一层
// - 点击目录切换展开/折叠
// - 点击文件高亮并触发 onFileClick
// - 文件图标根据 fileType 变化（📄 .py, ⚛️ .tsx, 🐳 Dockerfile 等）
```

### 6.3 CodePreview

```typescript
interface CodePreviewProps {
  content: string | null;
  language: string;      // 'python' | 'typescript' | 'yaml' | 'json' | 'dockerfile'
  fileName?: string;
  loading?: boolean;
}

// 状态:
// - loading: 显示代码骨架（灰色块）
// - content === null: 显示「点击左侧文件查看代码」
// - content === '': 显示「文件为空」
// - content 有值: 语法高亮渲染（使用 Shiki 或 highlight.js）
// - 错误: 显示「加载文件失败」

// 额外功能:
// - 行号显示
// - 复制按钮（右上角）
// - 最大高度 600px，超出滚动
```

### 6.4 PipelineProgress

```typescript
interface StepState {
  name: string;           // 'requirement' | 'backend' | 'frontend' | 'test'
  label: string;          // 中文标签
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  duration_ms?: number;
  logs?: string[];        // 实时日志行
}

interface PipelineProgressProps {
  steps: StepState[];
  currentStep?: string;
}

// 动画:
// - running 状态: 步骤图标脉冲动画
// - completed: 绿色对勾 + 时长
// - failed: 红色叉号
// - skipped: 灰色跳过标记

// 交互:
// - 点击已完成的步骤 → 展开该步骤的详细日志/产物
```

### 6.5 TestReport

```typescript
interface TestReportProps {
  report: {
    total_tests: number;
    passed: number;
    failed: number;
    errors: number;
    coverage_percent: number;
    failures: Array<{
      test_name: string;
      file: string;
      line: number;
      message: string;
    }>;
  };
  loading?: boolean;
}

// 状态:
// - loading: 进度条用动画占位
// - all_passed: 绿色主题 + 🎉
// - has_failures: 红色主题 + 失败列表展开
// - no_tests: 「未生成测试」提示

// 布局:
// - 顶部：通过率大数字 + 覆盖率进度环
// - 中部：后端测试 / 前端测试 分开的进度条
// - 底部：失败列表（如有），每个失败项可展开看详情
```

---

## 7. 响应式断点

| 断点 | 宽度 | 布局调整 |
|---|---|---|
| Desktop | ≥ 1024px | 首页居中单列（max-w-3xl）；项目页左右分栏（文件树 280px + 代码区 flex-1） |
| Tablet | 768-1023px | 首页同 Desktop；项目页文件树可折叠（默认折叠） |
| Mobile | < 768px | 首页全宽；项目页单列堆叠布局，文件树在上，代码区在下；统计卡片改为 2×2 网格；Header 导航收缩为汉堡菜单 |

---

## 8. 色彩与动效

### 8.1 主题色（基于 shadcn/ui 默认主题扩展）

| Token | 用途 |
|---|---|
| `--primary` | 主按钮、当前步骤、链接 |
| `--success` (green-500) | 完成状态、测试通过 |
| `--destructive` (red-500) | 失败状态、错误信息 |
| `--warning` (yellow-500) | 运行中、部分完成 |
| `--muted` (gray-400) | 未开始步骤、禁用状态 |

### 8.2 关键动效

| 元素 | 动效 |
|---|---|
| 步骤运行中 | 图标柔光脉冲（`animate-pulse`，1.5s 周期） |
| 页面跳转 | 无动画（即时渲染），仅项目页日志区支持平滑追加 |
| 文件树展开 | `collapsible` 组件默认动画（高度过渡 200ms） |
| Toast 通知 | 右上角滑入，3 秒后自动消失 |
| Skeleton | 标准 shimmer 动画 |

---

## 9. 前端技术实现要点

### 9.1 路由设计

```typescript
// src/router.tsx
import { createBrowserRouter } from "react-router-dom";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <MainLayout />,         // Header + Outlet + Footer
    children: [
      { index: true, element: <HomePage /> },
      { path: "projects/:id", element: <ProjectPage /> },
      { path: "history", element: <HistoryPage /> },
    ],
  },
]);
```

### 9.2 状态管理

MVP 不使用全局状态库（Redux/Zustand），每个页面自行管理状态：

| 页面 | 状态来源 | Hook |
|---|---|---|
| HomePage | 本地 useState | `useState` for form data |
| ProjectPage | API + WebSocket | `useProject(id)` custom hook |
| HistoryPage | API + URL search params | `useHistory()` custom hook |

### 9.3 关键依赖

```json
{
  "dependencies": {
    "react": "^18.3",
    "react-router-dom": "^6.26",
    "react-dom": "^18.3",
    "@shadcn/ui": "latest",
    "lucide-react": "latest",
    "shiki": "^1.12",
    "sonner": "latest"
  }
}
```

- `shiki`：代码语法高亮（服务端友好的 Shiki，比 Prism.js 更轻）
- `sonner`：Toast 通知组件
- `lucide-react`：图标库（与 shadcn/ui 配套）

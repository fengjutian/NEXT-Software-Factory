# Agent Error Handling & Recovery Specification v0.1

> 本文档定义 AI Project Factory 中 **Agent 失败场景的完整处理策略**。  
> 在流水线中，任何 Agent 都可能失败——LLM 超时、输出格式错误、Manifest 校验失败、  
> 依赖的上游 Agent 产出不完整等等。每个失败必须有明确的分类、重试策略和降级路径。

---

## 1. 错误分类

### 1.1 四级错误

| 级别 | 名称 | 含义 | 默认策略 |
|---|---|---|---|
| E0 | Transient | 瞬时故障，重试大概率恢复 | 自动重试 3 次，指数退避 |
| E1 | Recoverable | 可恢复，但需要策略调整 | 自动重试 1 次 + 调整参数 |
| E2 | Partial | 部分成功，部分失败 | 标记 manifest 中的 skipped 项，继续流水线 |
| E3 | Fatal | 致命错误，流水线终止 | 终止，通知用户，保留中间产物 |

### 1.2 错误类型映射表

| 错误场景 | 级别 | 检测方式 | 重试策略 |
|---|---|---|---|
| LLM API 超时（>120s） | E0 | `asyncio.TimeoutError` | 重试 3 次，间隔 2s/4s/8s |
| LLM API 速率限制（429） | E0 | HTTP 429 | 重试 3 次，间隔从 Retry-After header 读取 |
| LLM API 服务端错误（5xx） | E0 | HTTP 500/502/503 | 重试 2 次，间隔 5s/10s |
| LLM 返回非 JSON | E1 | `json.JSONDecodeError` | 重试 1 次 + Prompt 加强"只输出 JSON" |
| LLM 返回 JSON 结构不完整 | E1 | Schema validation failure | 重试 1 次 + 提供缺失字段列表 |
| LLM 返回内容超出 token 限制 | E1 | `max_tokens` exceeded | 重试 1 次 + 拆分任务 |
| Manifest 中某 item 标记 partial | E2 | Manifest status check | 不重试，下游 Agent 适配 |
| Manifest 中某 item 标记 skipped | E2 | Manifest status check | 不重试，下游 Agent 跳过 |
| Manifest stats 对不上 | E1 | Manifest validation | 重试 1 次（可能是 Agent 漏算了某项） |
| 生成的代码有语法错误 | E1 | AST 解析 / ESLint / Ruff | 重试 1 次 + 提供错误详情 |
| 依赖的上游 Agent 全量失败 | E3 | 上游 status=failed | 终止，不执行当前 Agent |
| 依赖的上游 Agent 部分失败 | E2 | 上游 manifest 有 skipped | 继续执行，适配上游的实际交付 |
| Docker Sandbox 启动失败 | E0 | Docker 错误 | 重试 2 次，间隔 5s |
| 测试执行超时（>300s） | E1 | 超时 | 重试 1 次，降低测试数量 |
| 磁盘空间不足 | E3 | OSError | 终止，通知管理员 |

---

## 2. 重试机制

### 2.1 重试参数

```python
from dataclasses import dataclass
from enum import Enum

class ErrorLevel(Enum):
    TRANSIENT = "E0"
    RECOVERABLE = "E1"
    PARTIAL = "E2"
    FATAL = "E3"

@dataclass
class RetryConfig:
    level: ErrorLevel
    max_retries: int
    base_delay_seconds: float
    backoff_multiplier: float
    max_delay_seconds: float
    
RETRY_CONFIGS = {
    ErrorLevel.TRANSIENT: RetryConfig(
        level=ErrorLevel.TRANSIENT,
        max_retries=3,
        base_delay_seconds=2.0,
        backoff_multiplier=2.0,
        max_delay_seconds=30.0,
    ),
    ErrorLevel.RECOVERABLE: RetryConfig(
        level=ErrorLevel.RECOVERABLE,
        max_retries=1,
        base_delay_seconds=3.0,
        backoff_multiplier=1.5,
        max_delay_seconds=15.0,
    ),
    ErrorLevel.PARTIAL: RetryConfig(
        level=ErrorLevel.PARTIAL,
        max_retries=0,  # 部分失败不重试
        base_delay_seconds=0,
        backoff_multiplier=0,
        max_delay_seconds=0,
    ),
    ErrorLevel.FATAL: RetryConfig(
        level=ErrorLevel.FATAL,
        max_retries=0,  # 致命错误不重试
        base_delay_seconds=0,
        backoff_multiplier=0,
        max_delay_seconds=0,
    ),
}
```

### 2.2 重试执行器

```python
import asyncio
import random
from typing import Callable, Awaitable

class AgentRetryExecutor:
    """Agent 重试执行器"""
    
    def __init__(self, agent_name: str, ws_manager):
        self.agent_name = agent_name
        self.ws_manager = ws_manager
        self.attempt = 0
    
    async def execute_with_retry(
        self, 
        project_id: str,
        task: Callable[[], Awaitable[dict]],
        error_classifier: Callable[[Exception], tuple[ErrorLevel, str]],
    ) -> dict:
        """
        执行 Agent 任务，自动重试。
        
        Returns:
            Agent 输出 JSON，或最后一次失败的异常
        """
        last_error = None
        
        for self.attempt in range(1, 4):  # 最多总共 3 次尝试
            try:
                result = await task()
                
                # 成功 — 但需要校验 Manifest
                manifest_errors = self._validate_manifest(result)
                if manifest_errors and self.attempt < 3:
                    await self._notify_retry(
                        project_id, 
                        f"Manifest 校验失败: {manifest_errors}，正在重试..."
                    )
                    # 修复后的 prompt 传给下一次重试
                    continue
                
                return result
                
            except Exception as e:
                last_error = e
                level, message = error_classifier(e)
                
                config = RETRY_CONFIGS[level]
                
                if self.attempt >= config.max_retries + 1:
                    # 重试次数用尽
                    await self._notify_failed(project_id, level, str(e))
                    raise
                
                delay = min(
                    config.base_delay_seconds * (config.backoff_multiplier ** (self.attempt - 1)),
                    config.max_delay_seconds
                )
                # 增加 jitter 防止惊群
                delay *= (1 + random.random() * 0.3)
                
                await self._notify_retry(
                    project_id,
                    f"{message}，{delay:.1f}s 后重试 (第 {self.attempt} 次)..."
                )
                await asyncio.sleep(delay)
        
        raise last_error
    
    def _validate_manifest(self, result: dict) -> list[str]:
        """校验 Manifest 完整性和一致性"""
        errors = []
        
        if "status" not in result:
            errors.append("缺少 status 字段")
            return errors
        
        if result["status"] == "failed":
            return []  # 失败态不检查 manifest
        
        manifest_key = f"{self.agent_name}_manifest"
        if manifest_key not in result:
            errors.append(f"缺少 {manifest_key} 字段")
            return errors
        
        m = result[manifest_key]
        
        # 必须字段检查
        for field in ["summary", "items", "stats"]:
            if field not in m:
                errors.append(f"manifest 缺少 '{field}' 字段")
        
        if "stats" in m:
            s = m["stats"]
            computed = (
                s.get("completed", 0) + s.get("partial", 0) 
                + s.get("skipped", 0) + s.get("deferred", 0)
            )
            if computed != s.get("total_planned", 0):
                errors.append(
                    f"stats 不一致: completed+partial+skipped+deferred={computed} "
                    f"≠ total_planned={s.get('total_planned')}"
                )
        
        # 每个 skipped/deferred item 必须有 skip_reason
        for item in m.get("items", []):
            if item.get("status") in ("skipped", "deferred"):
                if not item.get("skip_reason"):
                    errors.append(
                        f"Item {item.get('ref_id')} 状态为 {item['status']} 但缺少 skip_reason"
                    )
        
        return errors
```

---

## 3. 降级策略

### 3.1 逐层降级

当上游 Agent 部分失败时，下游 Agent 需要有降级行为：

| 上游失败情况 | 下游 Agent 降级行为 |
|---|---|
| Requirement Agent 全量失败 (E3) | 整个流水线终止，不执行任何后续 Agent |
| Requirement Agent 少规划了某类页面 | Backend Agent 正常执行（不依赖 pages） |
| Backend Agent 少实现了某 entity | Frontend Agent 不为该 entity 生成页面，manifest 标记 skipped |
| Backend Agent 少实现了某 endpoint | Frontend Agent 调整对应功能（如改为提示"即将推出"），manifest 标注 |
| Backend Agent 全量失败 | Frontend Agent 和 Test Agent 均跳过，流水线标记 failed |
| Frontend Agent 部分失败 | Test Agent 仅为完成的前端页面生成测试 |
| Frontend Agent 全量失败 | Test Agent 仅生成后端测试 |

### 3.2 降级决策伪代码

```python
class PipelineDegradation:
    """流水线降级决策器"""
    
    async def decide_next_step(
        self, 
        previous_result: dict, 
        next_agent: str
    ) -> tuple[bool, str | None]:
        """
        决定是否继续执行下一个 Agent。
        
        Returns:
            (should_continue, degradation_notice)
        """
        status = previous_result.get("status")
        
        if status == "failed":
            if next_agent in ("requirement",):
                # 第一个 Agent 就失败 → 终止
                return False, "需求分析失败，流水线终止"
            elif next_agent == "frontend":
                # Backend 失败 → 跳过 Frontend 和 Test
                return False, "后端生成失败，前端和测试阶段已跳过"
            elif next_agent == "test":
                return False, "前置阶段失败，测试阶段已跳过"
            return False, "流水线终止"
        
        manifest = previous_result.get(f"{previous_result.get('agent')}_manifest", {})
        stats = manifest.get("stats", {})
        
        if stats.get("completed", 0) == 0 and stats.get("total_planned", 0) > 0:
            # 全量失败但没报错
            return False, f"前置 Agent 未完成任何功能，{next_agent} Agent 跳过"
        
        if stats.get("skipped", 0) > 0 or stats.get("partial", 0) > 0:
            notice = (
                f"前置 Agent 部分完成：{stats['completed']}/{stats['total_planned']} 完成，"
                f"{stats['partial']} 部分，{stats['skipped']} 跳过。"
                f"将继续生成但功能可能不完整。"
            )
            return True, notice
        
        return True, None
```

---

## 4. 超时控制

### 4.1 超时配置

| Agent | 超时时间 | 理由 |
|---|---|---|
| Requirement Agent | 60s | 只做分析，不生成代码 |
| Backend Agent | 180s | 生成完整后端项目（多文件） |
| Frontend Agent | 180s | 生成完整前端项目 |
| Test Agent | 300s | 代码生成 + Docker Sandbox 执行 |
| 单个 LLM API 调用 | 120s | Anthropic/OpenAI 默认 |
| Docker Sandbox 测试执行 | 180s | 安装依赖 + 运行测试 |
| 整个流水线 | 600s (10 min) | 超时则标记失败，保留中间产物 |

### 4.2 超时实现

```python
import asyncio

async def run_with_timeout(coro, timeout_seconds: float, agent_name: str):
    """带超时的 Agent 执行"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise AgentTimeoutError(
            f"{agent_name} 执行超时（>{timeout_seconds}s），"
            f"可能原因：需求过于复杂、LLM 响应慢、生成内容过多"
        )

class AgentTimeoutError(Exception):
    """Agent 超时异常"""
    def __init__(self, message: str):
        self.message = message
        self.level = ErrorLevel.RECOVERABLE  # 超时可重试一次
        super().__init__(message)
```

---

## 5. 用户通知

### 5.1 WebSocket 错误事件

```json
// Agent 开始重试
{
  "type": "agent_retry",
  "step": "backend",
  "attempt": 2,
  "max_attempts": 3,
  "reason": "LLM API 超时",
  "next_retry_in_seconds": 4.2,
  "timestamp": "2025-01-01T00:02:15Z"
}

// Agent 部分完成（有降级）
{
  "type": "agent_partial",
  "step": "backend",
  "completed": 4,
  "total": 5,
  "skipped": [
    {"ref_id": "ep_005", "reason": "DELETE 端点需要额外确认"}
  ],
  "timestamp": "2025-01-01T00:02:15Z"
}

// Agent 致命失败
{
  "type": "agent_fatal",
  "step": "backend",
  "error": "LLM API 认证失败，请检查 API Key 配置",
  "retryable": false,
  "timestamp": "2025-01-01T00:02:15Z"
}
```

### 5.2 前端错误展示

```
┌──────────────────────────────────────────────────────┐
│  ⚠️ Backend Agent 部分完成                            │
│                                                       │
│  已完成 4/5 项功能：                                   │
│  ✅ GET /users — 用户列表                             │
│  ✅ POST /users — 创建用户                            │
│  ✅ GET /users/{id} — 用户详情                        │
│  ✅ PUT /users/{id} — 更新用户                        │
│  ⚠️ DELETE /users/{id} — LLM 响应格式异常，已跳过    │
│                                                       │
│  前端将自动适配：删除按钮改为"停用"                      │
│                                                       │
│  [继续生成前端]  [重新生成后端]                        │
└──────────────────────────────────────────────────────┘
```

---

## 6. 全局错误处理中间件

```python
# FastAPI 全局异常处理器

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(AgentTimeoutError)
async def agent_timeout_handler(request: Request, exc: AgentTimeoutError):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "AGENT_TIMEOUT",
                "message": str(exc.message),
                "retryable": True,
            }
        }
    )

@app.exception_handler(AgentFatalError)
async def agent_fatal_handler(request: Request, exc: AgentFatalError):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "AGENT_FATAL",
                "message": str(exc.message),
                "retryable": False,
            }
        }
    )

@app.exception_handler(ManifestValidationError)
async def manifest_error_handler(request: Request, exc: ManifestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "MANIFEST_INVALID",
                "message": exc.message,
                "details": exc.errors,
            }
        }
    )
```

---

## 7. Pipeline 状态转换（含错误路径）

```
                    ┌──────────────┐
                    │   pending     │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
              ┌─────│  analyzing   │─────┐
              │     └──────┬───────┘     │
              │            │             │
              │ E3/Fatal   │ success     │ E2/Partial
              │            ▼             │
              │     ┌──────────────┐     │
              │     │gen_backend   │     │
              │     └──────┬───────┘     │
              │            │             │
              │ E3/Fatal   │ success     │ E2/Partial
              │            ▼             │
              │     ┌──────────────┐     │
              │     │gen_frontend  │     │
              │     └──────┬───────┘     │
              │            │             │
              │ E3/Fatal   │ success     │ E2/Partial
              │            ▼             │
              │     ┌──────────────┐     │
              │     │   testing    │     │
              │     └──────┬───────┘     │
              │            │             │
              │            ▼             │
              │     ┌──────────────┐     │
              │     │     done     │◄────┘
              │     └──────────────┘
              │
              ▼
       ┌──────────────┐
       │    failed     │  ← 保留中间产物，支持重试
       └──────────────┘
```

所有路径最终状态：
- `done`: 全部成功，产物完整
- `done` + manifest 有 partial/skipped: 成功但有降级
- `failed`: 致命错误终止，但保留中间产物（如 RequirementSpec）

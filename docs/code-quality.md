# Code Quality Standards v0.1

> 本文档定义 AI Project Factory **生成代码的质量标准**。  
> 每个 Agent 生成的代码在交付前必须通过这些检查。违反任何一条红线的代码将被 Review Agent 驳回重新生成。  
> 这是工厂的「质检车间」规范。

---

## 1. 质量标准分级

| 级别 | 名称 | 含义 | 违反后果 |
|---|---|---|---|
| 🔴 CRITICAL | 红线 | 代码不可运行或存在安全漏洞 | **强制驳回**，Agent 必须修复后重新提交 |
| 🟡 WARNING | 警告 | 违反最佳实践或代码风格 | 记录但不驳回，Review Report 中标出 |
| 🔵 INFO | 建议 | 可以改进但不强制 | 仅作为提示输出 |

---

## 2. Python 代码标准（后端生成产物）

### 2.1 红线（CRITICAL）

| # | 规则 | 检测方式 |
|---|---|---|
| P-C01 | 代码可以 `import` 不报错 | AST 解析 |
| P-C02 | 所有函数有完整的类型注解（参数 + 返回值） | mypy --strict |
| P-C03 | 无未使用的 import | Ruff F401 |
| P-C04 | 无未使用的变量 | Ruff F841 |
| P-C05 | SQLAlchemy 模型使用 Mapped[T] + mapped_column()（2.0 风格） | AST 模式匹配 |
| P-C06 | 禁止使用 `eval()` / `exec()` | Ruff S102 |
| P-C07 | 禁止在 SQL 查询中使用字符串拼接（SQL 注入） | AST 检测 f-string 在 execute() 中 |
| P-C08 | 密码/Secret 不能硬编码 | 检测常见关键词：password, secret, api_key, token + 赋值 |
| P-C09 | 所有 HTTP 端点有错误返回（不是裸 Exception） | AST 检测 route 函数没有 try/except |
| P-C10 | Pydantic v2 风格：`model_validate` 而非 `from_orm` | 字符串匹配 |

### 2.2 警告（WARNING）

| # | 规则 | 检测方式 |
|---|---|---|
| P-W01 | 函数行数 ≤ 50 行 | 代码行数统计 |
| P-W02 | 类行数 ≤ 200 行 | 代码行数统计 |
| P-W03 | 圈复杂度 ≤ 10 | Ruff C901 |
| P-W04 | 文档字符串：所有 public 函数有 docstring | Ruff D103 |
| P-W05 | import 按标准库 → 第三方 → 本地排序 | Ruff I001 |
| P-W06 | 使用 `is` 而非 `==` 比较 None/True/False | Ruff E711 |
| P-W07 | 字符串使用 f-string 而非 % 格式化 | Ruff UP031 |
| P-W08 | 禁止 bare except (`except:`) | Ruff E722 |

### 2.3 mypy 配置

```ini
# pyproject.toml (生成的项目中)
[tool.mypy]
strict = true
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
```

### 2.4 Ruff 配置

```ini
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "SIM",  # flake8-simplify
    "D",    # pydocstyle (D103 only)
    "S",    # flake8-bandit (security)
]
ignore = [
    "D100",  # 模块级 docstring 可选
    "D104",  # package docstring 可选
    "D107",  # __init__ docstring 可选
]

[tool.ruff.lint.pydocstyle]
convention = "google"
```

---

## 3. TypeScript 代码标准（前端生成产物）

### 3.1 红线（CRITICAL）

| # | 规则 | 检测方式 |
|---|---|---|
| T-C01 | `tsc --noEmit` 通过（0 类型错误） | TypeScript 编译器 |
| T-C02 | 禁止使用 `any` 类型 | ESLint `@typescript-eslint/no-explicit-any` |
| T-C03 | React 组件使用函数式组件 + 类型化 Props | AST 检测 `class extends React.Component` |
| T-C04 | 使用 Tailwind 类名，禁止内联 style | ESLint 检测 `style={{}}` |
| T-C05 | 禁止 `dangerouslySetInnerHTML`（XSS） | ESLint `react/no-danger` |
| T-C06 | 所有用户可见文字使用中文 | 抽样检测 |
| T-C07 | 禁止硬编码颜色值（如 `#3B82F6`）| 字符串正则匹配 |
| T-C08 | 禁止硬编码 font-family | 字符串匹配 |
| T-C09 | API 调用有错误处理（try/catch 或 .catch()） | AST 检测 |

### 3.2 警告（WARNING）

| # | 规则 | 检测方式 |
|---|---|---|
| T-W01 | 组件行数 ≤ 200 行 | 代码行数统计 |
| T-W02 | 使用命名导出（禁止 default export） | ESLint `import/no-default-export` |
| T-W03 | Hook 命名以 `use` 开头 | ESLint `react-hooks/rules-of-hooks` |
| T-W04 | 使用 const 而非 let（除非需要重新赋值） | ESLint `prefer-const` |
| T-W05 | 无 console.log（生产代码） | ESLint `no-console` |
| T-W06 | 所有 Props 有 TypeScript interface 定义 | 手动检查 |
| T-W07 | 使用 optional chaining（`?.`）而非嵌套 if | ESLint |

### 3.3 ESLint 配置

```javascript
// .eslintrc.cjs (生成的项目中)
module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/strict-type-checked',
    'plugin:react-hooks/recommended',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    project: ['./tsconfig.json'],
  },
  plugins: ['react-refresh', '@typescript-eslint', 'import'],
  rules: {
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    'import/no-default-export': 'error',
    'no-console': 'warn',
    'react/no-danger': 'error',
  },
};
```

### 3.4 TypeScript 配置

```json
// tsconfig.json (生成的项目中)
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"]
}
```

---

## 4. 安全检查（通用）

### 4.1 安全红线

| # | 规则 | 适用范围 | 检测方式 |
|---|---|---|---|
| S-C01 | 无硬编码 Secret/API Key/Token | 全部 | 正则 + 关键词匹配 |
| S-C02 | 无 SQL 注入（字符串拼接 SQL） | Python | AST 检测 |
| S-C03 | 无 XSS（dangerouslySetInnerHTML / innerHTML） | TypeScript | ESLint |
| S-C04 | CORS 配置不使用 `allow_origins=["*"]`（生产环境） | Python | 字符串匹配 |
| S-C05 | 密码使用 `SecretStr`（Pydantic）或 hash 存储 | Python | AST 检测 |
| S-C06 | 所有文件上传有类型和大小限制 | Python | AST 检测 UploadFile 使用 |
| S-C07 | 敏感操作（删除）有确认机制 | TypeScript | 组件代码检查 |
| S-C08 | 无 `shell=True` 的 subprocess 调用 | Python | Ruff S602 |

### 4.2 安全扫描集成

```python
# 生成后自动安全扫描
async def security_scan(files: list[dict]) -> list[dict]:
    """
    对生成的所有文件进行安全扫描。
    返回违反安全红线的文件列表。
    """
    violations = []
    
    for file in files:
        path = file["path"]
        content = file["content"]
        
        # 检查硬编码密钥
        secret_patterns = [
            (r'(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*["\'][^"\']+["\']', 
             "硬编码敏感信息"),
            (r'(?i)(aws_access_key|private_key|ssh_key)', 
             "可能暴露云服务凭证"),
        ]
        for pattern, desc in secret_patterns:
            if re.search(pattern, content):
                violations.append({
                    "file": path,
                    "severity": "CRITICAL",
                    "rule": "S-C01",
                    "message": desc,
                })
        
        # 检查 SQL 注入
        if path.endswith(".py"):
            if re.search(r'f["\'].*SELECT.*\{', content) or \
               re.search(r'\.execute\(["\'].*%', content):
                violations.append({
                    "file": path,
                    "severity": "CRITICAL",
                    "rule": "S-C02",
                    "message": "潜在的 SQL 注入：使用字符串拼接构建 SQL",
                })
    
    return violations
```

---

## 5. Review Agent 执行流程

### 5.1 质检流水线

```
Agent 生成代码完成
      │
      ▼
┌─────────────────────┐
│ Step 1: Syntax Check │  ← AST 解析 / tsc --noEmit
└─────────┬───────────┘
          │ ✅ PASS
          ▼
┌─────────────────────┐
│ Step 2: Lint Check  │  ← Ruff / ESLint
└─────────┬───────────┘
          │ ✅ PASS (允许 WARNING)
          ▼
┌─────────────────────┐
│ Step 3: Type Check  │  ← mypy --strict / tsc --noEmit
└─────────┬───────────┘
          │ ✅ PASS
          ▼
┌─────────────────────┐
│ Step 4: Security    │  ← 安全规则扫描
└─────────┬───────────┘
          │ ✅ PASS
          ▼
┌─────────────────────┐
│ Step 5: Quality     │  ← 圈复杂度 / 行数 / 文档字符串
└─────────┬───────────┘
          │ ✅ PASS (允许 WARNING)
          ▼
      ✅ APPROVED
```

### 5.2 Review Report 格式

```json
{
  "review_report": {
    "overall": "PASSED_WITH_WARNINGS",
    "scores": {
      "syntax": {"passed": true},
      "lint": {"passed": true, "warnings": 3, "errors": 0},
      "types": {"passed": true, "errors": 0},
      "security": {"passed": true, "violations": 0},
      "quality": {"passed": true, "warnings": 5}
    },
    "violations": [
      {
        "file": "backend/app/services/user_service.py",
        "line": 45,
        "severity": "WARNING",
        "rule": "P-W01",
        "message": "函数 get_user_by_filters 有 67 行，超过 50 行限制"
      }
    ],
    "action": "approve",
    "summary": "0 红线违反，8 警告，建议在后续迭代中修复警告"
  }
}
```

### 5.3 红线违反时的处理

```
Review Agent 发现 CRITICAL violation
      │
      ▼
将 violation 列表注入原 Agent 的 Prompt
  追加一段：
  "You previously generated code with the following issues:
   - [file]: [rule] — [message]
   Please fix ALL critical issues and regenerate the affected files."
      │
      ▼
原 Agent 重新生成对应文件（不是全部重来）
      │
      ▼
最多重试 2 次。2 次后仍有 CRITICAL violation：
  → 标记该文件为 'rejected'
  → Manifest 中将相关功能标记为 'partial'，detail 说明原因
  → 流水线继续（降级），不阻塞整个 pipeline
```

---

## 6. 代码风格统一要求

### 6.1 Python 命名规范

| 元素 | 规范 | 示例 |
|---|---|---|
| 模块/文件 | snake_case | `user_service.py` |
| 类 | PascalCase | `class UserService:` |
| 函数/方法 | snake_case | `def get_user_by_id():` |
| 变量 | snake_case | `user_count = 0` |
| 常量 | UPPER_SNAKE_CASE | `MAX_PAGE_SIZE = 100` |
| 私有成员 | _leading_underscore | `_cache: dict` |

### 6.2 TypeScript 命名规范

| 元素 | 规范 | 示例 |
|---|---|---|
| 组件文件 | PascalCase | `UserList.tsx` |
| 工具文件 | camelCase | `apiClient.ts` |
| 组件 | PascalCase | `function UserList() {}` |
| Hook | camelCase, use 前缀 | `function useUsers() {}` |
| 接口/类型 | PascalCase | `interface UserCreate {}` |
| 变量/函数 | camelCase | `const userCount = 0` |
| 常量 | UPPER_SNAKE_CASE | `const API_BASE_URL = ...` |

---

## 7. 生成项目必须包含的文件

| 文件 | 必要性 | 内容要求 |
|---|---|---|
| `README.md` | REQUIRED | 项目名、简介、快速启动命令、API 文档链接 |
| `.gitignore` | REQUIRED | 至少包含 `__pycache__/`, `node_modules/`, `.env` |
| `.env.example` | REQUIRED | 所有环境变量的模板（不含真实值） |
| `Dockerfile` | RECOMMENDED | 多阶段构建，非 root 用户 |
| `docker-compose.yml` | RECOMMENDED | 一键启动完整服务 |
| `pyproject.toml` | REQUIRED (后端) | 含 mypy + Ruff 配置 |
| `tsconfig.json` | REQUIRED (前端) | strict 模式 |
| `.eslintrc.cjs` | REQUIRED (前端) | 含 TypeScript 规则 |

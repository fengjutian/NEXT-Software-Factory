# Design System Specification v0.1

> 本文档定义 AI Project Factory 的**设计规范层（Design System Layer）**。  
> 用户上传设计资产 + 选择设计 Token → Agent 严格遵守规范生成代码，不允许自由发挥。  
> 这是工厂从「AI 随意生成 UI」到「AI 按照设计标准生产 UI」的关键约束。

---

## 1. 设计理念

```
传统 AI 代码生成:                    本工厂的代码生成:

用户: "做一个管理后台"               用户: "做一个管理后台"
        │                                  │
        ▼                                  ▼
AI 随机挑颜色/字体/间距              AI 读取 Design Spec
        │                                  │
        ▼                                  ▼
每次生成都不一样 ❌                  每次生成风格一致 ✅
                             颜色/字体/间距/圆角全部可控 ✅
```

**核心原则**：

| 原则 | 说明 |
|---|---|
| **设计先行** | 先定义 Design Spec，再生成代码——不定义就不生成 |
| **Token 驱动** | 所有视觉属性从 Design Token 取值，Agent 不能硬编码颜色/字体 |
| **资产可替换** | 用户上传的图标/Logo 直接引用到代码中 |
| **默认即专业** | 提供 3 套预设设计规范，用户不改也能产出专业 UI |

---

## 2. 用户流程

```
用户输入需求
      │
      ▼
选择设计规范
  ├─ 使用预设 (默认)
  │    ├─ 📊 企业蓝 (Professional Blue)
  │    ├─ 🌿 自然绿 (Nature Green)
  │    └─ 🌙 暗夜模式 (Dark Mode)
  │
  └─ 自定义规范
       ├─ 上传 Logo (SVG/PNG, ≤ 500KB)
       ├─ 上传 Favicon (ICO/PNG, ≤ 100KB)
       ├─ 选择主色调 (Color Picker)
       ├─ 选择字体 (从 Google Fonts 列表)
       ├─ 调整圆角 (Slider: 0-16px)
       └─ 调整间距单位 (4px/8px/12px)
      │
      ▼
生成 DesignSpec JSON
      │
      ▼
传递给 Backend Agent + Frontend Agent
      │
      ▼
生成的代码严格引用 Design Token
```

---

## 3. DesignSpec JSON Schema

### 3.1 完整结构

```json
{
  "version": "1.0",
  "preset": "string — 预设名称: 'professional_blue' | 'nature_green' | 'dark_mode' | 'custom'",
  "brand": {
    "logo": {
      "path": "string — 相对于项目根目录的路径，如 'assets/logo.svg'",
      "alt": "string — Alt 文本",
      "width": "number — 像素",
      "height": "number — 像素"
    },
    "favicon": {
      "path": "string — 如 'assets/favicon.ico'",
      "type": "string — 'ico' | 'png' | 'svg'"
    },
    "project_name": "string — 显示在页面标题和应用 Header 中的项目名"
  },
  "tokens": {
    "colors": {
      "primary": {
        "50": "#EFF6FF",
        "100": "#DBEAFE",
        "200": "#BFDBFE",
        "300": "#93C5FD",
        "400": "#60A5FA",
        "500": "#3B82F6",
        "600": "#2563EB",
        "700": "#1D4ED8",
        "800": "#1E40AF",
        "900": "#1E3A8A",
        "950": "#172554"
      },
      "secondary": { "50": "...", "...": "..." },
      "success": "#10B981",
      "warning": "#F59E0B",
      "destructive": "#EF4444",
      "muted": "#6B7280",
      "background": "#FFFFFF",
      "foreground": "#111827",
      "card": "#FFFFFF",
      "border": "#E5E7EB",
      "input": "#F9FAFB"
    },
    "typography": {
      "font_family": {
        "sans": "'Inter', -apple-system, sans-serif",
        "mono": "'JetBrains Mono', monospace"
      },
      "font_size": {
        "xs": "0.75rem",
        "sm": "0.875rem",
        "base": "1rem",
        "lg": "1.125rem",
        "xl": "1.25rem",
        "2xl": "1.5rem",
        "3xl": "1.875rem",
        "4xl": "2.25rem"
      },
      "font_weight": {
        "normal": "400",
        "medium": "500",
        "semibold": "600",
        "bold": "700"
      },
      "line_height": {
        "tight": "1.25",
        "normal": "1.5",
        "relaxed": "1.75"
      }
    },
    "spacing": {
      "unit": "number — 基础间距单位，默认 4 (px)",
      "scale": {
        "0": "0px",
        "1": "4px",
        "2": "8px",
        "3": "12px",
        "4": "16px",
        "5": "20px",
        "6": "24px",
        "8": "32px",
        "10": "40px",
        "12": "48px",
        "16": "64px"
      }
    },
    "border_radius": {
      "none": "0px",
      "sm": "2px",
      "md": "6px",
      "lg": "8px",
      "xl": "12px",
      "full": "9999px"
    },
    "shadows": {
      "sm": "0 1px 2px rgba(0,0,0,0.05)",
      "md": "0 4px 6px -1px rgba(0,0,0,0.1)",
      "lg": "0 10px 15px -3px rgba(0,0,0,0.1)"
    }
  },
  "components": {
    "button": {
      "border_radius": "md",
      "padding_x": "4",
      "padding_y": "2",
      "font_weight": "medium"
    },
    "input": {
      "border_radius": "md",
      "border_color": "border",
      "focus_ring_color": "primary.500",
      "padding_x": "3",
      "padding_y": "2"
    },
    "card": {
      "border_radius": "lg",
      "shadow": "sm",
      "padding": "6",
      "background": "card"
    },
    "table": {
      "header_background": "primary.50",
      "row_hover_background": "primary.50",
      "border_color": "border",
      "cell_padding_x": "4",
      "cell_padding_y": "3"
    },
    "modal": {
      "border_radius": "xl",
      "shadow": "lg",
      "backdrop_opacity": "0.5"
    }
  }
}
```

### 3.2 三套预设

#### Preset 1: `professional_blue` (企业蓝)

```json
{
  "preset": "professional_blue",
  "brand": {
    "project_name": "未命名项目",
    "logo": null,
    "favicon": null
  },
  "tokens": {
    "colors": {
      "primary": {
        "50": "#EFF6FF", "100": "#DBEAFE", "200": "#BFDBFE",
        "300": "#93C5FD", "400": "#60A5FA", "500": "#3B82F6",
        "600": "#2563EB", "700": "#1D4ED8", "800": "#1E40AF", "900": "#1E3A8A"
      },
      "secondary": {
        "50": "#F8FAFC", "100": "#F1F5F9", "500": "#64748B", "900": "#0F172A"
      },
      "success": "#10B981",
      "warning": "#F59E0B",
      "destructive": "#EF4444",
      "background": "#FFFFFF",
      "foreground": "#111827",
      "card": "#FFFFFF",
      "border": "#E5E7EB",
      "input": "#F9FAFB"
    },
    "typography": {
      "font_family": {
        "sans": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "mono": "'JetBrains Mono', 'Fira Code', monospace"
      },
      "font_size": {
        "xs": "0.75rem", "sm": "0.875rem", "base": "1rem",
        "lg": "1.125rem", "xl": "1.25rem", "2xl": "1.5rem",
        "3xl": "1.875rem", "4xl": "2.25rem"
      }
    },
    "spacing": { "unit": 4 },
    "border_radius": { "sm": "4px", "md": "6px", "lg": "8px", "xl": "12px" }
  }
}
```

#### Preset 2: `nature_green` (自然绿)

```json
{
  "preset": "nature_green",
  "tokens": {
    "colors": {
      "primary": {
        "50": "#ECFDF5", "100": "#D1FAE5", "200": "#A7F3D0",
        "300": "#6EE7B7", "400": "#34D399", "500": "#10B981",
        "600": "#059669", "700": "#047857", "800": "#065F46", "900": "#064E3B"
      },
      "secondary": {
        "50": "#FFFBEB", "100": "#FEF3C7", "500": "#D97706", "900": "#451A03"
      },
      "success": "#059669",
      "warning": "#D97706",
      "destructive": "#DC2626",
      "background": "#FAFDF7",
      "foreground": "#1A2E1A",
      "card": "#FFFFFF",
      "border": "#D1E7D1",
      "input": "#F5FAF5"
    }
  }
}
```

#### Preset 3: `dark_mode` (暗夜模式)

```json
{
  "preset": "dark_mode",
  "tokens": {
    "colors": {
      "primary": {
        "50": "#EEF2FF", "100": "#E0E7FF", "400": "#818CF8",
        "500": "#6366F1", "600": "#4F46E5", "700": "#4338CA", "800": "#3730A3"
      },
      "background": "#0F1117",
      "foreground": "#E1E4EA",
      "card": "#1A1D27",
      "border": "#2A2D37",
      "input": "#1A1D27",
      "muted": "#8B8FA3"
    }
  }
}
```

---

## 4. 图标上传与使用规范

### 4.1 上传约束

| 资产类型 | 格式 | 大小限制 | 尺寸建议 |
|---|---|---|---|
| Logo | SVG (优先), PNG | ≤ 500KB | 200×60 (横版), 60×60 (方版) |
| Favicon | ICO, PNG | ≤ 100KB | 32×32, 180×180 |
| App Icon (PWA) | PNG | ≤ 200KB | 512×512 |

### 4.2 Logo 在前端代码中的使用规范

Agent 生成的代码必须：

```tsx
// ✅ 正确：从 DesignSpec 取路径
import { designSpec } from "@/lib/design-spec";

<header>
  {designSpec.brand.logo ? (
    <img 
      src={designSpec.brand.logo.path} 
      alt={designSpec.brand.logo.alt}
      width={designSpec.brand.logo.width}
      height={designSpec.brand.logo.height}
      className="h-8 w-auto"
    />
  ) : (
    <span className="text-xl font-bold text-primary">
      {designSpec.brand.project_name}
    </span>
  )}
</header>
```

```html
<!-- ❌ 错误：硬编码路径 -->
<img src="/logo.png" alt="Logo" />

<!-- ❌ 错误：自由发挥设计 -->
<div style={{ backgroundColor: '#3B82F6' }}>My App</div>
```

### 4.3 Design Token 在 Tailwind 中的映射

生成的代码使用 Tailwind CSS，Design Token 映射为 CSS 变量：

```css
/* globals.css — Agent 自动生成 */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --color-primary-50: #EFF6FF;
    --color-primary-100: #DBEAFE;
    /* ... 所有 Token 映射为 CSS 变量 ... */
    --color-primary-500: #3B82F6;
    --color-primary-900: #1E3A8A;
    
    --color-background: #FFFFFF;
    --color-foreground: #111827;
    --color-card: #FFFFFF;
    --color-border: #E5E7EB;
    
    --font-sans: 'Inter', -apple-system, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
    
    --radius-sm: 4px;
    --radius-md: 6px;
    --radius-lg: 8px;
    --radius-xl: 12px;
  }
}
```

```js
// tailwind.config.js — Agent 自动生成
export default {
  theme: {
    extend: {
      colors: {
        primary: {
          50: 'var(--color-primary-50)',
          100: 'var(--color-primary-100)',
          // ...
          500: 'var(--color-primary-500)',
          900: 'var(--color-primary-900)',
        },
        background: 'var(--color-background)',
        foreground: 'var(--color-foreground)',
        card: 'var(--color-card)',
        border: 'var(--color-border)',
      },
      fontFamily: {
        sans: ['var(--font-sans)'],
        mono: ['var(--font-mono)'],
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
      },
    },
  },
};
```

---

## 5. Agent 如何消费 DesignSpec

### 5.1 Agent 约束规则（写进 Prompt）

```
## DESIGN SYSTEM (CRITICAL — DO NOT VIOLATE)

You MUST follow the DesignSpec below. This is NOT optional.

### Color Rules:
- ALL buttons, links, active states: use primary.500 → primary.700 (hover)
- ALL success indicators: use success color
- ALL error/destructive actions: use destructive color
- ALL backgrounds: use background color
- ALL text: use foreground color (not pure black)
- NEVER hardcode hex colors in components (e.g., no #3B82F6 in JSX)

### Typography Rules:
- ALL body text: font-sans, size base
- ALL headings: font-sans, sizes 2xl/3xl/4xl
- ALL code blocks: font-mono, size sm
- NEVER hardcode font-family in components

### Spacing Rules:
- Use spacing unit from DesignSpec (default 4px)
- All padding/margin must be multiples of the spacing unit
- Use Tailwind spacing classes (p-4, m-2, gap-6) — they are already configured

### Component Rules:
- ALL buttons: border_radius from DesignSpec.components.button
- ALL inputs: border_radius + focus_ring from DesignSpec.components.input
- ALL cards: border_radius + shadow + padding from DesignSpec.components.card
- ALL tables: follow DesignSpec.components.table exactly

### Icon/Logo Rules:
- If brand.logo exists: use it in the header, DO NOT create a text-only fallback
- If brand.favicon exists: include it in <head>
- DO NOT invent a logo or icon if none provided

### Violations:
- Hardcoded colors → REJECT
- Wrong font → REJECT  
- Incorrect spacing → REJECT
```

### 5.2 Agent Protocol 更新

DesignSpec 作为独立输入传给 Frontend Agent：

```json
// Frontend Agent 输入增加 design_spec 字段
{
  "openapi_spec": { ... },
  "pages": [ ... ],
  "backend_manifest": { ... },
  "design_spec": { ... }  // ← 新增：完整 DesignSpec JSON
}
```

---

## 6. 前端 UI：设计规范选择器

### 6.1 在需求输入页面的位置

```
┌──────────────────────────────────────────────────────┐
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │  🎨 设计规范                          [自定义 ▾] │  │
│  │                                                  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │  │
│  │  │ ████     │  │ ████     │  │ ████     │       │  │
│  │  │ 企业蓝   │  │ 自然绿   │  │ 暗夜模式  │       │  │
│  │  │ ✓ 选中   │  │          │  │          │       │  │
│  │  └──────────┘  └──────────┘  └──────────┘       │  │
│  │                                                  │  │
│  │  ┌──────────────────────────────────────────┐    │  │
│  │  │ 自定义规范（展开时）                        │    │  │
│  │  │                                           │    │  │
│  │  │  Logo:  [选择文件]  logo-v2.svg (已上传)   │    │  │
│  │  │  Favicon: [选择文件]  未上传               │    │  │
│  │  │                                           │    │  │
│  │  │  主色调:  [█████████████]  #3B82F6         │    │  │
│  │  │  字体:    [Inter ▾]                       │    │  │
│  │  │  圆角:    [━━━━━●━━━━]  6px                │    │  │
│  │  │  间距:    [4px ▾]                          │    │  │
│  │  │                                           │    │  │
│  │  │  ┌──────────────────────────────────┐      │    │  │
│  │  │  │  预览                              │      │    │  │
│  │  │  │  ┌──────────────────────────┐     │      │    │  │
│  │  │  │  │ [Logo]  首页  历史        │     │      │    │  │
│  │  │  │  ├──────────────────────────┤     │      │    │  │
│  │  │  │  │                          │     │      │    │  │
│  │  │  │  │   [保存]  [取消]         │     │      │    │  │
│  │  │  │  │                          │     │      │    │  │
│  │  │  │  └──────────────────────────┘     │      │    │  │
│  │  │  └──────────────────────────────────┘      │    │  │
│  │  └──────────────────────────────────────────┘    │  │
│  └─────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### 6.2 组件状态

| 状态 | 条件 | 表现 |
|---|---|---|
| **默认** | 未选择 | 预设「企业蓝」默认选中 |
| **预设选中** | 点击预设卡片 | 卡片高亮边框 + ✓ 标记，自定义面板折叠 |
| **自定义展开** | 点击「自定义」 | 预设卡片取消选中，自定义面板展开 |
| **上传中** | 文件上传中 | Logo/Favicon 区域显示进度条 |
| **上传失败** | 格式/大小不符 | 红色错误文字：「仅支持 SVG/PNG，文件不超过 500KB」 |
| **预览更新** | 修改任意选项 | 右侧预览面板实时更新 |

### 6.3 数据流

```
用户选择预设 / 修改自定义项
      │
      ▼
前端构建 DesignSpec JSON
      │
      ▼
POST /api/v1/projects 时一并提交
  {
    "requirement": "...",
    "design_spec": { ... }
  }
      │
      ▼
Orchestrator 将 design_spec 注入 Frontend Agent 的输入
```

---

## 7. 后端 API 扩展

### 7.1 图标上传

```
POST /api/v1/assets/upload

Content-Type: multipart/form-data

Form Fields:
  file: (binary) — 图标文件
  type: "logo" | "favicon" | "app_icon"
  project_id: UUID (optional — 关联到项目)

Response (201):
{
  "success": true,
  "data": {
    "asset_id": "uuid",
    "path": "assets/logo-abc123.svg",
    "url": "/api/v1/assets/logo-abc123.svg",
    "type": "logo",
    "size_bytes": 45678,
    "mime_type": "image/svg+xml"
  }
}

Errors:
  400 — 文件格式不支持
  413 — 文件过大
```

### 7.2 设计预设查询

```
GET /api/v1/design-presets

Response (200):
{
  "success": true,
  "data": {
    "presets": [
      {
        "id": "professional_blue",
        "name": "企业蓝",
        "description": "专业、稳重，适合企业管理类系统",
        "preview_colors": ["#3B82F6", "#FFFFFF", "#111827"],
        "tokens": { ... }
      },
      {
        "id": "nature_green", 
        "name": "自然绿",
        "description": "清新、自然，适合环保/医疗类系统",
        "preview_colors": ["#10B981", "#FAFDF7", "#1A2E1A"],
        "tokens": { ... }
      },
      {
        "id": "dark_mode",
        "name": "暗夜模式",
        "description": "护眼、现代，适合开发工具/数据平台",
        "preview_colors": ["#6366F1", "#0F1117", "#E1E4EA"],
        "tokens": { ... }
      }
    ]
  }
}
```

---

## 8. 项目文件结构（更新）

生成的项目中增加设计资产文件夹：

```
project-output/
├── assets/                    # ← 新增
│   ├── logo.svg
│   ├── favicon.ico
│   └── design-spec.json       # ← 新增：DesignSpec 快照
├── backend/
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── design-spec.ts  # ← 新增：DesignSpec TypeScript 类型 + 导入
│   │   │   └── utils.ts
│   │   ├── styles/
│   │   │   └── globals.css     # ← 更新：包含 CSS 变量
│   │   └── ...
│   ├── tailwind.config.js      # ← 更新：引用 CSS 变量
│   └── index.html              # ← 更新：包含 favicon 引用
├── docker-compose.yml
└── README.md
```

### 8.1 `design-spec.ts`（Agent 自动生成）

```typescript
// 此文件由 Frontend Agent 自动生成，基于用户的 DesignSpec
// DO NOT EDIT MANUALLY

export interface DesignSpec {
  brand: {
    logo: { path: string; alt: string; width: number; height: number } | null;
    favicon: { path: string } | null;
    project_name: string;
  };
  tokens: {
    colors: Record<string, string | Record<string, string>>;
    typography: {
      font_family: { sans: string; mono: string };
      font_size: Record<string, string>;
    };
    spacing: { unit: number; scale: Record<string, string> };
    border_radius: Record<string, string>;
  };
}

export const designSpec: DesignSpec = {
  brand: {
    logo: {
      path: "/assets/logo.svg",
      alt: "我的项目",
      width: 200,
      height: 60
    },
    favicon: {
      path: "/assets/favicon.ico"
    },
    project_name: "我的项目"
  },
  tokens: {
    colors: {
      primary: {
        "500": "#3B82F6",
        "600": "#2563EB"
      },
      background: "#FFFFFF",
      foreground: "#111827"
    },
    // ... 完整 Token
  }
};
```

---

## 9. Agent 代码生成强制约束总结

| 约束类别 | 强制规则 | 违反后果 |
|---|---|---|
| **颜色** | 必须从 DesignSpec.tokens.colors 取值，禁止硬编码 | 代码 Review Agent 标记为 `violation` → 重新生成 |
| **字体** | 必须使用 DesignSpec.tokens.typography.font_family | 同上 |
| **圆角** | 必须使用 DesignSpec.tokens.border_radius | 同上 |
| **间距** | 必须是 DesignSpec.tokens.spacing.unit 的整数倍 | 同上 |
| **Logo** | 如果 brand.logo 存在，Header 必须展示 | 同上 |
| **Favicon** | 如果 brand.favicon 存在，index.html 必须包含 | 同上 |
| **组件样式** | Button/Input/Card/Table 必须使用 DesignSpec.components 配置 | 同上 |

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, ChevronDown } from 'lucide-react';
import { toast } from 'sonner';

const TEMPLATES = [
  { value: 'crud_admin', label: 'CRUD 管理后台', icon: '📋' },
  { value: 'rest_api', label: 'REST API 服务', icon: '🔌' },
  { value: 'dashboard', label: '数据看板', icon: '📊' },
];

const EXAMPLES = [
  {
    title: '用户管理系统',
    template: 'crud_admin',
    text: '我要做一个用户管理系统，支持用户的增删改查、角色管理（管理员、编辑、查看者）、分页查询和搜索',
  },
  {
    title: '博客 API 服务',
    template: 'rest_api',
    text: 'Build a blog API with posts and comments. Posts have title, content, tags. Comments belong to posts and have author and body.',
  },
  {
    title: '销售数据看板',
    template: 'dashboard',
    text: '我要做一个销售数据看板，展示总销售额、订单数、客户数统计卡片，月度销售趋势图，产品分类饼图，以及最近的订单列表',
  },
];

export function HomePage() {
  const navigate = useNavigate();
  const [requirement, setRequirement] = useState('');
  const [template, setTemplate] = useState('crud_admin');
  const [submitting, setSubmitting] = useState(false);

  const charCount = requirement.length;
  const isValid = charCount >= 10 && charCount <= 2000;

  const handleSubmit = async () => {
    if (!isValid) return;

    setSubmitting(true);
    try {
      const response = await fetch('/api/v1/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          requirement,
          template,
          language: 'zh',
          constraints: { database: 'sqlite' },
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error?.message || '创建失败');
      }

      const { data } = await response.json();
      navigate(`/projects/${data.id}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '生成失败，请重试');
      setSubmitting(false);
    }
  };

  const fillExample = (text: string, tpl: string) => {
    setRequirement(text);
    setTemplate(tpl);
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-12 sm:py-20">
      {/* Hero */}
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold tracking-tight mb-3">
          🏭 AI Project Factory
        </h1>
        <p className="text-lg text-muted">
          用自然语言描述需求，AI 自动生成完整项目代码
        </p>
      </div>

      {/* Template Selector */}
      <div className="mb-4">
        <div className="relative inline-block">
          <select
            value={template}
            onChange={(e) => setTemplate(e.target.value)}
            className="appearance-none bg-white border rounded-md px-3 py-2 pr-8 text-sm font-medium cursor-pointer hover:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {TEMPLATES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.icon} {t.label}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none text-muted" />
        </div>
      </div>

      {/* Requirement Input */}
      <div className="mb-2">
        <textarea
          value={requirement}
          onChange={(e) => setRequirement(e.target.value)}
          placeholder="描述你想要的项目，例如：我要做一个用户管理系统，支持用户的增删改查..."
          rows={6}
          maxLength={2000}
          className="w-full border rounded-lg px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          disabled={submitting}
        />
      </div>

      {/* Character Count + Validation */}
      <div className="flex items-center justify-between mb-6">
        <span className="text-xs text-muted">
          {charCount} / 2000
        </span>
        {charCount > 0 && charCount < 10 && (
          <span className="text-xs text-red-500">
            请至少输入 10 个字
          </span>
        )}
        {charCount > 2000 && (
          <span className="text-xs text-red-500">
            已超过 2000 字限制
          </span>
        )}
      </div>

      {/* Submit Button */}
      <div className="mb-12">
        <button
          onClick={handleSubmit}
          disabled={!isValid || submitting}
          className="w-full py-3 rounded-lg bg-primary-600 text-white font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {submitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              正在分析需求...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              生成项目
            </>
          )}
        </button>
      </div>

      {/* Examples */}
      <div className="text-center">
        <p className="text-sm text-muted mb-4">或者试试这些例子</p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {EXAMPLES.map((example) => (
            <button
              key={example.title}
              onClick={() => fillExample(example.text, example.template)}
              className="border rounded-lg p-4 text-left hover:border-primary-300 hover:bg-primary-50/50 transition-colors"
            >
              <div className="text-2xl mb-2">
                {TEMPLATES.find((t) => t.value === example.template)?.icon}
              </div>
              <div className="font-medium text-sm">{example.title}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

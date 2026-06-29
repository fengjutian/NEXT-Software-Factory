import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, FileCode, Clock, CheckCircle, XCircle, ArrowRight } from 'lucide-react';
import { listProjects, type Project } from '@/api/client';

export function HistoryPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const pageSize = 20;

  useEffect(() => {
    fetchProjects();
  }, [page, search]);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listProjects(page, pageSize);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setProjects((data as any).items || []);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setTotal((data as any).total || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  // ── Loading ──
  if (loading && projects.length === 0) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">历史项目</h1>
        <div className="space-y-3 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-gray-200 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  // ── Error ──
  if (error && projects.length === 0) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 text-center">
        <XCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <p className="text-muted mb-4">{error}</p>
        <button
          onClick={fetchProjects}
          className="text-primary-600 hover:underline text-sm"
        >
          重试
        </button>
      </div>
    );
  }

  // ── Empty ──
  if (!loading && projects.length === 0) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <FileCode className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h2 className="text-lg font-semibold mb-2">还没有项目</h2>
        <p className="text-muted mb-4">创建你的第一个 AI 生成项目吧</p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          开始创建
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">历史项目</h1>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
        <input
          type="text"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          placeholder="搜索项目..."
          className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      {/* Project List */}
      <div className="space-y-3">
        {projects.map((project) => (
          <Link
            key={project.id}
            to={`/projects/${project.id}`}
            className="block bg-white border rounded-lg p-4 hover:border-primary-300 hover:shadow-sm transition-all"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <StatusIcon status={project.status} />
                  <h3 className="font-semibold truncate">
                    {project.summary || '未命名项目'}
                  </h3>
                </div>
                <p className="text-sm text-muted truncate mb-2">
                  {project.requirement?.slice(0, 100)}
                </p>
                <div className="flex items-center gap-4 text-xs text-muted">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatTime(project.created_at)}
                  </span>
                  <StatusLabel status={project.status} />
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-muted shrink-0 ml-4" />
            </div>
          </Link>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="px-3 py-1.5 border rounded text-sm disabled:opacity-50 hover:bg-gray-50"
          >
            上一页
          </button>
          <span className="text-sm text-muted">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="px-3 py-1.5 border rounded text-sm disabled:opacity-50 hover:bg-gray-50"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'done':
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'failed':
      return <XCircle className="w-4 h-4 text-red-500" />;
    default:
      return <Clock className="w-4 h-4 text-blue-500 animate-pulse" />;
  }
}

function StatusLabel({ status }: { status: string }) {
  const map: Record<string, string> = {
    pending: '排队中',
    analyzing: '分析中',
    generating_backend: '生成后端',
    generating_frontend: '生成前端',
    testing: '测试中',
    done: '已完成',
    failed: '失败',
  };
  return <span>{map[status] || status}</span>;
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes} 分钟前`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} 小时前`;
  return d.toLocaleDateString('zh-CN');
}

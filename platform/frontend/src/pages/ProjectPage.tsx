import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Download,
  FileCode,
  CheckCircle,
  AlertCircle,
  RotateCw,
  FileText,
  ExternalLink,
} from 'lucide-react';
import { toast } from 'sonner';
import { useProject } from '@/hooks/useProject';
import { PipelineProgress } from '@/components/PipelineProgress';
import { FileTree } from '@/components/FileTree';
import { CodePreview } from '@/components/CodePreview';
import { StatCard } from '@/components/StatCard';
import { getDownloadUrl } from '@/api/client';
import type { FileContent } from '@/api/client';
import { useState } from 'react';

export function ProjectPage() {
  const { id } = useParams<{ id: string }>();
  const { project, fileTree, spec, loading, error, loadFile } = useProject(id);
  const [selectedFile, setSelectedFile] = useState<FileContent | null>(null);
  const [fileLoading, setFileLoading] = useState(false);

  const handleFileClick = async (path: string) => {
    setFileLoading(true);
    const content = await loadFile(path);
    setSelectedFile(content);
    setFileLoading(false);
  };

  // ── Loading state ──
  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-48 mb-6" />
        <div className="h-6 bg-gray-200 rounded w-96 mb-4" />
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-10 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    );
  }

  // ── Error state ──
  if (error || !project) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center">
        <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <h2 className="text-lg font-semibold mb-2">加载失败</h2>
        <p className="text-muted mb-4">{error || '项目不存在'}</p>
        <Link to="/" className="text-primary-600 hover:underline">
          返回首页
        </Link>
      </div>
    );
  }

  const isRunning =
    project.status !== 'done' && project.status !== 'failed';
  const isFailed = project.status === 'failed';
  const isDone = project.status === 'done';
  const stats = project.stats;

  // ── Running / Failed state ──
  if (!isDone) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Back */}
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-sm text-muted hover:text-foreground mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          返回首页
        </Link>

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">
              {project.summary || '项目生成中'}
            </h1>
          </div>
          <StatusBadge status={project.status} />
        </div>

        {/* Pipeline Progress */}
        <div className="bg-white border rounded-lg p-6 mb-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted mb-4">
            流水线进度
          </h2>
          <PipelineProgress steps={project.progress?.steps || []} />
        </div>

        {/* Error panel for failed state */}
        {isFailed && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-red-800 mb-1">生成失败</h3>
                <p className="text-sm text-red-700 mb-4">
                  {project.error_message || '未知错误'}
                </p>
                <div className="flex gap-3">
                  <Link
                    to="/"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-red-300 rounded-md text-sm text-red-700 hover:bg-red-50"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    修改需求
                  </Link>
                  <button
                    onClick={() => window.location.reload()}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-600 text-white rounded-md text-sm hover:bg-red-700"
                  >
                    <RotateCw className="w-3.5 h-3.5" />
                    重试
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Spec preview (if available) */}
        {spec && (
          <div className="mt-6 bg-white border rounded-lg p-6">
            <h3 className="text-sm font-semibold mb-3">📋 需求分析结果</h3>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-muted">实体</span>
                <p className="font-medium">{spec.entities?.length || 0}</p>
              </div>
              <div>
                <span className="text-muted">API 端点</span>
                <p className="font-medium">{spec.api_endpoints?.length || 0}</p>
              </div>
              <div>
                <span className="text-muted">页面</span>
                <p className="font-medium">{spec.pages?.length || 0}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── Done state ──
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Back */}
      <Link
        to="/"
        className="inline-flex items-center gap-1 text-sm text-muted hover:text-foreground mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        返回首页
      </Link>

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{project.summary || '未命名项目'}</h1>
        </div>
        <StatusBadge status={project.status} />
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          <StatCard
            label="生成文件"
            value={stats.total_files || 0}
            icon={<FileCode className="w-4 h-4" />}
          />
          <StatCard
            label="代码行数"
            value={(stats.total_lines || 0).toLocaleString()}
            icon={<FileText className="w-4 h-4" />}
          />
          <StatCard
            label="测试通过"
            value={stats.tests_passed !== undefined ? `${stats.tests_passed}/${(stats.tests_passed || 0) + (stats.tests_failed || 0)}` : '—'}
            icon={<CheckCircle className="w-4 h-4 text-green-500" />}
          />
          <StatCard
            label="测试覆盖率"
            value={stats.test_coverage !== undefined ? `${stats.test_coverage}%` : '—'}
            icon={<CheckCircle className="w-4 h-4 text-blue-500" />}
          />
        </div>
      )}

      {/* File tree + Code preview */}
      <div className="flex border rounded-lg overflow-hidden bg-white" style={{ minHeight: '500px' }}>
        {/* File Tree */}
        <div className="w-72 shrink-0 border-r bg-gray-50/50 overflow-y-auto">
          <div className="px-3 py-2 text-xs font-semibold text-muted uppercase border-b">
            📁 文件
          </div>
          {fileTree ? (
            <FileTree
              tree={fileTree}
              onFileClick={handleFileClick}
              selectedPath={selectedFile?.path}
            />
          ) : (
            <div className="p-4 text-sm text-muted">加载中...</div>
          )}
        </div>

        {/* Code Preview */}
        <div className="flex-1 overflow-hidden">
          <CodePreview
            content={selectedFile?.content ?? null}
            language={selectedFile?.language ?? 'text'}
            fileName={selectedFile?.path}
            loading={fileLoading}
          />
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3 mt-6">
        <a
          href={getDownloadUrl(id!)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
          onClick={() => toast.success('开始下载项目 ZIP')}
        >
          <Download className="w-4 h-4" />
          下载 ZIP
        </a>
        <button
          onClick={() => {
            navigator.clipboard.writeText(`${window.location.origin}/api/v1/projects/${id}/download`);
            toast.success('下载链接已复制');
          }}
          className="inline-flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50 transition-colors text-sm"
        >
          <ExternalLink className="w-4 h-4" />
          复制下载链接
        </button>
      </div>

      {/* Spec details (collapsed by default in done state) */}
      {spec && (
        <details className="mt-6 bg-white border rounded-lg p-6">
          <summary className="text-sm font-semibold cursor-pointer">
            📋 需求分析详情
          </summary>
          <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-muted">实体</span>
              <ul className="mt-1 space-y-0.5">
                {spec.entities?.map((e) => (
                  <li key={e.id} className="font-medium">
                    {e.display_name || e.name}
                    <span className="text-xs text-muted ml-1">
                      ({e.fields?.length || 0} 字段)
                    </span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <span className="text-muted">API 端点</span>
              <ul className="mt-1 space-y-0.5">
                {spec.api_endpoints?.map((ep) => (
                  <li key={ep.id} className="font-mono text-xs">
                    <span className="font-medium">{ep.method}</span> {ep.path}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <span className="text-muted">页面</span>
              <ul className="mt-1 space-y-0.5">
                {spec.pages?.map((p) => (
                  <li key={p.id} className="text-xs">
                    {p.display_name || p.name}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </details>
      )}
    </div>
  );
}

// ── StatusBadge ──

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  pending: { label: '排队中', className: 'bg-gray-100 text-gray-600' },
  analyzing: { label: '需求分析中', className: 'bg-blue-100 text-blue-700' },
  generating_backend: { label: '生成后端', className: 'bg-purple-100 text-purple-700' },
  generating_frontend: { label: '生成前端', className: 'bg-orange-100 text-orange-700' },
  testing: { label: '测试中', className: 'bg-yellow-100 text-yellow-700' },
  done: { label: '已完成', className: 'bg-green-100 text-green-700' },
  failed: { label: '失败', className: 'bg-red-100 text-red-700' },
};

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] || { label: status, className: 'bg-gray-100' };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.className}`}>
      {config.label}
    </span>
  );
}

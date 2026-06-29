import { Copy, Check } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';

interface CodePreviewProps {
  content: string | null;
  language: string;
  fileName?: string;
  loading?: boolean;
}

export function CodePreview({ content, language, fileName, loading }: CodePreviewProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!content) return;
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Loading state
  if (loading) {
    return (
      <div className="p-4 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-3" />
        <div className="h-3 bg-gray-200 rounded w-1/2 mb-2" />
        <div className="h-3 bg-gray-200 rounded w-2/3 mb-2" />
        <div className="h-3 bg-gray-200 rounded w-1/3" />
      </div>
    );
  }

  // Empty state
  if (content === null) {
    return (
      <div className="flex items-center justify-center h-full text-muted text-sm p-8">
        点击左侧文件查看代码
      </div>
    );
  }

  // Empty content
  if (content === '') {
    return (
      <div className="flex items-center justify-center h-full text-muted text-sm p-8">
        文件为空
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b bg-gray-50">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted">{fileName || 'untitled'}</span>
          {language && (
            <span className="text-xs bg-gray-200 px-1.5 py-0.5 rounded">{language}</span>
          )}
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-xs text-muted hover:text-foreground transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-green-500" />
              已复制
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              复制
            </>
          )}
        </button>
      </div>

      {/* Code */}
      <div className="flex-1 overflow-auto">
        <pre className="p-4 text-sm leading-relaxed">
          <code>{content}</code>
        </pre>
      </div>
    </div>
  );
}

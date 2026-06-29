import { useState } from 'react';
import { ChevronRight, ChevronDown, File, Folder } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { FileTreeNode as FileTreeNodeType } from '@/api/client';

interface FileTreeProps {
  tree: FileTreeNodeType[];
  onFileClick: (path: string) => void;
  selectedPath?: string;
}

export function FileTree({ tree, onFileClick, selectedPath }: FileTreeProps) {
  if (!tree || tree.length === 0) {
    return (
      <div className="text-sm text-muted p-4 text-center">
        暂无文件
      </div>
    );
  }

  return (
    <div className="py-2">
      {tree.map((node) => (
        <TreeNode
          key={node.name}
          node={node}
          depth={0}
          onFileClick={onFileClick}
          selectedPath={selectedPath}
          parentPath=""
        />
      ))}
    </div>
  );
}

function TreeNode({
  node,
  depth,
  onFileClick,
  selectedPath,
  parentPath,
}: {
  node: FileTreeNodeType;
  depth: number;
  onFileClick: (path: string) => void;
  selectedPath?: string;
  parentPath: string;
}) {
  const [expanded, setExpanded] = useState(depth < 2); // auto-expand first 2 levels
  const currentPath = parentPath ? `${parentPath}/${node.name}` : node.name;

  const fileIconMap: Record<string, string> = {
    model: '📦',
    schema: '📋',
    service: '⚙️',
    router: '🔀',
    config: '🔧',
    migration: '📜',
    test: '🧪',
    docker: '🐳',
    doc: '📄',
    page: '📑',
    component: '🧩',
    hook: '🪝',
    api_client: '🔌',
  };

  if (node.type === 'directory') {
    return (
      <div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 w-full px-2 py-1 text-sm hover:bg-gray-100 rounded text-left"
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
        >
          {expanded ? (
            <ChevronDown className="w-3.5 h-3.5 text-muted shrink-0" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-muted shrink-0" />
          )}
          <Folder className="w-3.5 h-3.5 text-blue-500 shrink-0" />
          <span className="font-medium truncate">{node.name}</span>
        </button>
        {expanded && node.children && (
          <div>
            {node.children.map((child) => (
              <TreeNode
                key={child.name}
                node={child}
                depth={depth + 1}
                onFileClick={onFileClick}
                selectedPath={selectedPath}
                parentPath={currentPath}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  // File node
  const isSelected = selectedPath === currentPath;
  const icon = fileIconMap[node.file_type || ''] || '📄';

  return (
    <button
      onClick={() => onFileClick(currentPath)}
      className={cn(
        'flex items-center gap-1 w-full px-2 py-1 text-sm hover:bg-gray-100 rounded text-left',
        isSelected && 'bg-primary-50 text-primary-700 font-medium',
      )}
      style={{ paddingLeft: `${depth * 16 + 8}px` }}
    >
      <File className="w-3.5 h-3.5 text-muted shrink-0" />
      <span className="text-xs mr-1">{icon}</span>
      <span className="truncate">{node.name}</span>
      {node.size && (
        <span className="text-xs text-muted ml-auto shrink-0">
          {formatSize(node.size)}
        </span>
      )}
    </button>
  );
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

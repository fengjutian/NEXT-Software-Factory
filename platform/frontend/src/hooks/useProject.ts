import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from './useWebSocket';
import {
  getProject,
  getFileTree,
  getFileContent,
  getSpec,
  type Project,
  type FileTreeNode,
  type FileContent,
  type RequirementSpec,
} from '@/api/client';

interface ProjectState {
  project: Project | null;
  fileTree: FileTreeNode[] | null;
  spec: RequirementSpec | null;
  loading: boolean;
  error: string | null;
}

interface ProjectActions {
  loadFile: (path: string) => Promise<FileContent | null>;
  refresh: () => void;
}

export function useProject(id: string | undefined): ProjectState & ProjectActions {
  const [project, setProject] = useState<Project | null>(null);
  const [fileTree, setFileTree] = useState<FileTreeNode[] | null>(null);
  const [spec, setSpec] = useState<RequirementSpec | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch project detail
  const fetchProject = useCallback(async () => {
    if (!id) return;
    try {
      const data = await getProject(id);
      setProject(data);
      setError(null);

      // If done or failed, also fetch files and spec
      if (data.status === 'done' || data.status === 'failed') {
        loadFiles();
        loadSpec();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
    }
  }, [id]);

  const loadFiles = async () => {
    if (!id) return;
    try {
      const { tree } = await getFileTree(id);
      setFileTree(tree);
    } catch {
      // files might not be available yet
    }
  };

  const loadSpec = async () => {
    if (!id) return;
    try {
      const { requirement_spec } = await getSpec(id);
      setSpec(requirement_spec);
    } catch {
      // spec might not be available yet
    }
  };

  const loadFile = async (path: string): Promise<FileContent | null> => {
    if (!id) return null;
    try {
      return await getFileContent(id, path);
    } catch {
      return null;
    }
  };

  // Handle WebSocket events
  const handleWsEvent = useCallback(
    (data: Record<string, unknown>) => {
      const type = data.type as string;

      switch (type) {
        case 'step_started':
        case 'step_completed':
        case 'agent_log':
          // Update step status in project
          setProject((prev) => {
            if (!prev || !prev.progress) return prev;
            const steps = prev.progress.steps.map((s) => {
              if (type === 'step_started' && s.name === data.step) {
                return { ...s, status: 'running' as const };
              }
              if (type === 'step_completed' && s.name === data.step) {
                return {
                  ...s,
                  status: 'completed' as const,
                  duration_ms: data.duration_ms as number,
                  summary: data.summary as string,
                };
              }
              return s;
            });
            return {
              ...prev,
              progress: {
                ...prev.progress,
                current_step: type === 'step_started' ? (data.step as string) : prev.progress.current_step,
                steps,
              },
            };
          });
          break;

        case 'step_failed':
          setProject((prev) => {
            if (!prev || !prev.progress) return prev;
            const steps = prev.progress.steps.map((s) =>
              s.name === data.step ? { ...s, status: 'failed' as const } : s,
            );
            return {
              ...prev,
              status: 'failed',
              progress: { ...prev.progress, steps },
            };
          });
          break;

        case 'pipeline_completed':
          // Refresh full project data
          fetchProject();
          loadFiles();
          loadSpec();
          break;

        case 'pipeline_failed':
          fetchProject();
          break;
      }
    },
    [fetchProject],
  );

  useWebSocket(id, handleWsEvent);

  useEffect(() => {
    setLoading(true);
    setProject(null);
    setFileTree(null);
    setSpec(null);
    fetchProject();
  }, [fetchProject]);

  return {
    project,
    fileTree,
    spec,
    loading,
    error,
    loadFile,
    refresh: fetchProject,
  };
}

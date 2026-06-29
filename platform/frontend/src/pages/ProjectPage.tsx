import { useParams } from 'react-router-dom';

export function ProjectPage() {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-4">项目详情</h1>
      <p className="text-muted">项目 ID: {id}</p>
      <p className="text-muted mt-2">🚧 进度展示和代码预览功能即将实现</p>
    </div>
  );
}

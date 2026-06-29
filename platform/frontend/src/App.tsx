import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import { MainLayout } from '@/components/MainLayout';
import { HomePage } from '@/pages/HomePage';
import { ProjectPage } from '@/pages/ProjectPage';
import { HistoryPage } from '@/pages/HistoryPage';

export function App() {
  return (
    <ErrorBoundary>
      <Toaster position="top-right" richColors />
      <Routes>
        <Route element={<MainLayout />}>
          <Route index element={<HomePage />} />
          <Route path="projects/:id" element={<ProjectPage />} />
          <Route path="history" element={<HistoryPage />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
}

function ErrorBoundary({ children }: { children: React.ReactNode }) {
  const [error, setError] = React.useState<Error | null>(null);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <div className="text-center">
          <h1 className="text-xl font-bold mb-2">出错了</h1>
          <p className="text-muted mb-4">{error.message}</p>
          <button
            onClick={() => { setError(null); window.location.reload(); }}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg"
          >
            刷新页面
          </button>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundaryInner onError={setError}>
      {children}
    </ErrorBoundaryInner>
  );
}

class ErrorBoundaryInner extends React.Component<{
  children: React.ReactNode;
  onError: (e: Error) => void;
}> {
  componentDidCatch(error: Error) {
    this.props.onError(error);
  }
  render() {
    return this.props.children;
  }
}

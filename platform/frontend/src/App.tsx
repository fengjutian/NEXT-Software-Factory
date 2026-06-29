import { Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import { MainLayout } from '@/components/MainLayout';
import { HomePage } from '@/pages/HomePage';
import { ProjectPage } from '@/pages/ProjectPage';
import { HistoryPage } from '@/pages/HistoryPage';

export function App() {
  return (
    <>
      <Toaster position="top-right" richColors />
      <Routes>
        <Route element={<MainLayout />}>
          <Route index element={<HomePage />} />
          <Route path="projects/:id" element={<ProjectPage />} />
          <Route path="history" element={<HistoryPage />} />
        </Route>
      </Routes>
    </>
  );
}

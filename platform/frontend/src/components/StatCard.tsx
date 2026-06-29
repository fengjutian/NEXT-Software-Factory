import { type ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface StatCardProps {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
  className?: string;
}

export function StatCard({ label, value, icon, className }: StatCardProps) {
  return (
    <div className={cn('bg-white border rounded-lg p-4', className)}>
      <div className="flex items-center gap-2 mb-1">
        {icon && <span className="text-muted">{icon}</span>}
        <span className="text-xs text-muted uppercase tracking-wide">{label}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}

import { CheckCircle, Loader2, XCircle, SkipForward, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { StepInfo } from '@/api/client';

interface PipelineProgressProps {
  steps: StepInfo[];
}

export function PipelineProgress({ steps }: PipelineProgressProps) {
  return (
    <div className="space-y-1">
      {steps.map((step, i) => (
        <div key={step.name}>
          <StepItem step={step} isLast={i === steps.length - 1} />
        </div>
      ))}
    </div>
  );
}

function StepItem({ step, isLast }: { step: StepInfo; isLast: boolean }) {
  const isRunning = step.status === 'running';
  const isCompleted = step.status === 'completed';
  const isFailed = step.status === 'failed';
  const isSkipped = step.status === 'skipped' || (step as Record<string, unknown>).status === 'skipped';

  return (
    <div className="flex items-start gap-3">
      {/* Icon column */}
      <div className="flex flex-col items-center pt-0.5">
        <div
          className={cn(
            'w-7 h-7 rounded-full flex items-center justify-center border-2',
            isCompleted && 'bg-green-500 border-green-500 text-white',
            isRunning && 'border-blue-500 text-blue-500',
            isFailed && 'bg-red-500 border-red-500 text-white',
            isSkipped && 'border-gray-300 text-gray-400',
            !isCompleted && !isRunning && !isFailed && !isSkipped && 'border-gray-200 text-gray-300',
          )}
        >
          {isCompleted && <CheckCircle className="w-4 h-4" />}
          {isRunning && <Loader2 className="w-4 h-4 animate-spin" />}
          {isFailed && <XCircle className="w-4 h-4" />}
          {isSkipped && <SkipForward className="w-4 h-4" />}
          {!isCompleted && !isRunning && !isFailed && !isSkipped && (
            <Clock className="w-4 h-4" />
          )}
        </div>
        {!isLast && (
          <div
            className={cn(
              'w-0.5 h-6',
              isCompleted ? 'bg-green-500' : 'bg-gray-200',
            )}
          />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 pb-4">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              'text-sm font-medium',
              isCompleted && 'text-green-700',
              isRunning && 'text-blue-700',
              isFailed && 'text-red-700',
              isSkipped && 'text-gray-400 line-through',
            )}
          >
            {step.label}
          </span>
          {step.duration_ms && (
            <span className="text-xs text-muted">
              {(step.duration_ms / 1000).toFixed(0)}s
            </span>
          )}
        </div>
        {step.summary && !isRunning && (
          <p className="text-xs text-muted mt-0.5">{step.summary}</p>
        )}
        {isRunning && (
          <p className="text-xs text-blue-500 mt-0.5 animate-pulse">进行中...</p>
        )}
      </div>
    </div>
  );
}

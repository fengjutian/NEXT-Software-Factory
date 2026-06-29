import { useState } from 'react';
import { Palette, Upload, X } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface DesignSpec {
  preset: string;
  brand?: {
    project_name?: string;
    logo_path?: string;
    favicon_path?: string;
  };
  tokens?: Record<string, unknown>;
}

interface DesignSpecSelectorProps {
  value: DesignSpec;
  onChange: (spec: DesignSpec) => void;
}

const PRESETS = [
  {
    id: 'professional_blue',
    name: '企业蓝',
    description: '专业、稳重',
    colors: ['#3B82F6', '#FFFFFF', '#111827'],
  },
  {
    id: 'nature_green',
    name: '自然绿',
    description: '清新、自然',
    colors: ['#10B981', '#FAFDF7', '#1A2E1A'],
  },
  {
    id: 'dark_mode',
    name: '暗夜模式',
    description: '护眼、现代',
    colors: ['#6366F1', '#0F1117', '#E1E4EA'],
  },
];

export function DesignSpecSelector({ value, onChange }: DesignSpecSelectorProps) {
  const [expanded, setExpanded] = useState(false);

  const handlePreset = (presetId: string) => {
    onChange({ preset: presetId });
    setExpanded(false);
  };

  const handleCustom = () => {
    onChange({ preset: 'custom' });
    setExpanded(true);
  };

  return (
    <div className="border rounded-lg p-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm font-medium text-muted hover:text-foreground w-full text-left"
      >
        <Palette className="w-4 h-4" />
        <span>🎨 设计规范</span>
        <span className="text-xs text-muted ml-auto">
          {PRESETS.find(p => p.id === value.preset)?.name || '自定义'}
        </span>
      </button>

      <div className={cn('mt-3 space-y-3', !expanded && 'hidden')}>
        {/* Preset cards */}
        <div className="grid grid-cols-3 gap-2">
          {PRESETS.map((preset) => (
            <button
              key={preset.id}
              onClick={() => handlePreset(preset.id)}
              className={cn(
                'border rounded-lg p-3 text-left transition-colors',
                value.preset === preset.id
                  ? 'border-primary-500 bg-primary-50 ring-1 ring-primary-500'
                  : 'hover:border-gray-300',
              )}
            >
              <div className="flex gap-0.5 mb-2">
                {preset.colors.map((c, i) => (
                  <div
                    key={i}
                    className="w-5 h-5 rounded-full border"
                    style={{ backgroundColor: c }}
                  />
                ))}
              </div>
              <div className="text-xs font-medium">{preset.name}</div>
              <div className="text-xs text-muted">{preset.description}</div>
            </button>
          ))}
        </div>

        {/* Custom toggle */}
        <button
          onClick={handleCustom}
          className={cn(
            'w-full border rounded-lg p-3 text-sm text-left transition-colors',
            value.preset === 'custom'
              ? 'border-primary-500 bg-primary-50'
              : 'hover:border-gray-300',
          )}
        >
          🎨 自定义规范（上传 Logo、选择色板...）
        </button>
      </div>
    </div>
  );
}

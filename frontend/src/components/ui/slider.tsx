import React from 'react';
import { cn } from '@/lib/utils';

export interface SliderProps {
  value: number | [number, number];
  onValueChange: (value: number | [number, number]) => void;
  min?: number;
  max?: number;
  step?: number;
  className?: string;
  disabled?: boolean;
}

export const Slider: React.FC<SliderProps> = ({
  value,
  onValueChange,
  min = 0,
  max = 100,
  step = 0.1,
  className,
  disabled = false,
}) => {
  const isDual = Array.isArray(value);

  if (isDual) {
    const [start, end] = value;
    const startPercent = Math.min(100, Math.max(0, ((start - min) / (max - min)) * 100));
    const endPercent = Math.min(100, Math.max(0, ((end - min) / (max - min)) * 100));

    return (
      <div className={cn('relative flex w-full touch-none select-none items-center py-2', className)}>
        {/* Track */}
        <div className="relative h-2 w-full grow overflow-hidden rounded-full bg-slate-800">
          <div
            className="absolute h-full bg-cyan-400"
            style={{
              left: `${startPercent}%`,
              width: `${Math.max(0, endPercent - startPercent)}%`,
            }}
          />
        </div>

        {/* Dual Input Overlays */}
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={start}
          disabled={disabled}
          onChange={(e) => {
            const newStart = Math.min(parseFloat(e.target.value), end - step);
            onValueChange([newStart, end]);
          }}
          className="absolute inset-0 w-full opacity-0 cursor-pointer pointer-events-auto h-6 -top-2"
        />
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={end}
          disabled={disabled}
          onChange={(e) => {
            const newEnd = Math.max(parseFloat(e.target.value), start + step);
            onValueChange([start, newEnd]);
          }}
          className="absolute inset-0 w-full opacity-0 cursor-pointer pointer-events-auto h-6 -top-2"
        />

        {/* Start Thumb Visual */}
        <div
          className="pointer-events-none absolute size-4 rounded-full border-2 border-cyan-400 bg-slate-950 shadow-md transition-transform"
          style={{ left: `calc(${startPercent}% - 8px)` }}
        />
        {/* End Thumb Visual */}
        <div
          className="pointer-events-none absolute size-4 rounded-full border-2 border-cyan-400 bg-slate-950 shadow-md transition-transform"
          style={{ left: `calc(${endPercent}% - 8px)` }}
        />
      </div>
    );
  }

  // Single Slider
  const percent = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));

  return (
    <div className={cn('relative flex w-full touch-none select-none items-center py-2', className)}>
      <div className="relative h-2 w-full grow overflow-hidden rounded-full bg-slate-800">
        <div className="h-full bg-cyan-400" style={{ width: `${percent}%` }} />
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        disabled={disabled}
        onChange={(e) => onValueChange(parseFloat(e.target.value))}
        className="absolute inset-0 w-full opacity-0 cursor-pointer h-6 -top-2"
      />
      <div
        className="pointer-events-none absolute size-4 rounded-full border-2 border-cyan-400 bg-slate-950 shadow-md transition-transform"
        style={{ left: `calc(${percent}% - 8px)` }}
      />
    </div>
  );
};

import React from 'react';
import { cn } from '@/lib/utils';

export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: number;
  max?: number;
  indicatorClassName?: string;
}

export const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, max = 100, indicatorClassName, ...props }, ref) => {
    const percent = Math.min(100, Math.max(0, (value / max) * 100));

    return (
      <div
        ref={ref}
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={value}
        className={cn('relative h-2 w-full overflow-hidden rounded-full bg-slate-800', className)}
        {...props}
      >
        <div
          className={cn(
            'h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-300 ease-out',
            indicatorClassName
          )}
          style={{ width: `${percent}%` }}
        />
      </div>
    );
  }
);
Progress.displayName = 'Progress';

import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', isLoading = false, children, disabled, ...props }, ref) => {
    const variantStyles = {
      default: 'bg-cyan-500 text-slate-950 hover:bg-cyan-400 font-semibold shadow-md shadow-cyan-500/20 active:scale-[0.98]',
      destructive: 'bg-red-600 text-white hover:bg-red-500 shadow-md shadow-red-600/20 active:scale-[0.98]',
      outline: 'border border-slate-700 bg-transparent hover:bg-slate-800 text-slate-200 active:scale-[0.98]',
      secondary: 'bg-slate-800 text-slate-100 hover:bg-slate-700 active:scale-[0.98]',
      ghost: 'hover:bg-slate-800/80 text-slate-300 hover:text-slate-100',
      link: 'text-cyan-400 underline-offset-4 hover:underline p-0 h-auto',
    }[variant];

    const sizeStyles = {
      default: 'h-10 px-4 py-2 text-sm',
      sm: 'h-8 px-3 text-xs',
      lg: 'h-12 px-8 text-base',
      icon: 'size-9 p-0',
    }[size];

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 disabled:pointer-events-none disabled:opacity-50 select-none cursor-pointer',
          variantStyles,
          sizeStyles,
          className
        )}
        {...props}
      >
        {isLoading && <Loader2 className="size-4 animate-spin" />}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';

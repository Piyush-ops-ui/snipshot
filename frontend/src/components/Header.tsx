import React from 'react';
import { Cpu, ShieldCheck, Zap } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="w-full bg-white border-b border-slate-200 sticky top-0 z-40 px-6 py-3 shadow-xs">
      <div className="max-w-[1600px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
        {/* Left: Branding */}
        <div className="flex items-center gap-3">
          <div className="size-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-xs">
            <Zap className="size-4.5 fill-white text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-900 text-base tracking-tight">
                SnipShot
              </span>
              <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100">
                Studio
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Autonomous Video Engine • Screen-Grounded Pedagogical Compiler
            </p>
          </div>
        </div>

        {/* Right: Local Hardware & Privacy Badge */}
        <div className="flex items-center gap-2.5 text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 font-mono">
          <div className="flex items-center gap-1.5 font-medium text-slate-700">
            <span className="size-2 rounded-full bg-emerald-500 animate-pulse" />
            <Cpu className="size-3.5 text-slate-500" />
            <span>Intel Core Ultra 5 125H + Arc QSV</span>
          </div>
          <span className="text-slate-300">•</span>
          <span className="text-emerald-600 font-semibold">₹0.00 Cloud Cost</span>
          <span className="text-slate-300">•</span>
          <div className="flex items-center gap-1 text-slate-600">
            <ShieldCheck className="size-3.5 text-slate-500" />
            <span>100% On-Device Privacy</span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;

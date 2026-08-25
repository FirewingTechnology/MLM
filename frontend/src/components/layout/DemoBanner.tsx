import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

export const DemoBanner: React.FC = () => {
  return (
    <div className="bg-gradient-to-r from-amber-500/20 via-emerald-500/20 to-amber-500/20 border-b border-amber-500/30 px-4 py-2 text-xs md:text-sm font-semibold text-amber-200 flex items-center justify-between shadow-inner">
      <div className="flex items-center gap-2 mx-auto">
        <AlertTriangle className="w-4 h-4 text-amber-400 animate-pulse" />
        <span className="tracking-wider uppercase font-bold text-amber-300">DEMO MODE</span>
        <span className="hidden sm:inline text-amber-200/80">—</span>
        <span className="hidden sm:inline text-slate-200">All balances, purchases, commissions, and withdrawals are 100% VIRTUAL DEMO DATA.</span>
        <span className="text-amber-400 font-bold bg-amber-500/20 px-2 py-0.5 rounded text-[11px] border border-amber-500/40">NO REAL MONEY</span>
      </div>
      <div className="hidden lg:flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
        <ShieldCheck className="w-3.5 h-3.5" />
        <span>Virtual Sandbox Environment</span>
      </div>
    </div>
  );
};

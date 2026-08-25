import React from 'react';
import { Commission } from '../../types';
import { 
  X, 
  Coins, 
  HelpCircle, 
  CheckCircle2, 
  ArrowRight, 
  GitFork, 
  Award, 
  Calendar, 
  ShoppingBag 
} from 'lucide-react';

interface CommissionDetailModalProps {
  commission: Commission | null;
  onClose: () => void;
}

export const CommissionDetailModal: React.FC<CommissionDetailModalProps> = ({
  commission,
  onClose,
}) => {
  if (!commission) return null;

  const details = commission.calculation_details || {};
  const isMatching = commission.commission_type === 'BINARY_MATCHING';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="w-full max-w-lg rounded-2xl glass-panel border border-slate-700/80 shadow-2xl p-6 relative overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 text-brand-400 text-xs font-bold uppercase tracking-wider mb-2">
          <HelpCircle className="w-4 h-4" />
          <span>Commission Transparency Audit</span>
        </div>

        <h2 className="text-xl font-black text-white mb-1">
          Why Did I Receive This Commission?
        </h2>
        <div className="text-xs text-slate-400 font-mono mb-4">
          Ref: {commission.commission_code} • {new Date(commission.created_at).toLocaleString()}
        </div>

        {/* Primary Benefit Summary */}
        <div className="p-4 rounded-xl bg-gradient-to-r from-brand-950/80 to-navy-900 border border-brand-500/30 mb-5 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-300 font-semibold uppercase">
              {isMatching ? 'Binary Matching Bonus' : 'Direct Referral Bonus'}
            </div>
            <div className="text-2xl font-black text-brand-400 font-mono">
              +₹{commission.amount.toLocaleString()}
            </div>
          </div>
          <div className="text-right text-xs">
            <span className="bg-brand-500/20 text-brand-300 border border-brand-500/30 px-2.5 py-1 rounded-lg font-mono font-bold">
              {commission.percentage}% of BV
            </span>
          </div>
        </div>

        {/* Audit Trail Context */}
        <div className="space-y-3 mb-5 text-xs">
          <div className="p-3 rounded-xl bg-navy-900/80 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 flex items-center gap-1.5">
                <ShoppingBag className="w-3.5 h-3.5 text-blue-400" />
                Triggering Purchase:
              </span>
              <span className="font-mono text-slate-200 font-bold">{commission.purchase_code || details.purchase_code || 'N/A'}</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5 text-amber-400" />
                Purchased By Member:
              </span>
              <span className="text-white font-bold">
                {commission.source_user_name || details.purchaser_name || details.triggered_by_user || 'Direct Member'}
                {commission.source_user_code && <span className="text-slate-400 font-mono ml-1 font-normal">({commission.source_user_code})</span>}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-400">Business Volume Credited:</span>
              <span className="font-mono font-bold text-emerald-400">{commission.bv_amount.toLocaleString()} BV</span>
            </div>
          </div>

          {/* If Binary Matching, show left/right volume balance snapshot */}
          {isMatching && (
            <div className="p-3.5 rounded-xl bg-navy-950/90 border border-slate-800">
              <div className="text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <GitFork className="w-3.5 h-3.5 text-emerald-400" />
                <span>Volume Matching Calculation Snapshot</span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono mb-2">
                <div className="p-2 rounded bg-navy-900 border border-slate-800">
                  <div className="text-slate-400 text-[10px]">Left BV Prior</div>
                  <div className="font-bold text-slate-200">
                    ₹{details.left_volume_before?.toLocaleString() || commission.bv_amount.toLocaleString()}
                  </div>
                </div>
                <div className="p-2 rounded bg-navy-900 border border-slate-800">
                  <div className="text-slate-400 text-[10px]">Right BV Prior</div>
                  <div className="font-bold text-slate-200">
                    ₹{details.right_volume_before?.toLocaleString() || commission.bv_amount.toLocaleString()}
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-800">
                <span className="text-slate-400">Formula:</span>
                <span className="font-mono text-emerald-400 font-bold">
                  {commission.bv_amount.toLocaleString()} Matched BV × {commission.percentage}% = ₹{commission.amount.toLocaleString()}
                </span>
              </div>
            </div>
          )}
        </div>

        <button
          onClick={onClose}
          className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold transition-colors"
        >
          Close Audit View
        </button>
      </div>
    </div>
  );
};

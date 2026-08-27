import React from 'react';
import { PairSummary } from '../../types';
import { 
  Zap, 
  CheckCircle2, 
  Scale, 
  Sparkles, 
  Clock, 
  ShieldCheck,
  RotateCcw
} from 'lucide-react';

interface PairSummaryCardProps {
  pairSummary?: PairSummary;
}

export const PairSummaryCard: React.FC<PairSummaryCardProps> = ({ pairSummary }) => {
  if (!pairSummary) {
    return null;
  }

  const threshold = pairSummary.pair_volume_threshold || 30000;
  const bonusAmount = pairSummary.pair_bonus_amount || 15000;

  const leftProgress = Math.min(100, (pairSummary.effective_left_bv / threshold) * 100);
  const rightProgress = Math.min(100, (pairSummary.effective_right_bv / threshold) * 100);

  const isCompleted = pairSummary.pair_completed;
  const leftNeeded = pairSummary.needed_left_bv;
  const rightNeeded = pairSummary.needed_right_bv;

  return (
    <div className={`rounded-3xl bg-[#FFFEF9] p-4 sm:p-6 border transition-all duration-200 shadow-wealth-card ${
      isCompleted
        ? 'border-[#C9A227]/50 shadow-wealth-gold'
        : 'border-[#E5E0D3]'
    }`}>
      {/* Top Header Row */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
        <div className="flex items-center gap-2.5">
          <div className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm shadow-sm ${
            isCompleted 
              ? 'bg-[#063B32] text-[#E2C766] border border-[#C9A227]/40 shadow-wealth-gold' 
              : 'bg-[#FAF4DC] text-[#8C6C16] border border-[#E2C766]/50'
          }`}>
            <Scale className="w-4 h-4" />
          </div>
          <div>
            <div className="text-sm sm:text-base font-heading font-extrabold text-[#18211F] tracking-tight flex items-center gap-2">
              <span>Binary Performance & Pair Bonus</span>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-[#FAF4DC] text-[#8C6C16] font-bold border border-[#E2C766]/50">
                30k / 30k Match
              </span>
            </div>
            <div className="text-[11px] text-[#69736F] font-medium">
              ₹{bonusAmount.toLocaleString()} Bonus per qualifying pair (Max 1 pair / 12h slot)
            </div>
          </div>
        </div>

        {/* Status Badge */}
        {isCompleted ? (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF4DC] border border-[#E2C766] text-[#8C6C16] text-xs font-bold font-mono shimmer-gold">
            <Sparkles className="w-3.5 h-3.5 text-[#C9A227]" />
            <span>₹{bonusAmount.toLocaleString()} BONUS PAID</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#F7F4EC] border border-[#E5E0D3] text-[#69736F] text-xs font-semibold font-mono">
            <Clock className="w-3.5 h-3.5 text-[#063B32]" />
            <span>Slot: {pairSummary.slot_id}</span>
          </div>
        )}
      </div>

      {/* Two Columns: Left Leg vs Right Leg */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-4">
        {/* Left Leg BV Card */}
        <div className="p-4 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#063B32] flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#0E9F6E]" />
              <span>Left Leg Effective BV</span>
            </span>
            <span className="text-[10px] font-mono text-[#69736F] font-bold">
              Target: ₹{threshold.toLocaleString()}
            </span>
          </div>

          <div className="flex items-baseline justify-between">
            <div className="text-2xl font-heading font-black font-mono text-[#18211F]">
              ₹{pairSummary.effective_left_bv.toLocaleString()}
            </div>
            <div className="text-xs font-mono font-bold text-[#063B32]">
              {leftProgress.toFixed(0)}%
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full h-2 bg-[#EFECE2] rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-[#063B32] to-[#0E9F6E] rounded-full transition-all duration-700"
              style={{ width: `${leftProgress}%` }}
            />
          </div>

          {/* Volume Breakdown Subtext */}
          <div className="pt-2 border-t border-[#E5E0D3] flex justify-between items-center text-[10px] font-mono text-[#69736F]">
            <span className="flex items-center gap-1">
              <RotateCcw className="w-2.5 h-2.5 opacity-70" />
              <span>Carry: ₹{pairSummary.carry_forward_left.toLocaleString()}</span>
            </span>
            <span>+</span>
            <span>New: ₹{pairSummary.current_left_bv.toLocaleString()}</span>
          </div>
        </div>

        {/* Right Leg BV Card */}
        <div className="p-4 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8C6C16] flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#C9A227]" />
              <span>Right Leg Effective BV</span>
            </span>
            <span className="text-[10px] font-mono text-[#69736F] font-bold">
              Target: ₹{threshold.toLocaleString()}
            </span>
          </div>

          <div className="flex items-baseline justify-between">
            <div className="text-2xl font-heading font-black font-mono text-[#18211F]">
              ₹{pairSummary.effective_right_bv.toLocaleString()}
            </div>
            <div className="text-xs font-mono font-bold text-[#8C6C16]">
              {rightProgress.toFixed(0)}%
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full h-2 bg-[#EFECE2] rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-[#C9A227] to-[#E2C766] rounded-full transition-all duration-700"
              style={{ width: `${rightProgress}%` }}
            />
          </div>

          {/* Volume Breakdown Subtext */}
          <div className="pt-2 border-t border-[#E5E0D3] flex justify-between items-center text-[10px] font-mono text-[#69736F]">
            <span className="flex items-center gap-1">
              <RotateCcw className="w-2.5 h-2.5 opacity-70" />
              <span>Carry: ₹{pairSummary.carry_forward_right.toLocaleString()}</span>
            </span>
            <span>+</span>
            <span>New: ₹{pairSummary.current_right_bv.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Pair Status / Action Bar */}
      {isCompleted ? (
        <div className="p-3.5 rounded-2xl bg-[#FAF4DC] border border-[#E2C766] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2 text-[#8C6C16]">
            <Sparkles className="w-4 h-4 text-[#C9A227] shrink-0" />
            <span className="font-bold">
              Pair Completed! ₹{bonusAmount.toLocaleString()} credited to Virtual Wealth Wallet.
            </span>
          </div>
          <div className="text-[11px] font-mono text-[#18211F] bg-[#FFFEF9] px-2.5 py-1 rounded-lg border border-[#E5E0D3] font-medium">
            Carried: L: ₹{pairSummary.ending_carry_left.toLocaleString()} | R: ₹{pairSummary.ending_carry_right.toLocaleString()}
          </div>
        </div>
      ) : (
        <div className="p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2 text-[#18211F]">
            <Zap className="w-4 h-4 text-[#C9A227] shrink-0" />
            <span>
              {leftNeeded > 0 && rightNeeded > 0 ? (
                <>Need <strong className="text-[#063B32] font-mono">₹{leftNeeded.toLocaleString()} Left BV</strong> and <strong className="text-[#8C6C16] font-mono">₹{rightNeeded.toLocaleString()} Right BV</strong></>
              ) : leftNeeded > 0 ? (
                <>Need <strong className="text-[#063B32] font-mono">₹{leftNeeded.toLocaleString()} Left BV</strong> to trigger ₹{bonusAmount.toLocaleString()} pair payout</>
              ) : rightNeeded > 0 ? (
                <>Need <strong className="text-[#8C6C16] font-mono">₹{rightNeeded.toLocaleString()} Right BV</strong> to trigger ₹{bonusAmount.toLocaleString()} pair payout</>
              ) : (
                <span>Qualifying pair ready for settlement</span>
              )}
            </span>
          </div>
          <div className="text-[10px] font-mono text-[#69736F] flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-[#063B32]" />
            <span>Carry forward never expires</span>
          </div>
        </div>
      )}
    </div>
  );
};


import React from 'react';
import { Commission } from '../../types';
import {
  X,
  Coins,
  HelpCircle,
  CheckCircle2,
  Award,
  Calendar,
  ShoppingBag,
  RotateCcw,
  Sparkles,
  GitFork
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
  const isPair = commission.commission_type === 'PAIR_BONUS';
  const isDirect = commission.commission_type === 'DIRECT_REFERRAL' || commission.commission_type === 'DIRECT_COMMISSION';
  const isMatching = commission.commission_type === 'MATCHING_COMMISSION' || commission.commission_type === 'BINARY_MATCHING';
  const isCarry = commission.commission_type === 'CARRY_COMMISSION';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="w-full max-w-lg rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-elevated p-6 relative overflow-hidden text-[#18211F]"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-[#69736F] hover:text-[#18211F] hover:bg-[#EFECE2] transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 text-[#063B32] text-xs font-mono font-bold uppercase tracking-wider mb-1.5">
          <HelpCircle className="w-4 h-4 text-[#C9A227]" />
          <span>Income Transparency Audit</span>
        </div>

        <h2 className="text-xl font-heading font-extrabold text-[#18211F] mb-1 tracking-tight">
          Why Did I Receive This Income?
        </h2>
        <div className="text-xs text-[#69736F] font-mono mb-4 font-medium">
          Ref: {commission.commission_code} • {new Date(commission.created_at).toLocaleString()}
        </div>

        {/* Primary Benefit Summary */}
        <div className={`p-4 rounded-2xl border mb-5 flex items-center justify-between ${isPair
            ? 'bg-[#FAF4DC] border-[#E2C766]'
            : isMatching
              ? 'bg-[#FFEDD5] border-[#FDBA74]'
              : isCarry
                ? 'bg-[#DBEAFE] border-[#93C5FD]'
                : 'bg-[#E0F3EE] border-[#8DCFBF]'
          }`}>
          <div>
            <div className="text-xs text-[#69736F] font-bold uppercase">
              {isPair
                ? 'Matching Pair Bonus (30k/30k)'
                : isMatching
                  ? 'Matching Upline Income'
                  : isCarry
                    ? 'Carry-Forward Income'
                    : 'Direct Sponsor Bonus'}
            </div>
            <div className={`text-2xl sm:text-3xl font-heading font-black font-mono ${isPair
                ? 'text-[#8C6C16]'
                : isMatching
                  ? 'text-[#C2410C]'
                  : isCarry
                    ? 'text-[#1D4ED8]'
                    : 'text-[#063B32]'
              }`}>
              +₹{commission.amount.toLocaleString()}
            </div>
          </div>
          <div className="text-right text-xs">
            <span className={`border px-3 py-1 rounded-xl font-mono font-bold ${isPair
                ? 'bg-[#FFFEF9] text-[#8C6C16] border-[#E2C766]'
                : isMatching
                  ? 'bg-[#FFFEF9] text-[#C2410C] border-[#FDBA74]'
                  : isCarry
                    ? 'bg-[#FFFEF9] text-[#1D4ED8] border-[#93C5FD]'
                    : 'bg-[#FFFEF9] text-[#063B32] border-[#8DCFBF]'
              }`}>
              {isPair
                ? `₹${commission.amount.toLocaleString()} Payout`
                : isMatching
                  ? `${commission.percentage || 10}% of Child Pair`
                  : isCarry
                    ? 'Carry Payout'
                    : `${commission.percentage || 10}% of BV`}
            </span>
          </div>
        </div>

        {/* Audit Trail Context */}
        <div className="space-y-3 mb-5 text-xs">
          <div className="p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[#69736F] flex items-center gap-1.5 font-medium">
                <ShoppingBag className="w-3.5 h-3.5 text-[#063B32]" />
                Triggering Purchase:
              </span>
              <span className="font-mono text-[#18211F] font-bold">{commission.purchase_code || details.purchase_code || 'N/A'}</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[#69736F] flex items-center gap-1.5 font-medium">
                <Award className="w-3.5 h-3.5 text-[#C9A227]" />
                Purchased By Member:
              </span>
              <span className="text-[#18211F] font-bold">
                {commission.source_user_name || details.purchaser_name || details.triggered_by_user || 'Direct Member'}
                {commission.source_user_code && <span className="text-[#69736F] font-mono ml-1 font-normal">({commission.source_user_code})</span>}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[#69736F] font-medium">Business Volume Credited:</span>
              <span className="font-mono font-bold text-[#063B32]">{commission.bv_amount.toLocaleString()} BV</span>
            </div>
          </div>

          {/* Explanation banner if present */}
          {details.explanation && (
            <div className="p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] text-[11px] leading-relaxed">
              <span className="text-[#063B32] font-bold">Audit Explanation: </span>
              {details.explanation}
            </div>
          )}

          {/* If Pair Bonus, show left/right volume balance snapshot */}
          {isPair && (
            <div className="p-4 rounded-2xl bg-[#F7F4EC] border border-[#E2C766]">
              <div className="text-[11px] font-bold text-[#8C6C16] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[#C9A227]" />
                <span>30k / 30k Pair Settlement Breakdown</span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono mb-2">
                <div className="p-2.5 rounded-xl bg-[#FFFEF9] border border-[#E5E0D3]">
                  <div className="text-[#69736F] text-[10px]">Left Effective BV</div>
                  <div className="font-bold text-[#18211F]">
                    ₹{(details.effective_left_bv || 30000).toLocaleString()}
                  </div>
                  <div className="text-[10px] text-[#063B32] font-semibold flex items-center gap-0.5">
                    <RotateCcw className="w-2.5 h-2.5 opacity-70" />
                    <span>Carry: ₹{(details.ending_carry_left || 0).toLocaleString()}</span>
                  </div>
                </div>
                <div className="p-2.5 rounded-xl bg-[#FFFEF9] border border-[#E5E0D3]">
                  <div className="text-[#69736F] text-[10px]">Right Effective BV</div>
                  <div className="font-bold text-[#18211F]">
                    ₹{(details.effective_right_bv || 30000).toLocaleString()}
                  </div>
                  <div className="text-[10px] text-[#8C6C16] font-semibold flex items-center gap-0.5">
                    <RotateCcw className="w-2.5 h-2.5 opacity-70" />
                    <span>Carry: ₹{(details.ending_carry_right || 0).toLocaleString()}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] pt-1.5 border-t border-[#E5E0D3]">
                <span className="text-[#69736F]">Pair Rule:</span>
                <span className="font-mono text-[#8C6C16] font-bold">
                  30k Left & 30k Right Match = ₹{commission.amount.toLocaleString()} Pair Bonus
                </span>
              </div>
            </div>
          )}

          {/* If Matching Commission, show child pair bonus basis and 10% match snapshot */}
          {isMatching && (
            <div className="p-4 rounded-2xl bg-[#FFEDD5]/40 border border-[#FDBA74]">
              <div className="text-[11px] font-bold text-[#C2410C] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <GitFork className="w-3.5 h-3.5 text-[#EA580C]" />
                <span>Matching Commission on Child Pair Bonus</span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono mb-2">
                <div className="p-2.5 rounded-xl bg-[#FFFEF9] border border-[#E5E0D3]">
                  <div className="text-[#69736F] text-[10px]">Child Pair Bonus</div>
                  <div className="font-bold text-[#18211F]">
                    ₹{(details.pair_bonus_basis || 15000).toLocaleString()}
                  </div>
                  <div className="text-[10px] text-[#C2410C]">Completed 30k/30k</div>
                </div>
                <div className="p-2.5 rounded-xl bg-[#FFFEF9] border border-[#E5E0D3]">
                  <div className="text-[#69736F] text-[10px]">Matching Rate</div>
                  <div className="font-bold text-[#EA580C]">
                    {(details.matching_rate ? details.matching_rate * 100 : commission.percentage || 10)}%
                  </div>
                  <div className="text-[10px] text-[#69736F]">Configured in settings</div>
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] pt-1.5 border-t border-[#FDBA74]/50">
                <span className="text-[#69736F]">Matching Formula:</span>
                <span className="font-mono text-[#C2410C] font-bold">
                  ₹{(details.pair_bonus_basis || 15000).toLocaleString()} (Child Pair Bonus) × {(details.matching_rate ? details.matching_rate * 100 : commission.percentage || 10)}% = +₹{commission.amount.toLocaleString()}
                </span>
              </div>
            </div>
          )}
        </div>

        <button
          onClick={onClose}
          className="w-full py-3 rounded-2xl bg-[#EFECE2] hover:bg-[#E5E0D3] text-[#18211F] text-xs font-bold transition-colors cursor-pointer"
        >
          Close Audit View
        </button>
      </div>
    </div>
  );
};


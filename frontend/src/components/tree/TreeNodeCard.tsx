import React from 'react';
import { BinaryTreeNode } from '../../types';
import { User as UserIcon, Award, ArrowUpRight, Sparkles, RotateCcw, Zap, CheckCircle2 } from 'lucide-react';

interface TreeNodeCardProps {
  node: BinaryTreeNode | null;
  positionLabel?: 'LEFT' | 'RIGHT' | 'ROOT';
  onSelectNode: (node: BinaryTreeNode) => void;
  isSelected?: boolean;
  viewMode?: 'network' | 'active_slot' | 'history';
}

export const TreeNodeCard: React.FC<TreeNodeCardProps> = ({
  node,
  positionLabel,
  onSelectNode,
  isSelected,
  viewMode = 'network',
}) => {
  if (!node) {
    return (
      <div className="w-60 p-3.5 rounded-3xl border-2 border-dashed border-[#D3CCA9] bg-[#FFFEF9]/80 text-center flex flex-col items-center justify-center opacity-75 hover:opacity-100 hover:border-[#C9A227] transition-all shadow-2xs cursor-pointer group">
        <div className="w-8 h-8 rounded-xl bg-[#FAF4DC] border border-[#E2C766]/50 flex items-center justify-center text-[#8C6C16] mb-1.5 group-hover:scale-105 transition-transform">
          <UserIcon className="w-4 h-4" />
        </div>
        <div className="text-xs font-bold text-[#18211F]">
          Empty {positionLabel || 'Slot'}
        </div>
        <div className="text-[10px] text-[#69736F] font-medium">Available for Placement</div>
      </div>
    );
  }

  const isRoot = positionLabel === 'ROOT' || !node.binary_position;
  const isPairQualified = ((node.left_bv || 0) >= 30000 && (node.right_bv || 0) >= 30000) || node.pair_completed;
  const isActiveSlotMode = viewMode === 'active_slot';

  // Volume values to display based on viewMode
  const displayLeft = isActiveSlotMode ? (node.effective_left_bv ?? node.left_bv ?? 0) : (node.accumulated_left_bv ?? node.left_bv ?? 0);
  const displayRight = isActiveSlotMode ? (node.effective_right_bv ?? node.right_bv ?? 0) : (node.accumulated_right_bv ?? node.right_bv ?? 0);
  const carryLeft = node.ending_carry_left ?? node.carry_left_bv ?? 0;
  const carryRight = node.ending_carry_right ?? node.carry_right_bv ?? 0;

  return (
    <div
      onClick={() => onSelectNode(node)}
      className={`w-64 rounded-3xl p-4 cursor-pointer transition-all duration-200 text-left relative bg-[#FFFEF9] border ${
        isSelected
          ? 'border-[#C9A227] shadow-wealth-gold ring-4 ring-[#FAF4DC]'
          : node.has_active_slot_volume && isActiveSlotMode
          ? 'border-[#063B32] ring-2 ring-[#8DCFBF]/50 shadow-wealth-elevated'
          : isRoot
          ? 'border-[#C9A227]/60 shadow-wealth-elevated'
          : 'border-[#E5E0D3] shadow-wealth-card hover:border-[#C9A227]/60 hover:shadow-md'
      }`}
    >
      {/* Active slot indicator banner if in active slot mode */}
      {isActiveSlotMode && node.has_active_slot_volume && (
        <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 bg-[#063B32] text-[#FFFEF9] text-[9px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full shadow-2xs flex items-center gap-1 border border-[#8DCFBF]/40">
          <Zap className="w-2.5 h-2.5 text-[#E2C766]" />
          <span>Active Volume</span>
        </div>
      )}

      {/* Top Tag: Active status & Position */}
      <div className="flex items-center justify-between mb-2.5">
        <span
          className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${
            node.is_active
              ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
              : 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766]'
          }`}
        >
          {node.is_active ? '● Active' : '● Inactive'}
        </span>

        <span className="text-[10px] font-mono font-bold text-[#8C6C16] bg-[#FAF4DC] px-2 py-0.5 rounded-md border border-[#E2C766]/50">
          {node.binary_position || 'ROOT'}
        </span>
      </div>

      {/* User Info */}
      <div className="flex items-center gap-2.5 mb-3">
        <div
          className={`w-10 h-10 rounded-full flex items-center justify-center font-heading font-extrabold text-xs uppercase shrink-0 transition-transform ${
            isRoot
              ? 'bg-[#063B32] text-[#E2C766] gold-ring shadow-wealth-gold'
              : node.is_active
              ? 'bg-[#063B32] text-[#FFFEF9] border border-[#C9A227]/40 shadow-xs'
              : 'bg-[#69736F] text-[#FFFEF9]'
          }`}
        >
          {node.full_name?.substring(0, 2) || 'AM'}
        </div>
        <div className="min-w-0 flex-1">
          <div className="font-heading font-extrabold text-sm text-[#18211F] truncate">
            {node.full_name}
          </div>
          <div className="text-[11px] text-[#063B32] font-mono flex items-center gap-1 font-bold">
            <span>{node.user_code}</span>
          </div>
        </div>
      </div>

      {/* Volume Summary Pill (Left / Right BV) */}
      <div className="grid grid-cols-2 gap-2 p-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[11px] font-mono mb-2">
        <div className="text-left border-r border-[#E5E0D3] pr-1.5">
          <div className="text-[#69736F] text-[9px] font-sans uppercase font-bold">
            {isActiveSlotMode ? 'Left Effective' : 'Left Lifetime'}
          </div>
          <div className="font-bold text-[#063B32] truncate">
            {displayLeft ? `₹${(displayLeft / 1000).toFixed(0)}k` : '₹0'}
          </div>
          <div className="text-[9px] text-[#8C6C16] flex items-center gap-0.5">
            <RotateCcw className="w-2.5 h-2.5 opacity-70" />
            <span>Carry: ₹{carryLeft ? `${(carryLeft / 1000).toFixed(0)}k` : '0'}</span>
          </div>
        </div>
        <div className="text-right pl-1.5">
          <div className="text-[#69736F] text-[9px] font-sans uppercase font-bold">
            {isActiveSlotMode ? 'Right Effective' : 'Right Lifetime'}
          </div>
          <div className="font-bold text-[#063B32] truncate">
            {displayRight ? `₹${(displayRight / 1000).toFixed(0)}k` : '₹0'}
          </div>
          <div className="text-[9px] text-[#8C6C16] flex items-center justify-end gap-0.5">
            <RotateCcw className="w-2.5 h-2.5 opacity-70" />
            <span>Carry: ₹{carryRight ? `${(carryRight / 1000).toFixed(0)}k` : '0'}</span>
          </div>
        </div>
      </div>

      {/* Pair Status Pill */}
      {node.pair_completed ? (
        <div className="mb-2 p-1.5 rounded-xl bg-[#E0F3EE] border border-[#8DCFBF] text-center text-[10px] font-bold text-[#063B32] flex items-center justify-center gap-1">
          <CheckCircle2 className="w-3 h-3 text-[#063B32]" />
          <span>✓ Slot Pair Paid (₹15,000)</span>
        </div>
      ) : isPairQualified ? (
        <div className="mb-2 p-1.5 rounded-xl bg-[#FAF4DC] border border-[#E2C766] text-center text-[10px] font-bold text-[#8C6C16] flex items-center justify-center gap-1 shimmer-gold">
          <Sparkles className="w-3 h-3 text-[#C9A227]" />
          <span>₹15,000 Pair Qualified</span>
        </div>
      ) : null}

      {/* Footer Details */}
      <div className="flex items-center justify-between text-[10px] text-[#69736F] pt-1.5 border-t border-[#EFECE2]">
        <div className="flex items-center gap-1 font-medium">
          <Award className="w-3 h-3 text-[#C9A227]" />
          <span>Direct: {node.direct_referrals ?? node.direct_referrals_count ?? 0}</span>
        </div>
        <div className="flex items-center gap-0.5 text-[#063B32] hover:text-[#042C26] font-bold">
          <span>Details</span>
          <ArrowUpRight className="w-3 h-3" />
        </div>
      </div>
    </div>
  );
};

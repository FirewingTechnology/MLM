import React from 'react';
import { BinaryTreeNode } from '../../types';
import { User as UserIcon, Award, ArrowUpRight } from 'lucide-react';

interface TreeNodeCardProps {
  node: BinaryTreeNode | null;
  positionLabel?: 'LEFT' | 'RIGHT' | 'ROOT';
  onSelectNode: (node: BinaryTreeNode) => void;
  isSelected?: boolean;
}

export const TreeNodeCard: React.FC<TreeNodeCardProps> = ({
  node,
  positionLabel,
  onSelectNode,
  isSelected,
}) => {
  if (!node) {
    return (
      <div className="w-56 p-3 rounded-2xl border border-dashed border-slate-700/60 bg-navy-900/40 text-center flex flex-col items-center justify-center opacity-60 hover:opacity-100 transition-all">
        <div className="w-7 h-7 rounded-lg bg-slate-800 flex items-center justify-center text-slate-500 mb-1.5">
          <UserIcon className="w-4 h-4" />
        </div>
        <div className="text-[11px] font-semibold text-slate-400">
          Empty {positionLabel || 'Slot'}
        </div>
        <div className="text-[10px] text-slate-500">Available for Placement</div>
      </div>
    );
  }

  return (
    <div
      onClick={() => onSelectNode(node)}
      className={`w-64 rounded-2xl p-3.5 cursor-pointer transition-all duration-200 text-left relative ${
        isSelected
          ? 'bg-gradient-to-b from-brand-950/80 to-navy-900 border-2 border-brand-400 shadow-glow-emerald'
          : 'glass-panel hover:border-slate-600 hover:shadow-card'
      }`}
    >
      {/* Top Tag: Active status & Position */}
      <div className="flex items-center justify-between mb-2">
        <span
          className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
            node.is_active
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
          }`}
        >
          {node.is_active ? 'Active' : 'Inactive'}
        </span>

        <span className="text-[10px] font-mono font-bold text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded-md">
          {node.binary_position || 'ROOT'}
        </span>
      </div>

      {/* User Info */}
      <div className="flex items-center gap-2.5 mb-2.5">
        <div
          className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-xs uppercase text-white shrink-0 ${
            node.is_active
              ? 'bg-gradient-to-br from-brand-500 to-emerald-700'
              : 'bg-gradient-to-br from-slate-700 to-slate-800 text-slate-400'
          }`}
        >
          {node.full_name?.substring(0, 2) || 'US'}
        </div>
        <div className="min-w-0 flex-1">
          <div className="font-bold text-sm text-slate-100 truncate group-hover:text-brand-300">
            {node.full_name}
          </div>
          <div className="text-[11px] text-slate-400 font-mono flex items-center gap-1.5">
            <span>{node.user_code}</span>
          </div>
        </div>
      </div>

      {/* Volume Summary Pill (Left / Right BV) */}
      <div className="grid grid-cols-2 gap-1.5 p-2 rounded-xl bg-navy-950/70 border border-slate-800/80 text-[11px] font-mono mb-2">
        <div className="text-left border-r border-slate-800 pr-1">
          <div className="text-slate-400 text-[9px] font-sans uppercase font-bold">Left BV</div>
          <div className="font-bold text-emerald-400 truncate">
            {node.left_bv ? `₹${(node.left_bv / 1000).toFixed(0)}k` : '₹0'}
          </div>
          <div className="text-[9px] text-slate-400">Carry: {node.carry_left_bv ? `₹${(node.carry_left_bv / 1000).toFixed(0)}k` : '0'}</div>
        </div>
        <div className="text-right pl-1">
          <div className="text-slate-400 text-[9px] font-sans uppercase font-bold">Right BV</div>
          <div className="font-bold text-emerald-400 truncate">
            {node.right_bv ? `₹${(node.right_bv / 1000).toFixed(0)}k` : '₹0'}
          </div>
          <div className="text-[9px] text-slate-400">Carry: {node.carry_right_bv ? `₹${(node.carry_right_bv / 1000).toFixed(0)}k` : '0'}</div>
        </div>
      </div>

      {/* Footer Details */}
      <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
        <div className="flex items-center gap-1">
          <Award className="w-3 h-3 text-brand-400" />
          <span>Direct: {node.direct_referrals_count}</span>
        </div>
        <div className="flex items-center gap-0.5 text-brand-400 hover:text-brand-300 font-semibold">
          <span>Details</span>
          <ArrowUpRight className="w-3 h-3" />
        </div>
      </div>
    </div>
  );
};

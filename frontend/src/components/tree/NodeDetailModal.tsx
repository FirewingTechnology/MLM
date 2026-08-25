import React from 'react';
import { BinaryTreeNode } from '../../types';
import { 
  X, 
  User as UserIcon, 
  GitFork, 
  Award, 
  CheckCircle2, 
  Clock, 
  TrendingUp, 
  Package, 
  Link2 
} from 'lucide-react';

interface NodeDetailModalProps {
  node: BinaryTreeNode | null;
  onClose: () => void;
  onFocusNode?: (nodeId: number) => void;
}

export const NodeDetailModal: React.FC<NodeDetailModalProps> = ({ node, onClose, onFocusNode }) => {
  if (!node) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="w-full max-w-md rounded-2xl glass-panel border border-slate-700/80 shadow-2xl p-6 relative overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-5">
          <div
            className={`w-12 h-12 rounded-2xl flex items-center justify-center font-black text-base uppercase text-white shadow-md ${
              node.is_active
                ? 'bg-gradient-to-tr from-brand-600 to-emerald-400'
                : 'bg-gradient-to-tr from-slate-700 to-slate-800 text-slate-400'
            }`}
          >
            {node.full_name?.substring(0, 2) || 'US'}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-white">{node.full_name}</h3>
              <span
                className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                  node.is_active
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                }`}
              >
                {node.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div className="text-xs text-slate-400 font-mono">{node.user_code} • {node.email}</div>
          </div>
        </div>

        {/* MLM Placement & Sponsor Info */}
        <div className="grid grid-cols-2 gap-2 mb-4">
          <div className="p-3 rounded-xl bg-navy-900/80 border border-slate-800 text-xs">
            <div className="text-slate-400 text-[10px] uppercase font-bold flex items-center gap-1 mb-1">
              <Link2 className="w-3 h-3 text-brand-400" />
              <span>Direct Sponsor</span>
            </div>
            <div className="font-bold text-slate-100 truncate">{node.sponsor_name || 'None (Root)'}</div>
            <div className="text-[10px] text-slate-400 font-mono">{node.sponsor_code || '—'}</div>
          </div>

          <div className="p-3 rounded-xl bg-navy-900/80 border border-slate-800 text-xs">
            <div className="text-slate-400 text-[10px] uppercase font-bold flex items-center gap-1 mb-1">
              <GitFork className="w-3 h-3 text-blue-400" />
              <span>Placement Parent</span>
            </div>
            <div className="font-bold text-slate-100 truncate">{node.binary_parent_name || 'None (Root)'}</div>
            <div className="text-[10px] text-blue-400 font-mono font-bold">
              Position: {node.binary_position || 'ROOT'}
            </div>
          </div>
        </div>

        {/* Package & Personal BV */}
        <div className="p-3.5 rounded-xl bg-navy-900/80 border border-slate-800 mb-4 text-xs">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5 text-slate-400">
              <Package className="w-4 h-4 text-brand-400" />
              <span>Active Package:</span>
            </div>
            <span className="font-bold text-slate-100">
              {node.active_package_name || (node.is_active ? 'Premium Business Package' : 'No Active Package')}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-slate-400">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Personal Volume:</span>
            </div>
            <span className="font-mono font-bold text-brand-400">
              {node.personal_bv ? `${node.personal_bv.toLocaleString()} BV` : '0 BV'}
            </span>
          </div>
        </div>

        {/* Binary Volume Detailed Matrix */}
        <div className="p-4 rounded-xl bg-navy-950/90 border border-slate-800 mb-5">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center justify-between">
            <span>Binary Tree Volumes</span>
            <span className="text-brand-400 font-mono">Matched: ₹{node.matched_bv?.toLocaleString() || 0}</span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs font-mono">
            <div className="p-2.5 rounded-lg bg-navy-900 border border-slate-800">
              <div className="text-slate-400 text-[10px] font-sans font-bold uppercase mb-1">Left Leg</div>
              <div className="text-sm font-bold text-emerald-400">₹{node.left_bv?.toLocaleString() || 0} BV</div>
              <div className="text-[10px] text-slate-400 mt-1">Carry: ₹{node.carry_left_bv?.toLocaleString() || 0}</div>
            </div>

            <div className="p-2.5 rounded-lg bg-navy-900 border border-slate-800">
              <div className="text-slate-400 text-[10px] font-sans font-bold uppercase mb-1">Right Leg</div>
              <div className="text-sm font-bold text-emerald-400">₹{node.right_bv?.toLocaleString() || 0} BV</div>
              <div className="text-[10px] text-slate-400 mt-1">Carry: ₹{node.carry_right_bv?.toLocaleString() || 0}</div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {onFocusNode && (
            <button
              onClick={() => {
                onFocusNode(node.id);
                onClose();
              }}
              className="flex-1 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-400 text-navy-950 text-xs font-bold transition-colors"
            >
              Set as Tree Root
            </button>
          )}
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

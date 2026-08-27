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
  Link2,
  Sparkles,
  RotateCcw
} from 'lucide-react';

interface NodeDetailModalProps {
  node: BinaryTreeNode | null;
  onClose: () => void;
  onFocusNode?: (nodeId: number) => void;
}

export const NodeDetailModal: React.FC<NodeDetailModalProps> = ({ node, onClose, onFocusNode }) => {
  if (!node) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
      <div 
        className="w-full max-w-md rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-elevated p-6 relative overflow-hidden text-[#18211F]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-[#69736F] hover:text-[#18211F] hover:bg-[#EFECE2] transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3.5 mb-5">
          <div
            className={`w-12 h-12 rounded-2xl flex items-center justify-center font-heading font-extrabold text-base uppercase text-[#FFFEF9] shadow-sm ${
              node.is_active
                ? 'bg-[#063B32] border border-[#C9A227]/40 text-[#E2C766]'
                : 'bg-[#69736F]'
            }`}
          >
            {node.full_name?.substring(0, 2) || 'US'}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-heading font-extrabold text-[#18211F] tracking-tight">{node.full_name}</h3>
              <span
                className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${
                  node.is_active
                    ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
                    : 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766]'
                }`}
              >
                {node.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div className="text-xs text-[#69736F] font-mono font-medium">{node.user_code} • {node.email}</div>
          </div>
        </div>

        {/* MLM Placement & Sponsor Info */}
        <div className="grid grid-cols-2 gap-2.5 mb-4">
          <div className="p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-xs">
            <div className="text-[#69736F] text-[10px] uppercase font-bold flex items-center gap-1 mb-1">
              <Link2 className="w-3.5 h-3.5 text-[#C9A227]" />
              <span>Direct Sponsor</span>
            </div>
            <div className="font-bold text-[#18211F] truncate">{node.sponsor_name || 'None (Root)'}</div>
            <div className="text-[10px] text-[#69736F] font-mono">{node.sponsor_code || '—'}</div>
          </div>

          <div className="p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-xs">
            <div className="text-[#69736F] text-[10px] uppercase font-bold flex items-center gap-1 mb-1">
              <GitFork className="w-3.5 h-3.5 text-[#063B32]" />
              <span>Placement Parent</span>
            </div>
            <div className="font-bold text-[#18211F] truncate">{node.binary_parent_name || 'None (Root)'}</div>
            <div className="text-[10px] text-[#8C6C16] font-mono font-bold">
              Position: {node.binary_position || 'ROOT'}
            </div>
          </div>
        </div>

        {/* Package & Personal BV */}
        <div className="p-4 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] mb-4 text-xs">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5 text-[#69736F] font-medium">
              <Package className="w-4 h-4 text-[#063B32]" />
              <span>Active Package:</span>
            </div>
            <span className="font-bold text-[#18211F]">
              {node.active_package_name || (node.is_active ? 'Premium Business Package' : 'No Active Package')}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-[#69736F] font-medium">
              <TrendingUp className="w-4 h-4 text-[#C9A227]" />
              <span>Personal Volume:</span>
            </div>
            <span className="font-mono font-bold text-[#063B32]">
              {node.personal_bv ? `${node.personal_bv.toLocaleString()} BV` : '0 BV'}
            </span>
          </div>
        </div>

        {/* Binary Volume Detailed Matrix */}
        <div className="p-4 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] mb-5">
          <div className="text-[11px] font-bold uppercase tracking-wider text-[#69736F] mb-3 flex items-center justify-between">
            <span>Binary Tree Volumes</span>
            <span className="text-[#8C6C16] font-mono font-bold">Matched: ₹{node.matched_bv?.toLocaleString() || 0}</span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs font-mono">
            <div className="p-3 rounded-xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-2xs">
              <div className="text-[#69736F] text-[10px] font-sans font-bold uppercase mb-1">Left Leg</div>
              <div className="text-sm font-bold text-[#063B32]">₹{node.left_bv?.toLocaleString() || 0} BV</div>
              <div className="text-[10px] text-[#8C6C16] mt-1 flex items-center gap-0.5">
                <RotateCcw className="w-2.5 h-2.5 opacity-70" />
                <span>Carry: ₹{node.carry_left_bv?.toLocaleString() || 0}</span>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-2xs">
              <div className="text-[#69736F] text-[10px] font-sans font-bold uppercase mb-1">Right Leg</div>
              <div className="text-sm font-bold text-[#063B32]">₹{node.right_bv?.toLocaleString() || 0} BV</div>
              <div className="text-[10px] text-[#8C6C16] mt-1 flex items-center gap-0.5">
                <RotateCcw className="w-2.5 h-2.5 opacity-70" />
                <span>Carry: ₹{node.carry_right_bv?.toLocaleString() || 0}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Child Subtree Jump Buttons */}
        {(node.left || node.right) && onFocusNode && (
          <div className="grid grid-cols-2 gap-2 mb-4">
            {node.left ? (
              <button
                onClick={() => {
                  onFocusNode(node.left!.id);
                  onClose();
                }}
                className="p-3 rounded-2xl bg-[#E0F3EE] border border-[#8DCFBF] hover:bg-[#C1E7DC] text-[#063B32] text-xs font-bold text-left transition-colors flex items-center justify-between shadow-2xs cursor-pointer"
              >
                <div className="truncate">
                  <div className="text-[10px] text-[#063B32] font-semibold">← Left Leg</div>
                  <div className="truncate font-bold">{node.left.full_name}</div>
                </div>
                <span className="text-[11px] font-mono">View →</span>
              </button>
            ) : (
              <div className="p-3 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[11px] text-[#69736F] text-center flex items-center justify-center">
                Left Leg Empty
              </div>
            )}

            {node.right ? (
              <button
                onClick={() => {
                  onFocusNode(node.right!.id);
                  onClose();
                }}
                className="p-3 rounded-2xl bg-[#FAF4DC] border border-[#E2C766] hover:bg-[#F4E7B4] text-[#8C6C16] text-xs font-bold text-left transition-colors flex items-center justify-between shadow-2xs cursor-pointer"
              >
                <div className="truncate">
                  <div className="text-[10px] text-[#8C6C16] font-semibold">Right Leg →</div>
                  <div className="truncate font-bold">{node.right.full_name}</div>
                </div>
                <span className="text-[11px] font-mono">View →</span>
              </button>
            ) : (
              <div className="p-3 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[11px] text-[#69736F] text-center flex items-center justify-center">
                Right Leg Empty
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2">
          {onFocusNode && (
            <button
              onClick={() => {
                onFocusNode(node.id);
                onClose();
              }}
              className="flex-1 py-3 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/30 text-xs font-bold transition-colors shadow-wealth-card cursor-pointer"
            >
              Set as Tree Root
            </button>
          )}
          <button
            onClick={onClose}
            className="flex-1 py-3 rounded-2xl bg-[#EFECE2] hover:bg-[#E5E0D3] text-[#18211F] text-xs font-bold transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};


import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useToast } from '../../context/ToastContext';
import { X, ShieldAlert, Loader2, DollarSign } from 'lucide-react';
import { User } from '../../types';

interface AdminAdjustmentModalProps {
  user: User | null;
  onClose: () => void;
}

export const AdminAdjustmentModal: React.FC<AdminAdjustmentModalProps> = ({ user, onClose }) => {
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const [type, setType] = useState<'CREDIT' | 'DEBIT'>('CREDIT');
  const [amount, setAmount] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);

  if (!user) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const num = parseFloat(amount);
    if (isNaN(num) || num <= 0) {
      showToast('Please enter a valid positive amount.', 'error');
      return;
    }
    if (!reason.trim()) {
      showToast('An audit reason is required for manual balance adjustments.', 'error');
      return;
    }

    const finalAmount = type === 'CREDIT' ? num : -num;

    setLoading(true);
    try {
      const res = await api.post(`/admin/users/${user.id}/adjust-wallet`, {
        amount: finalAmount,
        reason: reason.trim(),
      });

      if (res.data?.success) {
        showToast(`Wallet adjusted by ₹${finalAmount > 0 ? '+' : ''}${finalAmount.toLocaleString()} successfully.`, 'success');
        queryClient.invalidateQueries({ queryKey: ['adminUsers'] });
        queryClient.invalidateQueries({ queryKey: ['adminDashboard'] });
        onClose();
      }
    } catch (err: any) {
      showToast(err.response?.data?.error?.message || 'Adjustment failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
      <div 
        className="w-full max-w-md rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-elevated p-6 relative overflow-hidden text-[#18211F]"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-[#69736F] hover:text-[#18211F] hover:bg-[#EFECE2] transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 text-[#8C6C16] text-xs font-mono font-bold uppercase tracking-wider mb-1.5">
          <ShieldAlert className="w-4 h-4 text-[#C9A227]" />
          <span>Admin Financial Tool</span>
        </div>

        <h2 className="text-xl font-heading font-extrabold text-[#18211F] mb-1 tracking-tight">
          Adjust Virtual Wallet
        </h2>
        <p className="text-xs text-[#69736F] mb-4">
          Target User: <span className="text-[#063B32] font-bold">{user.full_name}</span> ({user.user_code})
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Current balance */}
          <div className="flex justify-between p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-xs font-mono">
            <span className="text-[#69736F] font-sans font-medium">Current Balance:</span>
            <span className="text-[#063B32] font-bold">₹{user.wallet_balance?.toLocaleString() || 0}</span>
          </div>

          {/* Type: Credit or Debit */}
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setType('CREDIT')}
              className={`py-2.5 rounded-2xl text-xs font-heading font-bold transition-all border cursor-pointer ${
                type === 'CREDIT'
                  ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF] shadow-xs'
                  : 'bg-[#F7F4EC] border-[#E5E0D3] text-[#69736F] hover:bg-[#EFECE2]'
              }`}
            >
              + Credit Balance
            </button>
            <button
              type="button"
              onClick={() => setType('DEBIT')}
              className={`py-2.5 rounded-2xl text-xs font-heading font-bold transition-all border cursor-pointer ${
                type === 'DEBIT'
                  ? 'bg-rose-50 text-rose-700 border-rose-200 shadow-xs'
                  : 'bg-[#F7F4EC] border-[#E5E0D3] text-[#69736F] hover:bg-[#EFECE2]'
              }`}
            >
              - Debit Balance
            </button>
          </div>

          {/* Amount */}
          <div>
            <label className="block text-xs font-bold text-[#18211F] mb-1">
              Adjustment Amount (₹)
            </label>
            <input
              type="number"
              min="1"
              step="1"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="e.g. 500"
              className="w-full px-3.5 py-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] font-mono text-sm focus:outline-none focus:border-[#063B32] shadow-xs"
              required
            />
          </div>

          {/* Mandatory reason */}
          <div>
            <label className="block text-xs font-bold text-[#18211F] mb-1">
              Audit Reason (Mandatory)
            </label>
            <textarea
              rows={2}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain why this manual adjustment is being made..."
              className="w-full px-3.5 py-2 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] text-xs focus:outline-none focus:border-[#063B32] shadow-xs"
              required
            />
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 rounded-2xl border border-[#E5E0D3] hover:bg-[#EFECE2] text-[#18211F] text-xs font-semibold cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-1.5 py-3 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/30 text-xs font-heading font-bold shadow-wealth-card transition-colors disabled:opacity-50 cursor-pointer"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin text-[#C9A227]" /> : <span>Confirm Adjustment</span>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};


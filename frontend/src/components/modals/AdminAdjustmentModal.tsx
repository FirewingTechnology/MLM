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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="w-full max-w-md rounded-2xl glass-panel border border-slate-700/80 shadow-2xl p-6 relative overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 text-amber-400 text-xs font-bold uppercase tracking-wider mb-2">
          <ShieldAlert className="w-4 h-4" />
          <span>Admin Financial Tool</span>
        </div>

        <h2 className="text-xl font-bold text-white mb-1">
          Adjust Virtual Wallet
        </h2>
        <p className="text-xs text-slate-400 mb-4">
          Target User: <span className="text-white font-semibold">{user.full_name}</span> ({user.user_code})
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Current balance */}
          <div className="flex justify-between p-3 rounded-xl bg-navy-900 border border-slate-800 text-xs font-mono">
            <span className="text-slate-400">Current Balance:</span>
            <span className="text-emerald-400 font-bold">₹{user.wallet_balance?.toLocaleString() || 0}</span>
          </div>

          {/* Type: Credit or Debit */}
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setType('CREDIT')}
              className={`py-2 rounded-xl text-xs font-bold transition-all border ${
                type === 'CREDIT'
                  ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                  : 'bg-navy-900 border-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              + Credit Balance
            </button>
            <button
              type="button"
              onClick={() => setType('DEBIT')}
              className={`py-2 rounded-xl text-xs font-bold transition-all border ${
                type === 'DEBIT'
                  ? 'bg-rose-500/20 text-rose-400 border-rose-500/40'
                  : 'bg-navy-900 border-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              - Debit Balance
            </button>
          </div>

          {/* Amount */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Adjustment Amount (₹)
            </label>
            <input
              type="number"
              min="1"
              step="1"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="e.g. 500"
              className="w-full px-3.5 py-2.5 rounded-xl bg-navy-950/80 border border-slate-700 text-white font-mono text-sm focus:outline-none focus:border-amber-500"
              required
            />
          </div>

          {/* Mandatory reason */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Audit Reason (Mandatory)
            </label>
            <textarea
              rows={2}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain why this manual adjustment is being made..."
              className="w-full px-3.5 py-2 rounded-xl bg-navy-950/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-amber-500"
              required
            />
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-300 text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-navy-950 text-xs font-bold shadow-glow-amber transition-colors disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Confirm Adjustment</span>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

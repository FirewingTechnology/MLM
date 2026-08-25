import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useToast } from '../../context/ToastContext';
import { useAuth } from '../../context/AuthContext';
import { 
  X, 
  Wallet, 
  ArrowUpRight, 
  ShieldAlert, 
  Building, 
  Smartphone, 
  Loader2, 
  CheckCircle2 
} from 'lucide-react';

interface WithdrawalModalProps {
  isOpen: boolean;
  onClose: () => void;
  availableBalance: number;
}

export const WithdrawalModal: React.FC<WithdrawalModalProps> = ({
  isOpen,
  onClose,
  availableBalance,
}) => {
  const { showToast } = useToast();
  const { refreshUser } = useAuth();
  const queryClient = useQueryClient();

  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState<'VIRTUAL_UPI' | 'VIRTUAL_BANK'>('VIRTUAL_UPI');
  const [upiId, setUpiId] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [ifsc, setIfsc] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState<any>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const numAmount = parseFloat(amount);

    if (isNaN(numAmount) || numAmount <= 0) {
      showToast('Please enter a valid withdrawal amount.', 'error');
      return;
    }

    if (numAmount > availableBalance) {
      showToast(`Cannot request ₹${numAmount.toLocaleString()}. Available balance is ₹${availableBalance.toLocaleString()}.`, 'error');
      return;
    }

    setLoading(true);
    try {
      const payoutDetails = method === 'VIRTUAL_UPI' 
        ? { upi_id: upiId || 'demo@okhdfcbank' }
        : { account_number: accountNumber || '987654321098', ifsc: ifsc || 'HDFC0001234' };

      const res = await api.post('/withdrawals', {
        amount: numAmount,
        payout_method: method,
        payout_details: payoutDetails,
      });

      if (res.data?.success) {
        setSubmitted(res.data.data);
        showToast('Virtual withdrawal request submitted. Awaiting demo admin approval.', 'success');
        queryClient.invalidateQueries({ queryKey: ['wallet'] });
        queryClient.invalidateQueries({ queryKey: ['withdrawals'] });
        queryClient.invalidateQueries({ queryKey: ['transactions'] });
        queryClient.invalidateQueries({ queryKey: ['dashboard'] });
        await refreshUser();
      }
    } catch (err: any) {
      showToast(err.response?.data?.error?.message || 'Failed to submit withdrawal request.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setSubmitted(null);
    setAmount('');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="w-full max-w-md rounded-2xl glass-panel border border-slate-700/80 shadow-2xl p-6 relative overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {!submitted ? (
          <form onSubmit={handleSubmit}>
            <div className="flex items-center gap-2 text-brand-400 text-xs font-bold uppercase tracking-wider mb-2">
              <Wallet className="w-4 h-4" />
              <span>Virtual Payout Request</span>
            </div>

            <h2 className="text-2xl font-extrabold text-white mb-2">
              Request Demo Withdrawal
            </h2>
            <p className="text-slate-400 text-xs mb-4">
              Submit a simulated payout request. Balance is held pending Admin approval in the demo portal.
            </p>

            {/* Current Balance Tag */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-navy-900/80 border border-slate-800 mb-4 text-xs font-mono">
              <span className="text-slate-400">Available Balance:</span>
              <span className="text-base font-bold text-emerald-400">₹{availableBalance.toLocaleString()}</span>
            </div>

            {/* Amount input */}
            <div className="mb-4">
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Withdrawal Amount (₹)
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 font-bold">₹</span>
                <input
                  type="number"
                  step="100"
                  min="100"
                  max={availableBalance}
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="e.g. 3000"
                  className="w-full pl-8 pr-4 py-2.5 rounded-xl bg-navy-950/80 border border-slate-700/80 text-white font-mono text-sm focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all"
                  required
                />
              </div>
              <div className="flex gap-2 mt-2">
                {[1000, 3000, 5000].map((quick) => (
                  quick <= availableBalance && (
                    <button
                      key={quick}
                      type="button"
                      onClick={() => setAmount(String(quick))}
                      className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-[11px] font-mono text-slate-300 transition-colors"
                    >
                      ₹{quick.toLocaleString()}
                    </button>
                  )
                ))}
                {availableBalance > 0 && (
                  <button
                    type="button"
                    onClick={() => setAmount(String(availableBalance))}
                    className="px-2.5 py-1 rounded-lg bg-brand-500/10 hover:bg-brand-500/20 text-brand-400 text-[11px] font-mono font-bold transition-colors"
                  >
                    Max (₹{availableBalance.toLocaleString()})
                  </button>
                )}
              </div>
            </div>

            {/* Payout method */}
            <div className="mb-4">
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Simulated Payout Destination
              </label>
              <div className="grid grid-cols-2 gap-2 mb-3">
                <button
                  type="button"
                  onClick={() => setMethod('VIRTUAL_UPI')}
                  className={`p-2.5 rounded-xl border flex items-center justify-center gap-2 text-xs font-bold transition-all ${
                    method === 'VIRTUAL_UPI'
                      ? 'bg-brand-500/10 border-brand-500/40 text-brand-400'
                      : 'bg-navy-900/60 border-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  <Smartphone className="w-4 h-4" />
                  <span>Virtual UPI</span>
                </button>
                <button
                  type="button"
                  onClick={() => setMethod('VIRTUAL_BANK')}
                  className={`p-2.5 rounded-xl border flex items-center justify-center gap-2 text-xs font-bold transition-all ${
                    method === 'VIRTUAL_BANK'
                      ? 'bg-brand-500/10 border-brand-500/40 text-brand-400'
                      : 'bg-navy-900/60 border-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  <Building className="w-4 h-4" />
                  <span>Virtual Bank</span>
                </button>
              </div>

              {method === 'VIRTUAL_UPI' ? (
                <input
                  type="text"
                  value={upiId}
                  onChange={(e) => setUpiId(e.target.value)}
                  placeholder="demo-id@okhdfcbank"
                  className="w-full px-3.5 py-2 rounded-xl bg-navy-950/80 border border-slate-700/80 text-white font-mono text-xs focus:outline-none focus:border-brand-500"
                />
              ) : (
                <div className="space-y-2">
                  <input
                    type="text"
                    value={accountNumber}
                    onChange={(e) => setAccountNumber(e.target.value)}
                    placeholder="Account: 987654321098"
                    className="w-full px-3.5 py-2 rounded-xl bg-navy-950/80 border border-slate-700/80 text-white font-mono text-xs focus:outline-none focus:border-brand-500"
                  />
                  <input
                    type="text"
                    value={ifsc}
                    onChange={(e) => setIfsc(e.target.value)}
                    placeholder="IFSC: HDFC0001234"
                    className="w-full px-3.5 py-2 rounded-xl bg-navy-950/80 border border-slate-700/80 text-white font-mono text-xs focus:outline-none focus:border-brand-500"
                  />
                </div>
              )}
            </div>

            {/* Demo Notice */}
            <div className="flex items-start gap-2 p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-[11px] mb-5">
              <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <span>Simulated withdrawal. No funds will be transferred to real bank accounts.</span>
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleClose}
                className="flex-1 px-4 py-2.5 rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-300 text-xs font-semibold transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || availableBalance <= 0}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-400 hover:to-emerald-500 text-navy-950 text-xs font-bold shadow-glow-emerald transition-all disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Submitting...</span>
                  </>
                ) : (
                  <>
                    <ArrowUpRight className="w-4 h-4" />
                    <span>Request Payout</span>
                  </>
                )}
              </button>
            </div>
          </form>
        ) : (
          <div className="text-center py-4">
            <div className="w-14 h-14 rounded-2xl bg-amber-500/20 border border-amber-500/40 text-amber-400 flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="w-8 h-8" />
            </div>

            <h3 className="text-xl font-bold text-white mb-1">Withdrawal Requested</h3>
            <p className="text-amber-300 font-semibold text-xs mb-4">
              Status: PENDING ADMIN APPROVAL
            </p>

            <div className="p-3.5 rounded-xl bg-navy-900/80 border border-slate-800 mb-5 text-left space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Request Code:</span>
                <span className="font-mono text-slate-200 font-bold">{submitted.withdrawal_code}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Amount:</span>
                <span className="font-mono text-amber-400 font-bold">₹{submitted.amount?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Method:</span>
                <span className="text-slate-300 font-semibold">{submitted.payout_method}</span>
              </div>
            </div>

            <p className="text-[11px] text-slate-400 mb-4">
              To test the approval flow, login as Admin (<code className="text-amber-300">admin@demo.com</code>) and approve this payout in the Admin Suite.
            </p>

            <button
              onClick={handleClose}
              className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold transition-colors"
            >
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

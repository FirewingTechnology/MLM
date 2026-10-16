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
  CheckCircle2,
  Sparkles 
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
  const { refreshUser, user } = useAuth();
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
    if (!user?.is_active) {
      showToast('Your account must be paid and active to request payouts.', 'error');
      return;
    }
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
        ? { upi_id: upiId }
        : { account_number: accountNumber, ifsc: ifsc };

      const res = await api.post('/withdrawals', {
        amount: numAmount,
        payout_method: method,
        payout_details: payoutDetails,
      });

      if (res.data?.success) {
        setSubmitted(res.data.data);
        showToast('Withdrawal request submitted successfully.', 'success');
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

  const numAmount = parseFloat(amount) || 0;
  const feePercentage = 15;
  const feeAmount = numAmount > 0 ? Math.round(numAmount * 0.15 * 100) / 100 : 0;
  const netAmount = numAmount > 0 ? Math.max(0, Math.round((numAmount - feeAmount) * 100) / 100) : 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
      <div 
        className="w-full max-w-md rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-elevated p-6 relative overflow-hidden text-[#18211F]"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-[#69736F] hover:text-[#18211F] hover:bg-[#EFECE2] transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {!submitted ? (
          <form onSubmit={handleSubmit}>
            <div className="flex items-center gap-2 text-[#063B32] text-xs font-mono font-bold uppercase tracking-wider mb-1.5">
              <Wallet className="w-4 h-4 text-[#C9A227]" />
              <span>Payout Request</span>
            </div>

            <h2 className="text-2xl font-heading font-extrabold text-[#18211F] mb-1 tracking-tight">
              Request Withdrawal
            </h2>
            <p className="text-[#69736F] text-xs mb-4">
              Submit a payout request. Balance is held pending Admin approval in the portal.
            </p>

            {/* Account Inactive Banner */}
            {!user?.is_active && (
              <div className="mb-4 p-3 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-2.5">
                <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">Account Inactive:</span> Your account must be paid and active to request payouts. Please activate your account first.
                </div>
              </div>
            )}

            {/* Current Balance Tag */}
            <div className="flex items-center justify-between p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] mb-4 text-xs font-mono">
              <span className="text-[#69736F] font-sans font-medium">Available Balance:</span>
              <span className="text-base font-bold text-[#063B32]">₹{availableBalance.toLocaleString()}</span>
            </div>

            {/* Amount input */}
            <div className="mb-4">
              <label className="block text-xs font-semibold text-[#18211F] mb-1.5">
                Withdrawal Amount (₹)
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#69736F] font-bold">₹</span>
                <input
                  type="number"
                  step="100"
                  min="100"
                  max={availableBalance}
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="e.g. 10000"
                  className="w-full pl-8 pr-4 py-3 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] font-mono text-sm focus:outline-none focus:border-[#063B32] focus:ring-2 focus:ring-[#063B32]/10 transition-all shadow-xs"
                  required
                />
              </div>
              <div className="flex gap-2 mt-2">
                {[1000, 5000, 10000].map((quick) => (
                  quick <= availableBalance && (
                    <button
                      key={quick}
                      type="button"
                      onClick={() => setAmount(String(quick))}
                      className="px-3 py-1 rounded-xl bg-[#F7F4EC] hover:bg-[#EFECE2] text-[11px] font-mono text-[#18211F] font-semibold transition-colors border border-[#E5E0D3] cursor-pointer"
                    >
                      ₹{quick.toLocaleString()}
                    </button>
                  )
                ))}
                {availableBalance > 0 && (
                  <button
                    type="button"
                    onClick={() => setAmount(String(availableBalance))}
                    className="px-3 py-1 rounded-xl bg-[#FAF4DC] hover:bg-[#F4E7B4] text-[#8C6C16] text-[11px] font-mono font-bold transition-colors border border-[#E2C766]/60 cursor-pointer"
                  >
                    Max (₹{availableBalance.toLocaleString()})
                  </button>
                )}
              </div>
            </div>

            {/* 15% Processing Fee Live Deduction Breakdown */}
            {numAmount > 0 && (
              <div className="mb-4 p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] space-y-2 text-xs">
                <div className="flex items-center justify-between text-[#69736F]">
                  <span className="font-medium">Requested Gross Amount:</span>
                  <span className="font-mono font-bold text-[#18211F]">
                    ₹{numAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="flex items-center justify-between text-amber-800">
                  <span className="flex items-center gap-1.5 font-medium">
                    <span>Processing Fee</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-amber-100 border border-amber-300 font-bold font-mono text-amber-900">
                      15%
                    </span>
                  </span>
                  <span className="font-mono font-bold">
                    - ₹{feeAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="h-px bg-[#E5E0D3] my-1" />
                <div className="flex items-center justify-between">
                  <span className="font-heading font-extrabold text-[#063B32]">Final Payout (You Receive):</span>
                  <span className="font-mono font-black text-sm text-[#063B32]">
                    ₹{netAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
              </div>
            )}

            {/* Payout method */}
            <div className="mb-4">
              <label className="block text-xs font-semibold text-[#18211F] mb-1.5">
                Payout Destination
              </label>
              <div className="grid grid-cols-2 gap-2 mb-3">
                <button
                  type="button"
                  onClick={() => setMethod('VIRTUAL_UPI')}
                  className={`p-3 rounded-2xl border flex items-center justify-center gap-2 text-xs font-bold transition-all cursor-pointer ${
                    method === 'VIRTUAL_UPI'
                      ? 'bg-[#E0F3EE] border-[#8DCFBF] text-[#063B32] shadow-xs'
                      : 'bg-[#F7F4EC] border-[#E5E0D3] text-[#69736F] hover:bg-[#EFECE2]'
                  }`}
                >
                  <Smartphone className="w-4 h-4 text-[#063B32]" />
                  <span>UPI Transfer</span>
                </button>
                <button
                  type="button"
                  onClick={() => setMethod('VIRTUAL_BANK')}
                  className={`p-3 rounded-2xl border flex items-center justify-center gap-2 text-xs font-bold transition-all cursor-pointer ${
                    method === 'VIRTUAL_BANK'
                      ? 'bg-[#E0F3EE] border-[#8DCFBF] text-[#063B32] shadow-xs'
                      : 'bg-[#F7F4EC] border-[#E5E0D3] text-[#69736F] hover:bg-[#EFECE2]'
                  }`}
                >
                  <Building className="w-4 h-4 text-[#063B32]" />
                  <span>Bank Account</span>
                </button>
              </div>

              {method === 'VIRTUAL_UPI' ? (
                <input
                  type="text"
                  value={upiId}
                  onChange={(e) => setUpiId(e.target.value)}
                  placeholder="user@okhdfcbank"
                  className="w-full px-3.5 py-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] font-mono text-xs focus:outline-none focus:border-[#063B32] shadow-xs"
                />
              ) : (
                <div className="space-y-2">
                  <input
                    type="text"
                    value={accountNumber}
                    onChange={(e) => setAccountNumber(e.target.value)}
                    placeholder="Account Number"
                    className="w-full px-3.5 py-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] font-mono text-xs focus:outline-none focus:border-[#063B32] shadow-xs"
                  />
                  <input
                    type="text"
                    value={ifsc}
                    onChange={(e) => setIfsc(e.target.value)}
                    placeholder="IFSC Code (e.g. HDFC0001234)"
                    className="w-full px-3.5 py-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] font-mono text-xs focus:outline-none focus:border-[#063B32] shadow-xs"
                  />
                </div>
              )}
            </div>

            {/* Payout Processing Notice */}
            <div className="flex items-start gap-2 p-3 rounded-2xl bg-[#FAF4DC] border border-[#E2C766] text-[#8C6C16] text-[11px] mb-5">
              <ShieldAlert className="w-4 h-4 text-[#C88A16] shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">15% Processing Fee Applicable:</span> Administrative & processing fee of 15% is deducted on payout disbursement. You will receive <span className="font-mono font-bold text-[#18211F]">₹{netAmount > 0 ? netAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}</span> in your destination account.
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleClose}
                className="flex-1 px-4 py-3 rounded-2xl border border-[#E5E0D3] hover:bg-[#EFECE2] text-[#18211F] text-xs font-semibold transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || availableBalance <= 0 || !user?.is_active}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/30 text-xs font-heading font-bold shadow-wealth-card transition-all disabled:opacity-50 cursor-pointer"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-[#C9A227]" />
                    <span>Submitting...</span>
                  </>
                ) : (
                  <>
                    <ArrowUpRight className="w-4 h-4 text-[#C9A227]" />
                    <span>Request Payout</span>
                  </>
                )}
              </button>
            </div>
          </form>
        ) : (
          <div className="text-center py-4">
            <div className="w-14 h-14 rounded-2xl bg-[#FAF4DC] border border-[#E2C766] text-[#8C6C16] flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="w-8 h-8 text-[#063B32]" />
            </div>

            <h3 className="text-xl font-heading font-extrabold text-[#18211F] mb-1">Withdrawal Requested</h3>
            <p className="text-[#8C6C16] font-bold text-xs mb-4">
              Status: PENDING ADMIN APPROVAL
            </p>

            <div className="p-4 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] mb-5 text-left space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-[#69736F] font-medium">Request Code:</span>
                <span className="font-mono text-[#18211F] font-bold">{submitted.withdrawal_code}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#69736F] font-medium">Requested Gross:</span>
                <span className="font-mono text-[#18211F] font-bold">₹{submitted.amount?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between text-amber-800">
                <span className="font-medium">Processing Fee (15%):</span>
                <span className="font-mono font-bold">- ₹{(submitted.fee_amount ?? (submitted.amount * 0.15))?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
              <div className="h-px bg-[#E5E0D3]" />
              <div className="flex justify-between text-[#063B32]">
                <span className="font-heading font-extrabold">Final Payout (Disbursed):</span>
                <span className="font-mono text-sm font-black">₹{(submitted.net_amount ?? (submitted.amount * 0.85))?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between pt-1">
                <span className="text-[#69736F] font-medium">Destination:</span>
                <span className="text-[#18211F] font-semibold">{submitted.payout_method === 'VIRTUAL_UPI' ? 'UPI Transfer' : 'Bank Account'}</span>
              </div>
            </div>

            <p className="text-[11px] text-[#69736F] mb-4">
              Your payout request has been queued for administrative processing and settlement.
            </p>

            <button
              onClick={handleClose}
              className="w-full py-3 rounded-2xl bg-[#EFECE2] hover:bg-[#E5E0D3] text-[#18211F] text-xs font-bold transition-colors cursor-pointer"
            >
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
};


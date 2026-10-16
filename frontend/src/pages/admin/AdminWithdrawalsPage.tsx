import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useToast } from '../../context/ToastContext';
import { Withdrawal } from '../../types';
import { 
  Wallet, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  ChevronLeft, 
  ChevronRight, 
  Check, 
  X, 
  Loader2,
  Percent
} from 'lucide-react';

export const AdminWithdrawalsPage: React.FC = () => {
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [processingId, setProcessingId] = useState<number | null>(null);
  const [selectedWithdrawalForApproval, setSelectedWithdrawalForApproval] = useState<Withdrawal | null>(null);
  const [adminNotes, setAdminNotes] = useState('');

  const { data, isLoading } = useQuery<{
    items: Withdrawal[];
    total: number;
    pages: number;
    page: number;
  }>({
    queryKey: ['adminWithdrawals', page, statusFilter],
    queryFn: async () => {
      const url = `/admin/withdrawals?page=${page}&per_page=15${statusFilter ? `&status=${statusFilter}` : ''}`;
      const res = await api.get(url);
      return res.data.data;
    },
  });

  const handleOpenApproveModal = (w: Withdrawal) => {
    setSelectedWithdrawalForApproval(w);
    setAdminNotes('Approved via Admin Panel');
  };

  const handleConfirmApprove = async () => {
    if (!selectedWithdrawalForApproval) return;
    const id = selectedWithdrawalForApproval.id;
    setProcessingId(id);
    try {
      const res = await api.post(`/admin/withdrawals/${id}/approve`, {
        notes: adminNotes || 'Approved via Admin Panel',
      });
      if (res.data?.success) {
        showToast(`Withdrawal ${selectedWithdrawalForApproval.withdrawal_code} approved. Net ₹${(selectedWithdrawalForApproval.net_amount ?? (selectedWithdrawalForApproval.amount * 0.85)).toLocaleString()} settled.`, 'success');
        setSelectedWithdrawalForApproval(null);
        queryClient.invalidateQueries({ queryKey: ['adminWithdrawals'] });
        queryClient.invalidateQueries({ queryKey: ['adminDashboard'] });
        queryClient.invalidateQueries({ queryKey: ['adminUsers'] });
      }
    } catch (err: any) {
      showToast(err.response?.data?.error?.message || 'Approval failed.', 'error');
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (id: number) => {
    setProcessingId(id);
    try {
      const res = await api.post(`/admin/withdrawals/${id}/reject`, {
        notes: 'Rejected by Administrator',
      });
      if (res.data?.success) {
        showToast('Withdrawal request marked as Rejected.', 'info');
        queryClient.invalidateQueries({ queryKey: ['adminWithdrawals'] });
        queryClient.invalidateQueries({ queryKey: ['adminDashboard'] });
      }
    } catch (err: any) {
      showToast(err.response?.data?.error?.message || 'Rejection failed.', 'error');
    } finally {
      setProcessingId(null);
    }
  };

  // Calculate queue aggregates
  const pendingItems = data?.items.filter(w => w.status === 'PENDING') || [];
  const pendingGross = pendingItems.reduce((acc, curr) => acc + curr.amount, 0);
  const pendingFee = pendingItems.reduce((acc, curr) => acc + (curr.fee_amount ?? (curr.amount * 0.15)), 0);
  const pendingNet = pendingItems.reduce((acc, curr) => acc + (curr.net_amount ?? (curr.amount * 0.85)), 0);

  return (
    <div className="space-y-5 sm:space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
        <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-[#C9A227] mb-1">
          <Wallet className="w-4 h-4 text-[#063B32]" />
          <span>Payout Operations</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-[#18211F] tracking-tight">Withdrawal Approval Queue</h1>
        <p className="text-xs sm:text-sm text-[#69736F] font-medium">
          Review, verify, and approve distributor payout requests with mandatory 15% processing fee deduction.
        </p>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-5 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
          <div className="flex items-center justify-between text-xs font-mono font-bold uppercase tracking-wider text-[#69736F] mb-1">
            <span>Pending Gross Volume</span>
            <Clock className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-xl sm:text-2xl font-heading font-black text-[#18211F] font-mono">
            ₹{pendingGross.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-[#69736F] font-medium mt-1">
            {pendingItems.length} requests awaiting administrative action
          </div>
        </div>

        <div className="p-5 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
          <div className="flex items-center justify-between text-xs font-mono font-bold uppercase tracking-wider text-amber-800 mb-1">
            <span>15% Processing Fees</span>
            <Percent className="w-4 h-4 text-amber-700" />
          </div>
          <div className="text-xl sm:text-2xl font-heading font-black text-amber-800 font-mono">
            ₹{pendingFee.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-amber-700/80 font-medium mt-1">
            Platform fee retained upon payout release
          </div>
        </div>

        <div className="p-5 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
          <div className="flex items-center justify-between text-xs font-mono font-bold uppercase tracking-wider text-[#063B32] mb-1">
            <span>Final Disbursal (Net)</span>
            <CheckCircle2 className="w-4 h-4 text-[#063B32]" />
          </div>
          <div className="text-xl sm:text-2xl font-heading font-black text-[#063B32] font-mono">
            ₹{pendingNet.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-[#063B32]/70 font-medium mt-1">
            Net payout payable to distributors
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 p-3 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card overflow-x-auto">
        {[
          { label: 'All Requests', value: '' },
          { label: 'Pending Only', value: 'PENDING' },
          { label: 'Approved', value: 'APPROVED' },
          { label: 'Rejected', value: 'REJECTED' },
        ].map((tab) => (
          <button
            key={tab.value}
            onClick={() => {
              setStatusFilter(tab.value);
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-xl text-xs font-heading font-bold transition-all cursor-pointer whitespace-nowrap ${
              statusFilter === tab.value
                ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs'
                : 'text-[#69736F] hover:text-[#18211F] hover:bg-[#F7F4EC]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="rounded-3xl bg-[#FFFEF9] p-6 border border-[#E5E0D3] shadow-wealth-card space-y-4">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#E5E0D3] text-[#69736F] font-bold uppercase tracking-wider text-[10px] bg-[#F7F4EC]/60">
                <th className="py-3 px-4">Request Code</th>
                <th className="py-3 px-4">Distributor</th>
                <th className="py-3 px-4 text-right">Gross Requested (₹)</th>
                <th className="py-3 px-4 text-right">Fee (15%)</th>
                <th className="py-3 px-4 text-right">Final Payout (Net ₹)</th>
                <th className="py-3 px-4">Method & Details</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-right">Date</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E0D3]/60 font-sans">
              {isLoading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-[#69736F]">
                    Loading withdrawal requests...
                  </td>
                </tr>
              ) : data?.items && data.items.length > 0 ? (
                data.items.map((w) => {
                  const feeAmt = w.fee_amount ?? Math.round(w.amount * 0.15 * 100) / 100;
                  const netAmt = w.net_amount ?? Math.round((w.amount - feeAmt) * 100) / 100;

                  return (
                    <tr key={w.id} className="hover:bg-[#F7F4EC]/40 transition-colors">
                      <td className="py-3 px-4 font-mono font-bold text-[#18211F]">
                        {w.withdrawal_code}
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-bold text-[#18211F]">{w.user_name || 'Distributor'}</div>
                        <div className="text-[11px] text-[#69736F] font-mono">{w.user_code}</div>
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-xs text-[#18211F]">
                        ₹{w.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="font-mono font-bold text-xs text-amber-800">
                          -₹{feeAmt.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </div>
                        <div className="text-[10px] text-amber-700/80 font-sans font-semibold">15% Fee</div>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="font-mono font-black text-sm text-[#063B32]">
                          ₹{netAmt.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </div>
                        <div className="text-[10px] text-emerald-800 font-sans font-bold">Disbursal Amount</div>
                      </td>
                      <td className="py-3 px-4 text-[#18211F]">
                        <div className="font-semibold text-[#18211F]">{w.payout_method}</div>
                        <div className="text-[10px] text-[#69736F] font-mono">
                          {w.payout_details?.upi_id || w.payout_details?.account_number || 'Standard Payout Account'}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${
                            w.status === 'APPROVED'
                              ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
                              : w.status === 'PENDING'
                              ? 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766]'
                              : 'bg-rose-50 text-rose-700 border-rose-200'
                          }`}
                        >
                          {w.status === 'APPROVED' && <CheckCircle2 className="w-3 h-3 text-[#063B32]" />}
                          {w.status === 'PENDING' && <Clock className="w-3 h-3 text-[#8C6C16]" />}
                          {w.status === 'REJECTED' && <XCircle className="w-3 h-3" />}
                          <span>{w.status}</span>
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-[#69736F] text-[11px]">
                        {new Date(w.created_at).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {w.status === 'PENDING' ? (
                          <div className="flex items-center justify-center gap-1.5">
                            <button
                              disabled={processingId === w.id}
                              onClick={() => handleOpenApproveModal(w)}
                              className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/40 font-heading font-bold text-[11px] transition-colors disabled:opacity-50 cursor-pointer shadow-xs"
                            >
                              <Check className="w-3.5 h-3.5 text-[#C9A227]" />
                              <span>Approve</span>
                            </button>
                            <button
                              disabled={processingId === w.id}
                              onClick={() => handleReject(w.id)}
                              className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-heading font-bold text-[11px] transition-colors disabled:opacity-50 cursor-pointer"
                            >
                              <X className="w-3.5 h-3.5" />
                              <span>Reject</span>
                            </button>
                          </div>
                        ) : (
                          <span className="text-[11px] text-[#69736F] font-mono">
                            {w.processed_at ? `Processed ${new Date(w.processed_at).toLocaleDateString()}` : 'Completed'}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-[#69736F]">
                    No withdrawal requests found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-between pt-4 border-t border-[#E5E0D3] text-xs">
            <span className="text-[#69736F]">
              Page {data.page} of {data.pages} ({data.total} records)
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                className="p-2 rounded-xl bg-[#F7F4EC] hover:bg-[#EFECE2] disabled:opacity-40 text-[#18211F] cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                disabled={page >= data.pages}
                onClick={() => setPage((p) => p + 1)}
                className="p-2 rounded-xl bg-[#F7F4EC] hover:bg-[#EFECE2] disabled:opacity-40 text-[#18211F] cursor-pointer"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Admin Approval Confirmation Modal with 15% Fee Breakdown */}
      {selectedWithdrawalForApproval && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
          <div 
            className="w-full max-w-lg rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-elevated p-6 relative overflow-hidden text-[#18211F]"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setSelectedWithdrawalForApproval(null)}
              className="absolute top-4 right-4 p-2 rounded-xl text-[#69736F] hover:text-[#18211F] hover:bg-[#EFECE2] transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2 text-[#063B32] text-xs font-mono font-bold uppercase tracking-wider mb-1">
              <CheckCircle2 className="w-4 h-4 text-[#C9A227]" />
              <span>Confirm Payout Settlement</span>
            </div>

            <h2 className="text-2xl font-heading font-extrabold text-[#18211F] mb-1">
              Approve Withdrawal
            </h2>
            <p className="text-[#69736F] text-xs mb-4">
              Review 15% fee deduction breakdown and confirm net disbursal for request{' '}
              <span className="font-mono font-bold text-[#18211F]">{selectedWithdrawalForApproval.withdrawal_code}</span>.
            </p>

            {/* Recipient Card */}
            <div className="p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] mb-4 text-xs space-y-1.5">
              <div className="flex justify-between">
                <span className="text-[#69736F]">Distributor:</span>
                <span className="font-bold text-[#18211F]">
                  {selectedWithdrawalForApproval.user_name} ({selectedWithdrawalForApproval.user_code})
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#69736F]">Destination:</span>
                <span className="font-semibold text-[#18211F]">
                  {selectedWithdrawalForApproval.payout_method === 'VIRTUAL_UPI' ? 'UPI Transfer' : 'Bank Transfer'}
                </span>
              </div>
              {selectedWithdrawalForApproval.payout_details?.upi_id && (
                <div className="flex justify-between">
                  <span className="text-[#69736F]">UPI ID:</span>
                  <span className="font-mono font-bold text-[#063B32]">
                    {selectedWithdrawalForApproval.payout_details.upi_id}
                  </span>
                </div>
              )}
              {selectedWithdrawalForApproval.payout_details?.account_number && (
                <>
                  <div className="flex justify-between">
                    <span className="text-[#69736F]">Account No:</span>
                    <span className="font-mono font-bold text-[#063B32]">
                      {selectedWithdrawalForApproval.payout_details.account_number}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#69736F]">IFSC Code:</span>
                    <span className="font-mono font-bold text-[#063B32]">
                      {selectedWithdrawalForApproval.payout_details.ifsc}
                    </span>
                  </div>
                </>
              )}
            </div>

            {/* Financial Deduction Breakdown */}
            <div className="p-4 rounded-2xl bg-[#FAF4DC]/60 border border-[#E2C766]/80 mb-4 space-y-2 text-xs">
              <div className="flex justify-between text-[#69736F]">
                <span>Requested Gross Amount:</span>
                <span className="font-mono font-bold text-[#18211F]">
                  ₹{selectedWithdrawalForApproval.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between text-amber-800">
                <span className="flex items-center gap-1 font-medium">
                  <span>Processing Fee Deduction</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-amber-100 border border-amber-300 font-bold font-mono">
                    15%
                  </span>
                </span>
                <span className="font-mono font-bold">
                  - ₹{(selectedWithdrawalForApproval.fee_amount ?? (selectedWithdrawalForApproval.amount * 0.15)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
              <div className="h-px bg-[#E2C766]/80 my-1" />
              <div className="flex justify-between items-center text-[#063B32]">
                <span className="font-heading font-extrabold text-sm">Final Amount to Disburse:</span>
                <span className="font-mono font-black text-lg text-[#063B32]">
                  ₹{(selectedWithdrawalForApproval.net_amount ?? (selectedWithdrawalForApproval.amount * 0.85)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
            </div>

            {/* Admin Notes */}
            <div className="mb-5">
              <label className="block text-xs font-semibold text-[#18211F] mb-1.5">
                Approval Reference / Notes
              </label>
              <input
                type="text"
                value={adminNotes}
                onChange={(e) => setAdminNotes(e.target.value)}
                placeholder="e.g. Disbursed via Banking Portal Ref #12345"
                className="w-full px-3.5 py-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] font-mono text-xs focus:outline-none focus:border-[#063B32] shadow-xs"
              />
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setSelectedWithdrawalForApproval(null)}
                className="flex-1 px-4 py-3 rounded-2xl border border-[#E5E0D3] hover:bg-[#EFECE2] text-[#18211F] text-xs font-semibold transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={processingId === selectedWithdrawalForApproval.id}
                onClick={handleConfirmApprove}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/30 text-xs font-heading font-bold shadow-wealth-card transition-all disabled:opacity-50 cursor-pointer"
              >
                {processingId === selectedWithdrawalForApproval.id ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-[#C9A227]" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4 text-[#C9A227]" />
                    <span>Confirm & Approve</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};


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
  Loader2 
} from 'lucide-react';

export const AdminWithdrawalsPage: React.FC = () => {
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [processingId, setProcessingId] = useState<number | null>(null);

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

  const handleApprove = async (id: number) => {
    setProcessingId(id);
    try {
      const res = await api.post(`/admin/withdrawals/${id}/approve`, {
        notes: 'Approved via Admin Panel',
      });
      if (res.data?.success) {
        showToast('Withdrawal approved and user wallet debited successfully.', 'success');
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
          Review, approve, or reject pending withdrawal requests submitted by distributors.
        </p>
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
                <th className="py-3 px-4 text-right">Amount (₹)</th>
                <th className="py-3 px-4">Method & Details</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-right">Date</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E0D3]/60 font-sans">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-[#69736F]">
                    Loading withdrawal requests...
                  </td>
                </tr>
              ) : data?.items && data.items.length > 0 ? (
                data.items.map((w) => (
                  <tr key={w.id} className="hover:bg-[#F7F4EC]/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-[#18211F]">
                      {w.withdrawal_code}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-bold text-[#18211F]">{w.user_name || 'Distributor'}</div>
                      <div className="text-[11px] text-[#69736F] font-mono">{w.user_code}</div>
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-black text-sm text-[#063B32]">
                      ₹{w.amount.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-[#18211F]">
                      <div className="font-semibold text-[#18211F]">{w.payout_method}</div>
                      <div className="text-[10px] text-[#69736F] font-mono">
                        {w.payout_details?.upi_id || w.payout_details?.account_number || 'Demo Account'}
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
                            onClick={() => handleApprove(w.id)}
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
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-[#69736F]">
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
    </div>
  );
};


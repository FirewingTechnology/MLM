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
  Filter, 
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
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400 mb-1">
          <Wallet className="w-4 h-4" />
          <span>Payout Operations</span>
        </div>
        <h1 className="text-2xl font-black text-white">Withdrawal Approval Queue</h1>
        <p className="text-xs text-slate-400">
          Review, approve, or reject pending virtual withdrawal requests submitted by distributors.
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 p-3 rounded-2xl glass-panel border border-slate-800">
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
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              statusFilter === tab.value
                ? 'bg-amber-500 text-navy-950 shadow-glow-amber'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="rounded-3xl glass-panel p-6 border border-slate-800 space-y-4">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800/80 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Request Code</th>
                <th className="py-3 px-4">Distributor</th>
                <th className="py-3 px-4 text-right">Amount (₹)</th>
                <th className="py-3 px-4">Method & Details</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-right">Date</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    Loading withdrawal requests...
                  </td>
                </tr>
              ) : data?.items && data.items.length > 0 ? (
                data.items.map((w) => (
                  <tr key={w.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-white">
                      {w.withdrawal_code}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-100">{w.user_name || 'Distributor'}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{w.user_code}</div>
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-black text-sm text-emerald-400">
                      ₹{w.amount.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      <div className="font-semibold text-white">{w.payout_method}</div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {w.payout_details?.upi_id || w.payout_details?.account_number || 'Demo Account'}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${
                          w.status === 'APPROVED'
                            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                            : w.status === 'PENDING'
                            ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                            : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                        }`}
                      >
                        {w.status === 'APPROVED' && <CheckCircle2 className="w-3 h-3" />}
                        {w.status === 'PENDING' && <Clock className="w-3 h-3" />}
                        {w.status === 'REJECTED' && <XCircle className="w-3 h-3" />}
                        <span>{w.status}</span>
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-slate-400 text-[11px]">
                      {new Date(w.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {w.status === 'PENDING' ? (
                        <div className="flex items-center justify-center gap-1.5">
                          <button
                            disabled={processingId === w.id}
                            onClick={() => handleApprove(w.id)}
                            className="flex items-center gap-1 px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[11px] transition-colors disabled:opacity-50"
                          >
                            <Check className="w-3.5 h-3.5" />
                            <span>Approve</span>
                          </button>
                          <button
                            disabled={processingId === w.id}
                            onClick={() => handleReject(w.id)}
                            className="flex items-center gap-1 px-3 py-1 rounded-lg bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 font-bold text-[11px] transition-colors disabled:opacity-50"
                          >
                            <X className="w-3.5 h-3.5" />
                            <span>Reject</span>
                          </button>
                        </div>
                      ) : (
                        <span className="text-[11px] text-slate-500 font-mono">
                          {w.processed_at ? `Processed on ${new Date(w.processed_at).toLocaleDateString()}` : 'Completed'}
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No withdrawal requests found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-between pt-4 border-t border-slate-800 text-xs">
            <span className="text-slate-400">
              Page {data.page} of {data.pages} ({data.total} records)
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                disabled={page >= data.pages}
                onClick={() => setPage((p) => p + 1)}
                className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300"
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

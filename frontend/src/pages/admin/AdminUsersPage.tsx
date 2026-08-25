import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useToast } from '../../context/ToastContext';
import { User } from '../../types';
import { AdminAdjustmentModal } from '../../components/modals/AdminAdjustmentModal';
import { 
  Users, 
  Search, 
  Filter, 
  CheckCircle2, 
  Clock, 
  DollarSign, 
  GitFork, 
  ChevronLeft, 
  ChevronRight,
  Shield,
  RotateCcw
} from 'lucide-react';

export const AdminUsersPage: React.FC = () => {
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [selectedUserForAdjustment, setSelectedUserForAdjustment] = useState<User | null>(null);

  const { data, isLoading } = useQuery<{
    items: User[];
    total: number;
    pages: number;
    page: number;
  }>({
    queryKey: ['adminUsers', page, search, statusFilter],
    queryFn: async () => {
      const url = `/admin/users?page=${page}&per_page=15${search ? `&search=${search}` : ''}${statusFilter ? `&status=${statusFilter}` : ''}`;
      const res = await api.get(url);
      return res.data.data;
    },
  });

  const handleToggleStatus = async (user: User) => {
    try {
      const res = await api.post(`/admin/users/${user.id}/status`, {
        is_active: !user.is_active,
      });
      if (res.data?.success) {
        showToast(`User status updated to ${!user.is_active ? 'Active' : 'Inactive'}.`, 'success');
        queryClient.invalidateQueries({ queryKey: ['adminUsers'] });
        queryClient.invalidateQueries({ queryKey: ['adminDashboard'] });
      }
    } catch (err: any) {
      showToast(err.response?.data?.error?.message || 'Failed to toggle user status.', 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400 mb-1">
            <Users className="w-4 h-4" />
            <span>Admin Directory</span>
          </div>
          <h1 className="text-2xl font-black text-white">Distributor Management</h1>
          <p className="text-xs text-slate-400">
            Inspect all registered accounts, binary positions, wallet balances, and manually adjust ledgers.
          </p>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-4 rounded-3xl glass-panel border border-slate-800">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Search by name, code, email, mobile..."
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-navy-900 border border-slate-700/80 text-white text-xs focus:outline-none focus:border-amber-500 font-mono"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          {[
            { label: 'All Statuses', value: '' },
            { label: 'Active Only', value: 'active' },
            { label: 'Inactive Only', value: 'inactive' },
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
      </div>

      {/* Users Table */}
      <div className="rounded-3xl glass-panel p-6 border border-slate-800 space-y-4">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800/80 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Distributor</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Sponsor</th>
                <th className="py-3 px-4">Placement</th>
                <th className="py-3 px-4 text-right">Wallet Balance</th>
                <th className="py-3 px-4 text-right">Left / Right BV</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {isLoading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400">
                    Loading users list...
                  </td>
                </tr>
              ) : data?.items && data.items.length > 0 ? (
                data.items.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-white">{u.full_name}</div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        {u.user_code} • {u.email}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                        u.role === 'ADMIN' ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-800 text-slate-300'
                      }`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      {u.sponsor_name || 'None (Root)'}
                    </td>
                    <td className="py-3 px-4">
                      <div className="text-slate-200">{u.binary_parent_name || 'Root'}</div>
                      <div className="text-[10px] font-mono text-slate-400">{u.binary_position || 'ROOT'}</div>
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-emerald-400">
                      ₹{u.wallet_balance?.toLocaleString() || 0}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-[11px]">
                      <div className="text-slate-300">L: ₹{u.left_bv?.toLocaleString() || 0}</div>
                      <div className="text-slate-400">R: ₹{u.right_bv?.toLocaleString() || 0}</div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => handleToggleStatus(u)}
                        className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border transition-all ${
                          u.is_active
                            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 hover:bg-emerald-500/30'
                            : 'bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30'
                        }`}
                        title="Click to toggle status"
                      >
                        {u.is_active ? <CheckCircle2 className="w-3 h-3" /> : <Clock className="w-3 h-3" />}
                        <span>{u.is_active ? 'Active' : 'Inactive'}</span>
                      </button>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => setSelectedUserForAdjustment(u)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[11px] font-bold transition-all"
                      >
                        <DollarSign className="w-3 h-3" />
                        <span>Adjust Balance</span>
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    No distributors matched the criteria.
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

      <AdminAdjustmentModal
        user={selectedUserForAdjustment}
        onClose={() => setSelectedUserForAdjustment(null)}
      />
    </div>
  );
};

import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useToast } from '../../context/ToastContext';
import { User } from '../../types';
import { AdminAdjustmentModal } from '../../components/modals/AdminAdjustmentModal';
import {
  Users,
  Search,
  CheckCircle2,
  Clock,
  DollarSign,
  ChevronLeft,
  ChevronRight,
  ShieldAlert
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
    <div className="space-y-5 sm:space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-[#C9A227] mb-1">
            <Users className="w-4 h-4 text-[#063B32]" />
            <span>Admin Directory</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-[#18211F] tracking-tight">Distributor Management</h1>
          <p className="text-xs sm:text-sm text-[#69736F] font-medium">
            Inspect all registered accounts, Matching positions, wallet balances, and manually adjust ledgers.
          </p>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-4 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-[#69736F] absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Search by name, code, email..."
            className="w-full pl-9 pr-4 py-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] text-xs focus:outline-none focus:border-[#063B32] font-mono shadow-xs"
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
              className={`px-3 py-1.5 rounded-xl text-xs font-heading font-bold transition-all cursor-pointer ${statusFilter === tab.value
                  ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs'
                  : 'text-[#69736F] hover:text-[#18211F] hover:bg-[#F7F4EC]'
                }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Users Table */}
      <div className="rounded-3xl bg-[#FFFEF9] p-6 border border-[#E5E0D3] shadow-wealth-card space-y-4">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#E5E0D3] text-[#69736F] font-bold uppercase tracking-wider text-[10px] bg-[#F7F4EC]/60">
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
            <tbody className="divide-y divide-[#E5E0D3]/60 font-sans">
              {isLoading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-[#69736F]">
                    Loading users list...
                  </td>
                </tr>
              ) : data?.items && data.items.length > 0 ? (
                data.items.map((u) => (
                  <tr key={u.id} className="hover:bg-[#F7F4EC]/40 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-[#18211F]">{u.full_name}</div>
                      <div className="text-[11px] text-[#69736F] font-mono">
                        {u.user_code} • {u.email}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${u.role === 'ADMIN' ? 'bg-[#FAF4DC] text-[#8C6C16] border border-[#E2C766]' : 'bg-[#F7F4EC] text-[#69736F] border border-[#E5E0D3]'
                        }`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[#18211F]">
                      {u.sponsor_name || 'None (Root)'}
                    </td>
                    <td className="py-3 px-4">
                      <div className="text-[#18211F] font-medium">{u.binary_parent_name || 'Root'}</div>
                      <div className="text-[10px] font-mono text-[#69736F]">{u.binary_position || 'ROOT'}</div>
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-[#063B32]">
                      ₹{u.wallet_balance?.toLocaleString() || 0}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-[11px]">
                      <div className="text-[#063B32] font-semibold">L: ₹{u.left_bv?.toLocaleString() || 0}</div>
                      <div className="text-[#8C6C16] font-semibold">R: ₹{u.right_bv?.toLocaleString() || 0}</div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => handleToggleStatus(u)}
                        className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border transition-all cursor-pointer ${u.is_active
                            ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF] hover:bg-[#CBECE3]'
                            : 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766] hover:bg-[#F2E8C4]'
                          }`}
                        title="Click to toggle status"
                      >
                        {u.is_active ? <CheckCircle2 className="w-3 h-3 text-[#063B32]" /> : <Clock className="w-3 h-3 text-[#8C6C16]" />}
                        <span>{u.is_active ? 'Active' : 'Inactive'}</span>
                      </button>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => setSelectedUserForAdjustment(u)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-[#F7F4EC] hover:bg-[#063B32] hover:text-[#FFFEF9] text-[#18211F] border border-[#E5E0D3] text-[11px] font-heading font-bold transition-all cursor-pointer"
                      >
                        <DollarSign className="w-3 h-3 text-[#C9A227]" />
                        <span>Adjust Balance</span>
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-[#69736F]">
                    No distributors matched the criteria.
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

      <AdminAdjustmentModal
        user={selectedUserForAdjustment}
        onClose={() => setSelectedUserForAdjustment(null)}
      />
    </div>
  );
};


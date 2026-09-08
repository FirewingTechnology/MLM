import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { Commission } from '../types';
import { CommissionDetailModal } from '../components/modals/CommissionDetailModal';
import {
  Coins,
  HelpCircle,
  Award,
  GitFork,
  Filter,
  ChevronLeft,
  ChevronRight,
  Sparkles
} from 'lucide-react';

export const CommissionsPage: React.FC = () => {
  const [selectedType, setSelectedType] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [selectedCommission, setSelectedCommission] = useState<Commission | null>(null);

  const { data, isLoading } = useQuery<{
    items: Commission[];
    total: number;
    pages: number;
    page: number;
    total_direct_amount: number;
    total_matching_amount: number;
    total_pair_amount?: number;
    total_carry_amount?: number;
  }>({
    queryKey: ['commissions', page, selectedType],
    queryFn: async () => {
      const url = `/commissions?page=${page}&per_page=15${selectedType ? `&type=${selectedType}` : ''}`;
      const res = await api.get(url);
      return res.data.data;
    },
  });

  return (
    <div className="space-y-5 sm:space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
        <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-[#C9A227] mb-1">
          <Coins className="w-4 h-4 text-[#063B32]" />
          <span>Income Report & Breakdown</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-[#18211F] tracking-tight">Income Report & Transparency Audit</h1>
        <p className="text-xs sm:text-sm text-[#69736F] font-medium">
          Auditable record of all direct sponsor and Matching pair bonus income.
        </p>
      </div>

      {/* Summary Stat Cards - Final Client Commission Model: Direct Commission & Pair Bonus */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        {/* Direct Referral Bonus in Deep Emerald Card */}
        <div className="rounded-3xl bg-[#FFFEF9] p-5 border border-[#8DCFBF] shadow-wealth-card flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#063B32] flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-[#0E9F6E]" />
              <span>Direct Sponsor (10%)</span>
            </span>
            <div className="w-8 h-8 rounded-lg bg-[#E0F3EE] text-[#063B32] flex items-center justify-center">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl sm:text-3xl font-heading font-black text-[#063B32] font-mono mt-3">
            ₹{data?.total_direct_amount?.toLocaleString() || 0}
          </div>
          <div className="text-xs text-[#69736F] mt-1">10% on direct sponsor package BV</div>
        </div>

        {/* Pair Bonus in Champagne Gold Card */}
        <div className="rounded-3xl bg-[#FFFEF9] p-5 border border-[#E2C766] shadow-wealth-card flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8C6C16] flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-[#C9A227]" />
              <span>Pair Bonus (₹15k)</span>
            </span>
            <div className="w-8 h-8 rounded-lg bg-[#FAF4DC] text-[#8C6C16] flex items-center justify-center">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl sm:text-3xl font-heading font-black text-[#8C6C16] font-mono mt-3">
            ₹{(data?.total_pair_amount || 0).toLocaleString()}
          </div>
          <div className="text-xs text-[#69736F] mt-1">30k/30k matching pair (exclusive to earner)</div>
        </div>
      </div>

      {/* Historical Legacy Commissions Card (Displayed only if legacy records exist) */}
      {((data?.total_matching_amount || 0) > 0 || (data?.total_carry_amount || 0) > 0) && (
        <div className="rounded-2xl bg-[#F7F4EC] p-4 border border-[#E5E0D3] flex items-center justify-between text-xs text-[#69736F]">
          <span className="font-semibold">Historical Legacy Earnings (Archived):</span>
          <div className="flex gap-4 font-mono font-medium">
            {(data?.total_matching_amount || 0) > 0 && <span>Matching: ₹{data?.total_matching_amount?.toLocaleString()}</span>}
            {(data?.total_carry_amount || 0) > 0 && <span>Carry: ₹{data?.total_carry_amount?.toLocaleString()}</span>}
          </div>
        </div>
      )}

      {/* Filter Tabs & Commission Table */}
      <div className="rounded-3xl bg-[#FFFEF9] p-6 border border-[#E5E0D3] shadow-wealth-card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E5E0D3] pb-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-[#063B32]" />
            <span className="text-sm font-heading font-extrabold text-[#18211F]">Income Report Log</span>
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
            {[
              { label: 'All Income', value: '' },
              { label: '🟢 Direct Sponsor', value: 'DIRECT_COMMISSION' },
              { label: '🟣 Pair Bonus (₹15k)', value: 'PAIR_BONUS' },
            ].map((tab) => (
              <button
                key={tab.value}
                onClick={() => {
                  setSelectedType(tab.value);
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${selectedType === tab.value
                    ? 'bg-[#063B32] text-[#FFFEF9] font-bold shadow-xs'
                    : 'text-[#69736F] hover:text-[#18211F] hover:bg-[#F7F4EC]'
                  }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#E5E0D3] text-[#69736F] font-bold uppercase tracking-wider text-[10px] bg-[#F7F4EC]/60">
                <th className="py-3 px-4">Income ID</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Triggered By</th>
                <th className="py-3 px-4 text-right">BV Basis</th>
                <th className="py-3 px-4 text-right">Income Amount</th>
                <th className="py-3 px-4 text-right">Date</th>
                <th className="py-3 px-4 text-center">Audit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E0D3]/60 font-mono">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-[#69736F]">
                    Loading income report...
                  </td>
                </tr>
              ) : data?.items && data.items.length > 0 ? (
                data.items.map((comm) => (
                  <tr key={comm.id} className="hover:bg-[#F7F4EC]/40 transition-colors">
                    <td className="py-3 px-4 text-[#18211F] font-bold">
                      {comm.commission_code}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`text-[10px] px-2.5 py-0.5 rounded font-sans font-bold border ${comm.commission_type === 'PAIR_BONUS'
                          ? 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766]'
                          : comm.commission_type === 'DIRECT_REFERRAL' || comm.commission_type === 'DIRECT_COMMISSION'
                            ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
                            : comm.commission_type === 'MATCHING_COMMISSION' || comm.commission_type === 'BINARY_MATCHING'
                              ? 'bg-[#FFEDD5] text-[#C2410C] border-[#FDBA74]'
                              : 'bg-[#DBEAFE] text-[#1D4ED8] border-[#93C5FD]'
                        }`}>
                        {comm.commission_type === 'PAIR_BONUS'
                          ? '🟣 Pair Bonus (₹15k)'
                          : comm.commission_type === 'DIRECT_REFERRAL' || comm.commission_type === 'DIRECT_COMMISSION'
                            ? '🟢 Direct Sponsor'
                            : comm.commission_type === 'MATCHING_COMMISSION' || comm.commission_type === 'BINARY_MATCHING'
                              ? '🟠 Matching Upline'
                              : '🔵 Carry Bonus'}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-sans text-[#18211F] font-medium">
                      {comm.source_user_name || 'Network Member'}
                      {comm.source_user_code && <span className="text-[#69736F] font-mono ml-1 font-normal">({comm.source_user_code})</span>}
                    </td>
                    <td className="py-3 px-4 text-right text-[#18211F] font-medium">
                      {comm.bv_basis ? `₹${comm.bv_basis.toLocaleString()}` : `${comm.bv_amount.toLocaleString()} BV`}
                    </td>
                    <td className="py-3 px-4 text-right text-[#063B32] font-bold">
                      +₹{comm.amount.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right text-[#69736F] text-[11px]">
                      {new Date(comm.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => setSelectedCommission(comm)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#F7F4EC] hover:bg-[#063B32] hover:text-[#FFFEF9] text-[#18211F] text-[11px] font-sans font-bold transition-all border border-[#E5E0D3] cursor-pointer"
                      >
                        <HelpCircle className="w-3.5 h-3.5 text-[#C9A227]" />
                        <span>Why received?</span>
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-[#69736F] font-sans">
                    No income records found.
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

      <CommissionDetailModal
        commission={selectedCommission}
        onClose={() => setSelectedCommission(null)}
      />
    </div>
  );
};


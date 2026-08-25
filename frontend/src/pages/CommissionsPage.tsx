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
  ArrowUpRight 
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
  }>({
    queryKey: ['commissions', page, selectedType],
    queryFn: async () => {
      const url = `/commissions?page=${page}&per_page=15${selectedType ? `&type=${selectedType}` : ''}`;
      const res = await api.get(url);
      return res.data.data;
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-brand-400 mb-1">
          <Coins className="w-4 h-4" />
          <span>Earnings Breakdown</span>
        </div>
        <h1 className="text-2xl font-black text-white">Commissions & Transparency Audit</h1>
        <p className="text-xs text-slate-400">
          Fully auditable record of all direct sponsor and binary matching commissions generated.
        </p>
      </div>

      {/* Summary Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="rounded-3xl glass-panel p-6 border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Direct Referral Bonuses (10%)
            </span>
            <div className="text-2xl font-black text-brand-400 font-mono mt-1">
              ₹{data?.total_direct_amount?.toLocaleString() || 0}
            </div>
            <div className="text-xs text-slate-400 mt-1">Earned when sponsored team buys packages</div>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-brand-500/10 text-brand-400 flex items-center justify-center">
            <Award className="w-6 h-6" />
          </div>
        </div>

        <div className="rounded-3xl glass-panel p-6 border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Binary Matching Bonuses (10%)
            </span>
            <div className="text-2xl font-black text-emerald-400 font-mono mt-1">
              ₹{data?.total_matching_amount?.toLocaleString() || 0}
            </div>
            <div className="text-xs text-slate-400 mt-1">Earned when Left & Right legs match volume</div>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
            <GitFork className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Filter Tabs & Commission Table */}
      <div className="rounded-3xl glass-panel p-6 border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-brand-400" />
            <span className="text-sm font-bold text-white">Commissions Log</span>
          </div>

          <div className="flex items-center gap-1.5">
            {[
              { label: 'All Commissions', value: '' },
              { label: 'Direct Referral Bonus', value: 'DIRECT_REFERRAL' },
              { label: 'Binary Matching Bonus', value: 'BINARY_MATCHING' },
            ].map((tab) => (
              <button
                key={tab.value}
                onClick={() => {
                  setSelectedType(tab.value);
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                  selectedType === tab.value
                    ? 'bg-brand-500 text-navy-950 font-bold shadow-glow-emerald'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
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
              <tr className="border-b border-slate-800/80 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Commission ID</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Triggered By</th>
                <th className="py-3 px-4 text-right">BV Basis</th>
                <th className="py-3 px-4 text-right">Commission (10%)</th>
                <th className="py-3 px-4 text-right">Date</th>
                <th className="py-3 px-4 text-center">Audit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    Loading commissions...
                  </td>
                </tr>
              ) : data?.items && data.items.length > 0 ? (
                data.items.map((comm) => (
                  <tr key={comm.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 text-slate-300 font-bold">
                      {comm.commission_code}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`text-[10px] px-2 py-0.5 rounded font-sans font-semibold border ${
                        comm.commission_type === 'DIRECT_REFERRAL'
                          ? 'bg-brand-500/10 text-brand-300 border-brand-500/30'
                          : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                      }`}>
                        {comm.commission_type === 'DIRECT_REFERRAL' ? 'Direct Bonus' : 'Binary Match'}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-sans text-slate-200 font-medium">
                      {comm.source_user_name || 'Network Member'}
                      {comm.source_user_code && <span className="text-slate-400 font-mono ml-1 font-normal">({comm.source_user_code})</span>}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-300">
                      {comm.bv_amount.toLocaleString()} BV
                    </td>
                    <td className="py-3 px-4 text-right text-emerald-400 font-bold">
                      +₹{comm.amount.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-400 text-[11px]">
                      {new Date(comm.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => setSelectedCommission(comm)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-brand-500 hover:text-navy-950 text-slate-300 text-[11px] font-sans font-bold transition-all"
                      >
                        <HelpCircle className="w-3.5 h-3.5" />
                        <span>Why received?</span>
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500 font-sans">
                    No commissions found.
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

      <CommissionDetailModal
        commission={selectedCommission}
        onClose={() => setSelectedCommission(null)}
      />
    </div>
  );
};

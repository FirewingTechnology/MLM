import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import { AdminDashboardData, SlotSettlement, VolumeLedgerEntry, Commission } from '../../types';
import { DemoTimeControl } from '../../components/admin/DemoTimeControl';
import { CommissionDetailModal } from '../../components/modals/CommissionDetailModal';
import { 
  ShieldAlert, 
  Users, 
  ShoppingBag, 
  Coins, 
  Wallet, 
  Clock, 
  TrendingUp, 
  Activity, 
  CheckCircle2,
  GitFork,
  Layers,
  FileSpreadsheet,
  RotateCcw,
  Zap,
  Filter,
  Search,
  HelpCircle,
  Award,
  Sparkles
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell } from 'recharts';

export const AdminDashboardPage: React.FC = () => {
  const [adminTab, setAdminTab] = useState<'analytics' | 'commissions' | 'settlements' | 'volume_ledger'>('analytics');
  const [selectedCommission, setSelectedCommission] = useState<Commission | null>(null);
  const [commTypeFilter, setCommTypeFilter] = useState<string>('');
  const [commSearch, setCommSearch] = useState<string>('');

  const { data, isLoading } = useQuery<AdminDashboardData>({
    queryKey: ['adminDashboard'],
    queryFn: async () => {
      const res = await api.get('/admin/dashboard');
      return res.data.data;
    },
    refetchInterval: 10000,
  });

  const { data: commissionsData } = useQuery<{ items: Commission[]; total: number }>({
    queryKey: ['adminCommissions', commTypeFilter, commSearch],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append('per_page', '50');
      if (commTypeFilter) params.append('type', commTypeFilter);
      if (commSearch) params.append('search', commSearch);
      const res = await api.get(`/admin/commissions?${params.toString()}`);
      return res.data.data || { items: [], total: 0 };
    },
    enabled: adminTab === 'commissions',
    refetchInterval: 10000,
  });

  const { data: settlementsData } = useQuery<{ items: SlotSettlement[]; total: number }>({
    queryKey: ['adminSettlements'],
    queryFn: async () => {
      const res = await api.get('/admin/settlements?per_page=50');
      return res.data.data || { items: [], total: 0 };
    },
    enabled: adminTab === 'settlements',
    refetchInterval: 10000,
  });

  const { data: volumeLedgerData } = useQuery<{ items: VolumeLedgerEntry[]; total: number }>({
    queryKey: ['adminVolumeLedger'],
    queryFn: async () => {
      const res = await api.get('/admin/volume-ledger?per_page=50');
      return res.data.data || { items: [], total: 0 };
    },
    enabled: adminTab === 'volume_ledger',
    refetchInterval: 10000,
  });

  const kpis = data?.kpis;

  const commissionPieData = [
    { name: 'Direct Sponsor (10%)', value: kpis?.direct_commissions || 0, color: '#063B32' },
    { name: 'Pair Bonus (₹10k)', value: kpis?.pair_commissions || 0, color: '#C9A227' },
    { name: 'Matching Upline', value: kpis?.matching_commissions || 0, color: '#EA580C' },
    { name: 'Carry Commission', value: kpis?.carry_commissions || 0, color: '#3B82F6' },
  ].filter(d => d.value > 0);

  const financialBarData = [
    { name: 'Virtual Sales', amount: kpis?.total_virtual_sales || 0 },
    { name: 'Total Volume', amount: kpis?.total_bv || 0 },
    { name: 'Commissions', amount: kpis?.total_commissions || 0 },
    { name: 'Withdrawn', amount: kpis?.total_withdrawn || 0 },
  ];

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-28 rounded-3xl bg-[#E5E0D3]/60" />
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 rounded-3xl bg-[#E5E0D3]/60" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5 sm:space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-[#8C6C16] mb-1">
            <ShieldAlert className="w-4 h-4 text-[#C9A227]" />
            <span>Superuser Control Center</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-[#18211F] tracking-tight">System Analytics & Audit</h1>
          <p className="text-xs sm:text-sm text-[#69736F] font-medium">
            Platform KPIs, 12-Hour Slot Settlements, Commission Lineage, and Traceable Volume Ledger.
          </p>
        </div>

        {/* Admin Navigation Tabs */}
        <div className="flex items-center gap-1.5 p-1.5 bg-[#F7F4EC] rounded-2xl border border-[#E5E0D3] self-start md:self-auto flex-wrap">
          <button
            onClick={() => setAdminTab('analytics')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              adminTab === 'analytics'
                ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs'
                : 'text-[#69736F] hover:text-[#18211F]'
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Overview</span>
          </button>
          <button
            onClick={() => setAdminTab('commissions')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              adminTab === 'commissions'
                ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs'
                : 'text-[#69736F] hover:text-[#18211F]'
            }`}
          >
            <Coins className="w-3.5 h-3.5 text-[#C9A227]" />
            <span>Commissions Audit</span>
          </button>
          <button
            onClick={() => setAdminTab('settlements')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              adminTab === 'settlements'
                ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs'
                : 'text-[#69736F] hover:text-[#18211F]'
            }`}
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-[#C9A227]" />
            <span>Slot Settlements</span>
          </button>
          <button
            onClick={() => setAdminTab('volume_ledger')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              adminTab === 'volume_ledger'
                ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs'
                : 'text-[#69736F] hover:text-[#18211F]'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-[#063B32]" />
            <span>Volume Ledger</span>
          </button>
        </div>
      </div>

      {/* 0. Demo Time Control Center */}
      <DemoTimeControl />

      {adminTab === 'analytics' && (
        <>
          {/* KPI Cards Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Users */}
            <div className="rounded-3xl bg-[#FFFEF9] p-5 border border-[#E5E0D3] shadow-wealth-card">
              <div className="flex items-center justify-between text-[#69736F] mb-2">
                <span className="text-xs font-mono font-bold uppercase tracking-wider">Total Members</span>
                <Users className="w-4 h-4 text-[#063B32]" />
              </div>
              <div className="text-2xl sm:text-3xl font-heading font-black text-[#18211F] font-mono">
                {kpis?.total_users || 0}
              </div>
              <div className="text-[11px] text-[#063B32] mt-1 font-semibold">
                {kpis?.active_users || 0} Active • {kpis?.inactive_users || 0} Inactive
              </div>
            </div>

            {/* Total Virtual Sales */}
            <div className="rounded-3xl bg-[#FFFEF9] p-5 border border-[#E5E0D3] shadow-wealth-card">
              <div className="flex items-center justify-between text-[#69736F] mb-2">
                <span className="text-xs font-mono font-bold uppercase tracking-wider">Virtual Sales</span>
                <ShoppingBag className="w-4 h-4 text-[#063B32]" />
              </div>
              <div className="text-2xl sm:text-3xl font-heading font-black text-[#063B32] font-mono">
                ₹{kpis?.total_virtual_sales?.toLocaleString() || 0}
              </div>
              <div className="text-[11px] text-[#69736F] mt-1">Total revenue generated</div>
            </div>

            {/* Total Volume */}
            <div className="rounded-3xl bg-[#FFFEF9] p-5 border border-[#E5E0D3] shadow-wealth-card">
              <div className="flex items-center justify-between text-[#69736F] mb-2">
                <span className="text-xs font-mono font-bold uppercase tracking-wider">Total BV Volume</span>
                <Coins className="w-4 h-4 text-[#C9A227]" />
              </div>
              <div className="text-2xl sm:text-3xl font-heading font-black text-[#C9A227] font-mono">
                ₹{kpis?.total_bv?.toLocaleString() || 0} <span className="text-xs font-normal">BV</span>
              </div>
              <div className="text-[11px] text-[#69736F] mt-1">Package Business Value</div>
            </div>

            {/* Total Commissions */}
            <div className="rounded-3xl bg-[#FFFEF9] p-5 border border-[#E5E0D3] shadow-wealth-card">
              <div className="flex items-center justify-between text-[#69736F] mb-2">
                <span className="text-xs font-mono font-bold uppercase tracking-wider">Commissions Paid</span>
                <Wallet className="w-4 h-4 text-[#063B32]" />
              </div>
              <div className="text-2xl sm:text-3xl font-heading font-black text-[#18211F] font-mono">
                ₹{kpis?.total_commissions?.toLocaleString() || 0}
              </div>
              <div className="text-[11px] text-[#063B32] mt-1 font-semibold">
                Direct: ₹{kpis?.direct_commissions?.toLocaleString() || 0} • Pair: ₹{(kpis?.pair_commissions || kpis?.matching_commissions || 0).toLocaleString()}
              </div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Financial Overview Chart */}
            <div className="rounded-3xl bg-[#FFFEF9] p-6 border border-[#E5E0D3] shadow-wealth-card">
              <div className="text-xs font-heading font-bold uppercase tracking-wider text-[#18211F] mb-4 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-[#063B32]" />
                <span>Financial Flow Overview (₹ INR)</span>
              </div>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={financialBarData}>
                    <XAxis dataKey="name" stroke="#69736F" fontSize={11} />
                    <YAxis stroke="#69736F" fontSize={11} tickFormatter={(val) => `₹${val / 1000}k`} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#FFFEF9', borderColor: '#E5E0D3', borderRadius: '1rem', fontSize: '12px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                      formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, 'Amount']}
                    />
                    <Bar dataKey="amount" fill="#063B32" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Commission Distribution Chart */}
            <div className="rounded-3xl bg-[#FFFEF9] p-6 border border-[#E5E0D3] shadow-wealth-card">
              <div className="text-xs font-heading font-bold uppercase tracking-wider text-[#18211F] mb-4 flex items-center gap-2">
                <Coins className="w-4 h-4 text-[#C9A227]" />
                <span>Commission Distribution Ratio</span>
              </div>

              <div className="h-64 w-full flex items-center justify-center">
                {kpis?.total_commissions ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={commissionPieData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        paddingAngle={5}
                      >
                        {commissionPieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ backgroundColor: '#FFFEF9', borderColor: '#E5E0D3', borderRadius: '1rem', fontSize: '12px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, 'Earned']}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="text-xs text-[#69736F]">No commissions generated yet</div>
                )}
              </div>
              <div className="flex justify-center gap-6 text-xs mt-2">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-[#063B32]" />
                  <span className="text-[#69736F] font-medium">Direct Sponsor (10%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-[#C9A227]" />
                  <span className="text-[#69736F] font-medium">Binary Matching (₹10k/Pair)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Audit Log Stream */}
          <div className="rounded-3xl bg-[#FFFEF9] p-6 border border-[#E5E0D3] shadow-wealth-card">
            <div className="text-xs font-heading font-bold uppercase tracking-wider text-[#18211F] mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#063B32]" />
              <span>Real-time System Audit Stream</span>
            </div>

            <div className="space-y-2.5">
              {data?.recent_logs && data.recent_logs.length > 0 ? (
                data.recent_logs.map((log: any) => (
                  <div
                    key={log.id}
                    className="p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] font-mono font-bold bg-[#FAF4DC] text-[#8C6C16] border border-[#E2C766]/60 px-2.5 py-0.5 rounded-lg">
                        {log.action}
                      </span>
                      <span className="text-[#18211F]">
                        By: <strong className="text-[#063B32]">{log.user_name}</strong> • Target: {log.entity_type} {log.entity_id || ''}
                      </span>
                    </div>
                    <div className="text-[#69736F] font-mono text-[11px]">
                      {new Date(log.created_at).toLocaleTimeString()}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-xs text-[#69736F]">No system events logged yet.</div>
              )}
            </div>
          </div>
        </>
      )}

      {/* 1. Commissions Audit Table */}
      {adminTab === 'commissions' && (
        <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E5E0D3] pb-4">
            <div>
              <h2 className="text-lg font-heading font-extrabold text-[#18211F]">Network Commissions Audit Log</h2>
              <p className="text-xs text-[#69736F]">
                Real-time lineage of all Direct Sponsor, Pair Bonus (₹10k), Matching Upline, and Carry Commission events.
              </p>
            </div>
            <span className="text-xs font-mono bg-[#F7F4EC] px-3 py-1.5 rounded-xl border border-[#E5E0D3] font-bold text-[#063B32] self-start sm:self-auto">
              {commissionsData?.total || 0} Total Records
            </span>
          </div>

          {/* Filter Bar */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
              {[
                { label: 'All Commissions', value: '' },
                { label: '🟢 Direct Sponsor', value: 'DIRECT_COMMISSION' },
                { label: '🟣 Pair Bonus (₹10k)', value: 'PAIR_BONUS' },
                { label: '🟠 Matching Upline', value: 'MATCHING_COMMISSION' },
                { label: '🔵 Carry Commission', value: 'CARRY_COMMISSION' },
              ].map((tab) => (
                <button
                  key={tab.value}
                  onClick={() => setCommTypeFilter(tab.value)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                    commTypeFilter === tab.value
                      ? 'bg-[#063B32] text-[#FFFEF9] font-bold shadow-xs'
                      : 'text-[#69736F] hover:text-[#18211F] hover:bg-[#F7F4EC]'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <div className="relative min-w-[220px]">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[#69736F]" />
              <input
                type="text"
                placeholder="Search member name or code..."
                value={commSearch}
                onChange={(e) => setCommSearch(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-[#F7F4EC] border border-[#E5E0D3] text-xs text-[#18211F] placeholder-[#69736F] focus:outline-none focus:border-[#063B32]"
              />
            </div>
          </div>

          {commissionsData?.items && commissionsData.items.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#E5E0D3] bg-[#F7F4EC]/60 text-[#69736F] font-mono text-[10px] uppercase">
                    <th className="py-3 px-3">Commission ID</th>
                    <th className="py-3 px-3">Type</th>
                    <th className="py-3 px-3">Beneficiary Member</th>
                    <th className="py-3 px-3">Triggered By</th>
                    <th className="py-3 px-3">Slot ID</th>
                    <th className="py-3 px-3 text-right">BV Basis</th>
                    <th className="py-3 px-3 text-right">Commission Amount</th>
                    <th className="py-3 px-3 text-right">Created At</th>
                    <th className="py-3 px-3 text-center">Audit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#EFECE2] font-mono">
                  {commissionsData.items.map((comm) => (
                    <tr key={comm.id} className="hover:bg-[#F7F4EC]/50 transition-colors">
                      <td className="py-3 px-3 font-bold text-[#18211F]">
                        {comm.commission_code || `#${comm.id}`}
                      </td>
                      <td className="py-3 px-3">
                        <span className={`text-[10px] px-2.5 py-0.5 rounded font-sans font-bold border ${
                          comm.commission_type === 'PAIR_BONUS'
                            ? 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766]'
                            : comm.commission_type === 'DIRECT_REFERRAL' || comm.commission_type === 'DIRECT_COMMISSION'
                            ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
                            : comm.commission_type === 'MATCHING_COMMISSION' || comm.commission_type === 'BINARY_MATCHING'
                            ? 'bg-[#FFEDD5] text-[#C2410C] border-[#FDBA74]'
                            : 'bg-[#DBEAFE] text-[#1D4ED8] border-[#93C5FD]'
                        }`}>
                          {comm.commission_type === 'PAIR_BONUS'
                            ? '🟣 Pair Bonus (₹10k)'
                            : comm.commission_type === 'DIRECT_REFERRAL' || comm.commission_type === 'DIRECT_COMMISSION'
                            ? '🟢 Direct Sponsor'
                            : comm.commission_type === 'MATCHING_COMMISSION' || comm.commission_type === 'BINARY_MATCHING'
                            ? '🟠 Matching Upline'
                            : '🔵 Carry Commission'}
                        </span>
                      </td>
                      <td className="py-3 px-3 font-sans">
                        <div className="font-bold text-[#063B32]">{comm.beneficiary_name || `Member #${comm.beneficiary_id}`}</div>
                      </td>
                      <td className="py-3 px-3 font-sans">
                        <div className="font-medium text-[#18211F]">
                          {comm.source_user_name || 'System / Network'}
                          {comm.source_user_code && <span className="text-[#69736F] font-mono ml-1">({comm.source_user_code})</span>}
                        </div>
                      </td>
                      <td className="py-3 px-3 font-bold text-[#18211F]">{comm.slot_id}</td>
                      <td className="py-3 px-3 text-right text-[#18211F]">
                        {comm.bv_basis ? `₹${comm.bv_basis.toLocaleString()}` : `${comm.bv_amount.toLocaleString()} BV`}
                      </td>
                      <td className="py-3 px-3 text-right font-bold text-[#063B32]">
                        +₹{comm.amount.toLocaleString()}
                      </td>
                      <td className="py-3 px-3 text-right text-[#69736F] text-[11px]">
                        {new Date(comm.created_at).toLocaleString()}
                      </td>
                      <td className="py-3 px-3 text-center">
                        <button
                          onClick={() => setSelectedCommission(comm)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#F7F4EC] hover:bg-[#063B32] hover:text-[#FFFEF9] text-[#18211F] text-[11px] font-sans font-bold transition-all border border-[#E5E0D3] cursor-pointer"
                        >
                          <HelpCircle className="w-3.5 h-3.5 text-[#C9A227]" />
                          <span>Audit</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-12 text-center text-xs text-[#69736F]">No commission records match the filter.</div>
          )}
        </div>
      )}

      {/* 2. Slot Settlements Table */}
      {adminTab === 'settlements' && (
        <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-heading font-extrabold text-[#18211F]">Slot Settlement Records (All Users)</h2>
              <p className="text-xs text-[#69736F]">
                Audit matching calculations, pair payouts (₹10,000 max 1/slot), matching upline earnings, and side-specific carry forwards.
              </p>
            </div>
            <span className="text-xs font-mono bg-[#F7F4EC] px-3 py-1.5 rounded-xl border border-[#E5E0D3] font-bold text-[#063B32]">
              {settlementsData?.total || 0} Total Settlements
            </span>
          </div>

          {settlementsData?.items && settlementsData.items.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#E5E0D3] bg-[#F7F4EC]/60 text-[#69736F] font-mono text-[10px] uppercase">
                    <th className="py-3 px-3">Member</th>
                    <th className="py-3 px-3">Slot ID</th>
                    <th className="py-3 px-3">Opening L/R</th>
                    <th className="py-3 px-3">Matched L/R</th>
                    <th className="py-3 px-3 text-[#C9A227]">Pair Bonus</th>
                    <th className="py-3 px-3 text-[#EA580C]">Matching Comm.</th>
                    <th className="py-3 px-3 text-[#063B32]">Ending Carry L/R</th>
                    <th className="py-3 px-3 text-[#3B82F6]">Carry Comm.</th>
                    <th className="py-3 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#EFECE2] font-mono">
                  {settlementsData.items.map((s) => (
                    <tr key={s.id} className="hover:bg-[#F7F4EC]/50 transition-colors">
                      <td className="py-3 px-3 font-sans">
                        <div className="font-bold text-[#18211F]">{s.user_name || `User #${s.user_id}`}</div>
                        <div className="text-[10px] text-[#063B32] font-mono font-bold">{s.user_code}</div>
                      </td>
                      <td className="py-3 px-3 font-bold text-[#18211F]">{s.slot_id}</td>
                      <td className="py-3 px-3">
                        ₹{s.left_before?.toLocaleString()} / ₹{s.right_before?.toLocaleString()}
                      </td>
                      <td className="py-3 px-3 text-[#8C6C16] font-bold">
                        ₹{s.left_matched?.toLocaleString()} / ₹{s.right_matched?.toLocaleString()}
                      </td>
                      <td className="py-3 px-3 font-bold text-[#C9A227]">
                        {s.pair_bonus > 0 ? `₹${s.pair_bonus?.toLocaleString()}` : '—'}
                      </td>
                      <td className="py-3 px-3 font-bold text-[#EA580C]">
                        {s.matching_commission > 0 ? `₹${s.matching_commission?.toLocaleString()}` : '—'}
                      </td>
                      <td className="py-3 px-3 font-bold text-[#063B32]">
                        ₹{s.left_carry?.toLocaleString()} / ₹{s.right_carry?.toLocaleString()}
                      </td>
                      <td className="py-3 px-3 text-[#3B82F6] font-medium">
                        {s.carry_commission > 0 ? `₹${s.carry_commission?.toLocaleString()}` : '—'}
                      </td>
                      <td className="py-3 px-3 font-sans">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#E0F3EE] text-[#063B32] border border-[#8DCFBF]">
                          {s.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-12 text-center text-xs text-[#69736F]">No settlement records found.</div>
          )}
        </div>
      )}

      {/* 3. Volume Ledger Table */}
      {adminTab === 'volume_ledger' && (
        <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-heading font-extrabold text-[#18211F]">Volume Ledger (Immutable BV Lineage)</h2>
              <p className="text-xs text-[#69736F]">
                Traceable origin of every business volume event and its ancestor leg representations.
              </p>
            </div>
            <span className="text-xs font-mono bg-[#F7F4EC] px-3 py-1.5 rounded-xl border border-[#E5E0D3] font-bold text-[#063B32]">
              {volumeLedgerData?.total || 0} Total Entries
            </span>
          </div>

          {volumeLedgerData?.items && volumeLedgerData.items.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#E5E0D3] bg-[#F7F4EC]/60 text-[#69736F] font-mono text-[10px] uppercase">
                    <th className="py-3 px-3">ID</th>
                    <th className="py-3 px-3">Source Member</th>
                    <th className="py-3 px-3">Ancestor Member</th>
                    <th className="py-3 px-3">Side</th>
                    <th className="py-3 px-3">Slot ID</th>
                    <th className="py-3 px-3">Amount</th>
                    <th className="py-3 px-3">Consumed</th>
                    <th className="py-3 px-3">Remaining</th>
                    <th className="py-3 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#EFECE2] font-mono">
                  {volumeLedgerData.items.map((v) => (
                    <tr key={v.id} className="hover:bg-[#F7F4EC]/50 transition-colors">
                      <td className="py-3 px-3 font-bold text-[#69736F]">#{v.id}</td>
                      <td className="py-3 px-3 font-sans">
                        <div className="font-bold text-[#18211F]">{v.source_user_name || `User #${v.source_user_id}`}</div>
                        <div className="text-[10px] text-[#69736F] font-mono">{v.source_user_code}</div>
                      </td>
                      <td className="py-3 px-3 font-sans">
                        <div className="font-bold text-[#063B32]">{v.ancestor_user_name || `User #${v.ancestor_user_id}`}</div>
                        <div className="text-[10px] text-[#69736F] font-mono">{v.ancestor_user_code}</div>
                      </td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          v.side === 'LEFT' ? 'bg-[#E0F3EE] text-[#063B32]' : 'bg-[#FAF4DC] text-[#8C6C16]'
                        }`}>
                          {v.side}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-[#18211F]">{v.slot_id}</td>
                      <td className="py-3 px-3 font-bold text-[#18211F]">₹{v.amount?.toLocaleString()}</td>
                      <td className="py-3 px-3 text-[#8C6C16]">₹{v.consumed_amount?.toLocaleString()}</td>
                      <td className="py-3 px-3 font-bold text-[#063B32]">₹{v.remaining_amount?.toLocaleString()}</td>
                      <td className="py-3 px-3 font-sans">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                          v.status === 'CONSUMED' 
                            ? 'bg-[#F7F4EC] text-[#69736F] border-[#E5E0D3]' 
                            : 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
                        }`}>
                          {v.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-12 text-center text-xs text-[#69736F]">No volume ledger records found.</div>
          )}
        </div>
      )}

      {/* Commission Audit Modal */}
      <CommissionDetailModal
        commission={selectedCommission}
        onClose={() => setSelectedCommission(null)}
      />
    </div>
  );
};

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import { AdminDashboardData } from '../../types';
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
  GitFork
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell } from 'recharts';

export const AdminDashboardPage: React.FC = () => {
  const { data, isLoading } = useQuery<AdminDashboardData>({
    queryKey: ['adminDashboard'],
    queryFn: async () => {
      const res = await api.get('/admin/dashboard');
      return res.data.data;
    },
    refetchInterval: 10000,
  });

  const kpis = data?.kpis;

  const commissionPieData = [
    { name: 'Direct Referral (10%)', value: kpis?.direct_commissions || 0, color: '#10b981' },
    { name: 'Binary Matching (10%)', value: kpis?.matching_commissions || 0, color: '#3b82f6' },
  ];

  const financialBarData = [
    { name: 'Virtual Sales', amount: kpis?.total_virtual_sales || 0 },
    { name: 'Total Volume', amount: kpis?.total_bv || 0 },
    { name: 'Commissions', amount: kpis?.total_commissions || 0 },
    { name: 'Withdrawn', amount: kpis?.total_withdrawn || 0 },
  ];

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-28 rounded-2xl bg-slate-800/40" />
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 rounded-2xl bg-slate-800/40" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400 mb-1">
          <ShieldAlert className="w-4 h-4" />
          <span>Superuser Control Center</span>
        </div>
        <h1 className="text-2xl font-black text-white">System Analytics & Platform KPIs</h1>
        <p className="text-xs text-slate-400">
          Global financial health, MLM distribution metrics, and live audit event log.
        </p>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Users */}
        <div className="rounded-3xl glass-panel p-5 border border-slate-800 relative glass-panel-hover">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Members</span>
            <Users className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {kpis?.total_users || 0}
          </div>
          <div className="text-[11px] text-emerald-400 mt-1 font-medium">
            {kpis?.active_users || 0} Active • {kpis?.inactive_users || 0} Inactive
          </div>
        </div>

        {/* Total Virtual Sales */}
        <div className="rounded-3xl glass-panel p-5 border border-slate-800 relative glass-panel-hover">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Virtual Sales</span>
            <ShoppingBag className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-emerald-400 font-mono">
            ₹{kpis?.total_virtual_sales?.toLocaleString() || 0}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Total demo revenue generated</div>
        </div>

        {/* Total Commissions Paid */}
        <div className="rounded-3xl glass-panel p-5 border border-slate-800 relative glass-panel-hover">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Commissions Paid</span>
            <Coins className="w-4 h-4 text-brand-400" />
          </div>
          <div className="text-2xl font-black text-brand-400 font-mono">
            ₹{kpis?.total_commissions?.toLocaleString() || 0}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 font-mono">
            Direct: ₹{kpis?.direct_commissions?.toLocaleString()} • Binary: ₹{kpis?.matching_commissions?.toLocaleString()}
          </div>
        </div>

        {/* Pending Withdrawals */}
        <div className="rounded-3xl glass-panel p-5 border border-slate-800 relative glass-panel-hover">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Pending Payouts</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-amber-400 font-mono">
            {kpis?.pending_withdrawals_count || 0}
          </div>
          <div className="text-[11px] text-amber-300/80 mt-1 font-mono">
            ₹{kpis?.pending_withdrawals_amount?.toLocaleString() || 0} awaiting approval
          </div>
        </div>
      </div>

      {/* Visual Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Financial Flow Bar Chart */}
        <div className="rounded-3xl glass-panel p-6 border border-slate-800">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-amber-400" />
            <span>Virtual Financial Overview (₹)</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={financialBarData} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                  formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, 'Amount']}
                />
                <Bar dataKey="amount" fill="#10b981" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Commission Distribution Chart */}
        <div className="rounded-3xl glass-panel p-6 border border-slate-800">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-4 flex items-center gap-2">
            <Coins className="w-4 h-4 text-emerald-400" />
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
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                    formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, 'Earned']}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-slate-500">No commissions generated yet</div>
            )}
          </div>
          <div className="flex justify-center gap-6 text-xs mt-2">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-emerald-500" />
              <span className="text-slate-300">Direct Sponsor (10%)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-blue-500" />
              <span className="text-slate-300">Binary Matching (10%)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Audit Log Stream */}
      <div className="rounded-3xl glass-panel p-6 border border-slate-800">
        <div className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4 text-amber-400" />
          <span>Real-time System Audit Stream</span>
        </div>

        <div className="space-y-2.5">
          {data?.recent_logs && data.recent_logs.length > 0 ? (
            data.recent_logs.map((log: any) => (
              <div
                key={log.id}
                className="p-3 rounded-2xl bg-navy-900/60 border border-slate-800/80 flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-3">
                  <span className="text-[10px] font-mono font-bold bg-slate-800 text-amber-300 px-2 py-0.5 rounded">
                    {log.action}
                  </span>
                  <span className="text-slate-200">
                    By: <strong className="text-white">{log.user_name}</strong> • Target: {log.entity_type} {log.entity_id || ''}
                  </span>
                </div>
                <div className="text-slate-400 font-mono text-[11px]">
                  {new Date(log.created_at).toLocaleTimeString()}
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-6 text-xs text-slate-500">No system events logged yet.</div>
          )}
        </div>
      </div>
    </div>
  );
};

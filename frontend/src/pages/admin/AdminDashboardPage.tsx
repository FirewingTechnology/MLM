import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useToast } from '../../context/ToastContext';
import { 
  AdminDashboardData, 
  SlotSettlement, 
  VolumeLedgerEntry, 
  Commission, 
  PackageActivationRequest, 
  SecurityPin,
  SecurityPinOrder,
  SecurityPinTransfer,
  SecurityPinLedgerItem
} from '../../types';
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
  Sparkles,
  KeyRound,
  ShieldCheck,
  Check,
  Copy,
  AlertCircle,
  Loader2,
  X,
  UserCheck,
  ArrowUpRight,
  Package,
  Send,
  History,
  FileText
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell } from 'recharts';

export const AdminDashboardPage: React.FC = () => {
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const [adminTab, setAdminTab] = useState<'analytics' | 'activations' | 'commissions' | 'settlements' | 'volume_ledger'>('analytics');
  const [selectedCommission, setSelectedCommission] = useState<Commission | null>(null);
  
  // Commission filters
  const [commTypeFilter, setCommTypeFilter] = useState<string>('');
  const [commSearch, setCommSearch] = useState<string>('');

  // Security PIN & Activation Sub-Tabs
  const [pinSubTab, setPinSubTab] = useState<'orders' | 'requests' | 'inventory' | 'transfers' | 'ledger'>('orders');

  // Activation Request filters
  const [activationStatusFilter, setActivationStatusFilter] = useState<string>('ALL');
  const [activationSearch, setActivationSearch] = useState<string>('');
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);

  // Bulk Orders filter
  const [pinOrderStatusFilter, setPinOrderStatusFilter] = useState<string>('ALL');

  // One-time Single PIN Display modal state
  const [generatedPinModal, setGeneratedPinModal] = useState<{
    pin: any;
    raw_security_pin: string;
    request?: PackageActivationRequest;
  } | null>(null);

  // Batch PINs Display modal state (For Bulk Orders)
  const [batchGeneratedPinsModal, setBatchGeneratedPinsModal] = useState<{
    order: SecurityPinOrder;
    pins: any[];
    raw_pins: string[];
  } | null>(null);

  const [copiedPin, setCopiedPin] = useState(false);
  const [copiedBatch, setCopiedBatch] = useState(false);

  // Reject Modal State
  const [rejectingReq, setRejectingReq] = useState<PackageActivationRequest | null>(null);
  const [rejectingPinOrder, setRejectingPinOrder] = useState<SecurityPinOrder | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [rejectLoading, setRejectLoading] = useState(false);

  const { data, isLoading } = useQuery<AdminDashboardData>({
    queryKey: ['adminDashboard'],
    queryFn: async () => {
      const res = await api.get('/admin/dashboard');
      return res.data.data;
    },
    refetchInterval: 10000,
  });

  const { data: activationData, isLoading: loadingActivations } = useQuery<{ items: PackageActivationRequest[]; total: number }>({
    queryKey: ['adminActivationRequests', activationStatusFilter, activationSearch],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append('per_page', '50');
      if (activationStatusFilter && activationStatusFilter !== 'ALL') {
        params.append('status', activationStatusFilter);
      }
      if (activationSearch) {
        params.append('search', activationSearch);
      }
      const res = await api.get(`/admin/activation-requests?${params.toString()}`);
      return res.data.data || { items: [], total: 0 };
    },
    enabled: adminTab === 'activations',
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

  // 1. Bulk PIN Orders Query
  const { data: pinOrdersData, isLoading: loadingPinOrders } = useQuery<{ items: SecurityPinOrder[]; total: number }>({
    queryKey: ['adminPinOrders', pinOrderStatusFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append('per_page', '50');
      if (pinOrderStatusFilter && pinOrderStatusFilter !== 'ALL') {
        params.append('status', pinOrderStatusFilter);
      }
      const res = await api.get(`/admin/security-pins/orders?${params.toString()}`);
      return res.data.data || { items: [], total: 0 };
    },
    enabled: adminTab === 'activations' && pinSubTab === 'orders',
    refetchInterval: 8000,
  });

  // 2. Master PINs Inventory Query
  const { data: masterPinsData, isLoading: loadingMasterPins } = useQuery<{ items: SecurityPin[]; total: number }>({
    queryKey: ['adminMasterPins'],
    queryFn: async () => {
      const res = await api.get('/admin/security-pins?per_page=50');
      return res.data.data || { items: [], total: 0 };
    },
    enabled: adminTab === 'activations' && pinSubTab === 'inventory',
    refetchInterval: 10000,
  });

  // 3. Transfers Audit Query
  const { data: pinTransfersData, isLoading: loadingPinTransfers } = useQuery<{ items: SecurityPinTransfer[]; total: number }>({
    queryKey: ['adminPinTransfers'],
    queryFn: async () => {
      const res = await api.get('/admin/security-pins/transfers?per_page=50');
      return res.data.data || { items: [], total: 0 };
    },
    enabled: adminTab === 'activations' && pinSubTab === 'transfers',
    refetchInterval: 10000,
  });

  // 4. Master Ledger Query
  const { data: pinLedgerData, isLoading: loadingPinLedger } = useQuery<{ items: SecurityPinLedgerItem[]; total: number }>({
    queryKey: ['adminPinLedger'],
    queryFn: async () => {
      const res = await api.get('/admin/security-pins/ledger?per_page=50');
      return res.data.data || { items: [], total: 0 };
    },
    enabled: adminTab === 'activations' && pinSubTab === 'ledger',
    refetchInterval: 10000,
  });

  const kpis = data?.kpis;

  // Bulk PIN Order Handlers
  const handleVerifyPinOrder = async (order: SecurityPinOrder) => {
    setActionLoadingId(order.id);
    try {
      const res = await api.post(`/admin/security-pins/orders/${order.id}/verify`, {
        notes: `Verified by Admin at ${new Date().toISOString()}`
      });
      if (res.data?.success) {
        showToast(`Payment verified for PIN Order ${order.order_code}! You can now issue ${order.quantity} PINs.`, 'success');
        queryClient.invalidateQueries({ queryKey: ['adminPinOrders'] });
        queryClient.invalidateQueries({ queryKey: ['adminDashboard'] });
      }
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Could not verify payment.';
      showToast(msg, 'error');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleIssuePinOrderBatch = async (order: SecurityPinOrder) => {
    setActionLoadingId(order.id);
    try {
      const res = await api.post(`/admin/security-pins/orders/${order.id}/issue`, {
        expires_in_days: 30
      });
      if (res.data?.success) {
        const batchData = res.data.data;
        setBatchGeneratedPinsModal({
          order,
          pins: batchData.pins || [],
          raw_pins: batchData.raw_security_pins || []
        });
        showToast(`Successfully generated ${order.quantity} Security PINs for ${order.buyer_name || order.buyer_code}!`, 'success');
        queryClient.invalidateQueries({ queryKey: ['adminPinOrders'] });
        queryClient.invalidateQueries({ queryKey: ['adminMasterPins'] });
        queryClient.invalidateQueries({ queryKey: ['adminDashboard'] });
      }
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Could not issue Security PINs batch.';
      showToast(msg, 'error');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleRejectPinOrderSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectingPinOrder || !rejectReason.trim()) return;

    setRejectLoading(true);
    try {
      const res = await api.post(`/admin/security-pins/orders/${rejectingPinOrder.id}/reject`, {
        reason: rejectReason.trim()
      });
      if (res.data?.success) {
        showToast(`PIN Order ${rejectingPinOrder.order_code} rejected.`, 'info');
        setRejectingPinOrder(null);
        setRejectReason('');
        queryClient.invalidateQueries({ queryKey: ['adminPinOrders'] });
        queryClient.invalidateQueries({ queryKey: ['adminDashboard'] });
      }
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Could not reject PIN Order.';
      showToast(msg, 'error');
    } finally {
      setRejectLoading(false);
    }
  };

  const handleVerifyPayment = async (req: PackageActivationRequest) => {
    setActionLoadingId(req.id);
    try {
      const res = await api.post(`/admin/activation-requests/${req.id}/verify-payment`, {
        admin_notes: `Verified by Admin at ${new Date().toISOString()}`
      });
      if (res.data?.success) {
        showToast(`Payment verified for request ${req.request_code}! You can now issue a Security PIN.`, 'success');
        queryClient.invalidateQueries({ queryKey: ['adminActivationRequests'] });
        queryClient.invalidateQueries({ queryKey: ['adminDashboard'] });
      }
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Could not verify payment.';
      showToast(msg, 'error');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleIssuePin = async (req: PackageActivationRequest) => {
    setActionLoadingId(req.id);
    try {
      const res = await api.post(`/admin/activation-requests/${req.id}/issue-pin`, {
        expires_in_days: 7
      });
      if (res.data?.success) {
        const rawPin = res.data.data.raw_security_pin;
        setGeneratedPinModal({
          pin: res.data.data.pin,
          raw_security_pin: rawPin,
          request: req
        });
        showToast(`Security PIN generated for ${req.user_name || req.user_code}!`, 'success');
        queryClient.invalidateQueries({ queryKey: ['adminActivationRequests'] });
        queryClient.invalidateQueries({ queryKey: ['adminDashboard'] });
      }
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Could not generate Security PIN.';
      showToast(msg, 'error');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleConfirmReject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectingReq || !rejectReason.trim()) return;

    setRejectLoading(true);
    try {
      const res = await api.post(`/admin/activation-requests/${rejectingReq.id}/reject`, {
        reason: rejectReason.trim()
      });
      if (res.data?.success) {
        showToast(`Activation request ${rejectingReq.request_code} rejected.`, 'info');
        setRejectingReq(null);
        setRejectReason('');
        queryClient.invalidateQueries({ queryKey: ['adminActivationRequests'] });
        queryClient.invalidateQueries({ queryKey: ['adminDashboard'] });
      }
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Could not reject request.';
      showToast(msg, 'error');
    } finally {
      setRejectLoading(false);
    }
  };

  const handleRevokePin = async (pinId: number) => {
    if (!window.confirm('Are you sure you want to revoke this Security PIN? It will immediately become unusable.')) {
      return;
    }

    try {
      const res = await api.post(`/admin/security-pins/${pinId}/revoke`, {
        reason: 'Administrative revocation'
      });
      if (res.data?.success) {
        showToast('Security PIN revoked successfully.', 'info');
        queryClient.invalidateQueries({ queryKey: ['adminActivationRequests'] });
        queryClient.invalidateQueries({ queryKey: ['adminDashboard'] });
      }
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Could not revoke PIN.';
      showToast(msg, 'error');
    }
  };

  const handleCopyPin = (pinValue: string) => {
    navigator.clipboard.writeText(pinValue);
    setCopiedPin(true);
    showToast('Security PIN copied to clipboard!', 'success');
    setTimeout(() => setCopiedPin(false), 2500);
  };

  const commissionPieData = [
    { name: 'Direct Sponsor (10%)', value: kpis?.direct_commissions || 0, color: '#063B32' },
    { name: 'Pair Bonus (₹10k)', value: kpis?.pair_commissions || 0, color: '#C9A227' },
    { name: 'Matching Upline', value: kpis?.matching_commissions || 0, color: '#EA580C' },
    { name: 'Carry Commission', value: kpis?.carry_commissions || 0, color: '#3B82F6' },
  ].filter(d => d.value > 0);

  const financialBarData = [
    { name: 'Total Sales', amount: kpis?.total_virtual_sales || 0 },
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
            <div key={i} className="h-32 rounded-3xl bg-[#E5E0D3]/60" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-[#C9A227] mb-1">
            <ShieldAlert className="w-4 h-4 text-[#063B32]" />
            <span>Master Administration Portal</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-[#18211F] tracking-tight">
            Financial & Network Command Center
          </h1>
          <p className="text-xs sm:text-sm text-[#69736F] font-medium">
            Monitor real-time MLM commissions, verify member package payments, and issue single-use Security PINs.
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center gap-1.5 bg-[#F7F4EC] p-1.5 rounded-2xl border border-[#E5E0D3] self-start sm:self-auto flex-wrap">
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
            onClick={() => setAdminTab('activations')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer relative ${
              adminTab === 'activations'
                ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs'
                : 'text-[#69736F] hover:text-[#18211F]'
            }`}
          >
            <KeyRound className="w-3.5 h-3.5 text-[#C9A227]" />
            <span>Security PIN & Activations</span>
            {(kpis as any)?.pending_activations_count > 0 && (
              <span className="w-2 h-2 rounded-full bg-[#EA580C] animate-ping" />
            )}
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
            <span>Income Audit</span>
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

      {/* TAB: OVERVIEW */}
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
              <div className="text-[11px] text-[#063B32] font-semibold mt-1">
                Active: {kpis?.active_users || 0} • Inactive: {kpis?.inactive_users || 0}
              </div>
            </div>

            {/* Total Virtual Sales */}
            <div className="rounded-3xl bg-[#FFFEF9] p-5 border border-[#E5E0D3] shadow-wealth-card">
              <div className="flex items-center justify-between text-[#69736F] mb-2">
                <span className="text-xs font-mono font-bold uppercase tracking-wider">Package Sales</span>
                <ShoppingBag className="w-4 h-4 text-[#0E9F6E]" />
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
                        outerRadius={80}
                        innerRadius={50}
                        paddingAngle={5}
                      >
                        {commissionPieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ backgroundColor: '#FFFEF9', borderColor: '#E5E0D3', borderRadius: '1rem', fontSize: '12px' }}
                        formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, 'Commission']}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="text-center text-xs text-[#69736F]">No commissions generated yet.</div>
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

      {/* TAB: SECURITY PIN & PACKAGE ACTIVATIONS */}
      {adminTab === 'activations' && (
        <div className="space-y-5">
          {/* Top KPI Cards for Activations */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
              <div className="flex items-center justify-between text-[#69736F] mb-1">
                <span className="text-[10px] font-bold uppercase tracking-wider">Pending Review</span>
                <Clock className="w-4 h-4 text-[#EA580C]" />
              </div>
              <div className="text-2xl font-heading font-black text-[#EA580C] font-mono">
                {(kpis as any)?.pending_activations_count || 0}
              </div>
              <div className="text-[10px] text-[#69736F] mt-1">Awaiting Payment Verification</div>
            </div>

            <div className="p-4 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
              <div className="flex items-center justify-between text-[#69736F] mb-1">
                <span className="text-[10px] font-bold uppercase tracking-wider">Payment Verified</span>
                <ShieldCheck className="w-4 h-4 text-[#0E9F6E]" />
              </div>
              <div className="text-2xl font-heading font-black text-[#0E9F6E] font-mono">
                {(kpis as any)?.verified_activations_count || 0}
              </div>
              <div className="text-[10px] text-[#69736F] mt-1">Ready for PIN Issuance</div>
            </div>

            <div className="p-4 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
              <div className="flex items-center justify-between text-[#69736F] mb-1">
                <span className="text-[10px] font-bold uppercase tracking-wider">Active PINs Issued</span>
                <KeyRound className="w-4 h-4 text-[#C9A227]" />
              </div>
              <div className="text-2xl font-heading font-black text-[#C9A227] font-mono">
                {(kpis as any)?.issued_pins_count || 0}
              </div>
              <div className="text-[10px] text-[#69736F] mt-1">Unused Member PINs</div>
            </div>

            <div className="p-4 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
              <div className="flex items-center justify-between text-[#69736F] mb-1">
                <span className="text-[10px] font-bold uppercase tracking-wider">Total Activated</span>
                <CheckCircle2 className="w-4 h-4 text-[#063B32]" />
              </div>
              <div className="text-2xl font-heading font-black text-[#063B32] font-mono">
                {(kpis as any)?.total_activated_count || 0}
              </div>
              <div className="text-[10px] text-[#69736F] mt-1">Packages Active & Credited</div>
            </div>
          </div>

          {/* Security PIN Sub-Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-[#E5E0D3] pb-2 overflow-x-auto">
            {[
              { id: 'orders', label: '📦 Bulk PIN Orders', icon: Package },
              { id: 'requests', label: '👤 Direct Activation Requests', icon: ShieldCheck },
              { id: 'inventory', label: '🔑 Master PIN Inventory', icon: KeyRound },
              { id: 'transfers', label: '🔄 Downline Transfers', icon: Send },
              { id: 'ledger', label: '📜 Master Audit Ledger', icon: History },
            ].map((st) => (
              <button
                key={st.id}
                onClick={() => setPinSubTab(st.id as any)}
                className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer ${
                  pinSubTab === st.id
                    ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs'
                    : 'bg-[#F7F4EC] text-[#69736F] hover:text-[#18211F] border border-[#E5E0D3]'
                }`}
              >
                <st.icon className="w-3.5 h-3.5" />
                <span>{st.label}</span>
              </button>
            ))}
          </div>

          {/* SUBTAB 1: BULK PIN ORDERS */}
          {pinSubTab === 'orders' && (
            <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E5E0D3] pb-4">
                <div>
                  <h2 className="text-lg font-heading font-extrabold text-[#18211F]">
                    Prepaid Security PIN Bulk Orders
                  </h2>
                  <p className="text-xs text-[#69736F]">
                    Review member payment references for bulk PIN requests, verify transactions, and issue batch activation PINs.
                  </p>
                </div>
                <span className="text-xs font-mono bg-[#F7F4EC] px-3 py-1.5 rounded-xl border border-[#E5E0D3] font-bold text-[#063B32]">
                  {pinOrdersData?.total || 0} Total Orders
                </span>
              </div>

              {/* Status Filter */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
                {[
                  { label: 'All Orders', value: 'ALL' },
                  { label: '🟠 Payment Submitted', value: 'PAYMENT_SUBMITTED' },
                  { label: '🟢 Payment Verified', value: 'PAYMENT_VERIFIED' },
                  { label: '🌲 Completed (PINs Issued)', value: 'COMPLETED' },
                  { label: '🔴 Rejected', value: 'REJECTED' },
                ].map((tab) => (
                  <button
                    key={tab.value}
                    onClick={() => setPinOrderStatusFilter(tab.value)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer ${
                      pinOrderStatusFilter === tab.value
                        ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs'
                        : 'bg-[#F7F4EC] text-[#69736F] hover:text-[#18211F] border border-[#E5E0D3]'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Table */}
              {loadingPinOrders ? (
                <div className="py-12 flex justify-center items-center gap-2 text-xs text-[#69736F]">
                  <Loader2 className="w-4 h-4 animate-spin text-[#C9A227]" />
                  <span>Loading bulk PIN orders...</span>
                </div>
              ) : pinOrdersData?.items && pinOrdersData.items.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-[#E5E0D3] text-[#69736F] font-mono uppercase text-[10px]">
                        <th className="py-3 px-3">Order Code / Date</th>
                        <th className="py-3 px-3">Buyer Member</th>
                        <th className="py-3 px-3">Quantity / Price</th>
                        <th className="py-3 px-3">Total Amount</th>
                        <th className="py-3 px-3">Payment Reference</th>
                        <th className="py-3 px-3">Status</th>
                        <th className="py-3 px-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E5E0D3]/60">
                      {pinOrdersData.items.map((order) => {
                        const isLoadingThis = actionLoadingId === order.id;
                        return (
                          <tr key={order.id} className="hover:bg-[#F7F4EC]/60 transition-colors">
                            <td className="py-3.5 px-3">
                              <div className="font-mono font-bold text-[#18211F]">{order.order_code}</div>
                              <div className="text-[10px] text-[#69736F]">
                                {new Date(order.created_at).toLocaleDateString()} {new Date(order.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </div>
                            </td>
                            <td className="py-3.5 px-3">
                              <div className="font-bold text-[#063B32]">{order.buyer_name || 'Member'}</div>
                              <div className="text-[10px] text-[#69736F] font-mono">{order.buyer_code}</div>
                              <div className="text-[10px] text-[#69736F]">{order.buyer_email}</div>
                            </td>
                            <td className="py-3.5 px-3 font-mono">
                              <div className="font-bold text-[#18211F]">{order.quantity} PIN(s)</div>
                              <div className="text-[10px] text-[#69736F]">₹{(order.price_per_pin || order.unit_price || 35000).toLocaleString()} / PIN</div>
                            </td>
                            <td className="py-3.5 px-3 font-mono">
                              <div className="font-black text-sm text-[#063B32]">
                                ₹{order.total_amount.toLocaleString()}
                              </div>
                            </td>
                            <td className="py-3.5 px-3 font-mono">
                              {order.payment_reference ? (
                                <div className="font-bold text-[#063B32] bg-white px-2 py-1 rounded border border-[#E5E0D3] w-fit">
                                  {order.payment_reference}
                                </div>
                              ) : (
                                <span className="text-[#69736F] italic">No reference</span>
                              )}
                              <div className="text-[10px] text-[#69736F] mt-0.5">{order.payment_method}</div>
                            </td>
                            <td className="py-3.5 px-3">
                              <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold border ${
                                order.status === 'COMPLETED'
                                  ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
                                  : order.status === 'PAYMENT_VERIFIED'
                                  ? 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766]'
                                  : order.status === 'REJECTED'
                                  ? 'bg-red-50 text-red-700 border-red-200'
                                  : 'bg-amber-50 text-amber-800 border-amber-200'
                              }`}>
                                <span className={`w-1.5 h-1.5 rounded-full ${
                                  order.status === 'COMPLETED' ? 'bg-[#0E9F6E]' : order.status === 'PAYMENT_VERIFIED' ? 'bg-[#C9A227]' : order.status === 'REJECTED' ? 'bg-red-600' : 'bg-amber-600'
                                }`} />
                                <span>{order.status.replace('_', ' ')}</span>
                              </span>
                            </td>
                            <td className="py-3.5 px-3 text-right">
                              <div className="flex items-center justify-end gap-1.5 flex-wrap">
                                {order.status === 'PAYMENT_SUBMITTED' && (
                                  <>
                                    <button
                                      onClick={() => handleVerifyPinOrder(order)}
                                      disabled={isLoadingThis}
                                      className="px-3 py-1.5 rounded-xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/30 text-xs font-bold transition-all shadow-xs cursor-pointer flex items-center gap-1"
                                    >
                                      {isLoadingThis ? <Loader2 className="w-3 h-3 animate-spin" /> : <ShieldCheck className="w-3 h-3 text-[#C9A227]" />}
                                      <span>Verify Payment</span>
                                    </button>
                                    <button
                                      onClick={() => setRejectingPinOrder(order)}
                                      className="px-2.5 py-1.5 rounded-xl border border-red-200 text-red-700 hover:bg-red-50 text-xs font-bold transition-colors cursor-pointer"
                                    >
                                      Reject
                                    </button>
                                  </>
                                )}

                                {order.status === 'PAYMENT_VERIFIED' && (
                                  <>
                                    <button
                                      onClick={() => handleIssuePinOrderBatch(order)}
                                      disabled={isLoadingThis}
                                      className="px-3 py-1.5 rounded-xl bg-[#C9A227] hover:bg-[#B38F1E] text-[#18211F] text-xs font-extrabold transition-all shadow-xs cursor-pointer flex items-center gap-1"
                                    >
                                      {isLoadingThis ? <Loader2 className="w-3 h-3 animate-spin" /> : <KeyRound className="w-3 h-3" />}
                                      <span>ISSUE {order.quantity} PINs</span>
                                    </button>
                                    <button
                                      onClick={() => setRejectingPinOrder(order)}
                                      className="px-2.5 py-1.5 rounded-xl border border-red-200 text-red-700 hover:bg-red-50 text-xs font-bold transition-colors cursor-pointer"
                                    >
                                      Reject
                                    </button>
                                  </>
                                )}

                                {order.status === 'COMPLETED' && (
                                  <span className="text-[11px] text-[#063B32] font-bold flex items-center gap-1">
                                    <CheckCircle2 className="w-4 h-4 text-[#0E9F6E]" />
                                    <span>{order.quantity} PINs Issued</span>
                                  </span>
                                )}

                                {order.status === 'REJECTED' && (
                                  <span className="text-[10px] text-red-600 italic">
                                    {order.rejection_reason || 'Rejected'}
                                  </span>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-12 text-center text-xs text-[#69736F]">
                  No bulk PIN purchase orders found.
                </div>
              )}
            </div>
          )}

          {/* SUBTAB 2: DIRECT ACTIVATION REQUESTS */}
          {pinSubTab === 'requests' && (
            <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E5E0D3] pb-4">
                <div>
                  <h2 className="text-lg font-heading font-extrabold text-[#18211F]">
                    Single User Package Activation Requests
                  </h2>
                  <p className="text-xs text-[#69736F]">
                    Verify direct single package payments and generate single-use Security PINs for individual members.
                  </p>
                </div>
                <span className="text-xs font-mono bg-[#F7F4EC] px-3 py-1.5 rounded-xl border border-[#E5E0D3] font-bold text-[#063B32]">
                  {activationData?.total || 0} Total Requests
                </span>
              </div>

              {/* Filter & Search Bar */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
                  {[
                    { label: 'All Requests', value: 'ALL' },
                    { label: '🟠 Pending Review', value: 'PAYMENT_SUBMITTED' },
                    { label: '🟢 Verified', value: 'PAYMENT_VERIFIED' },
                    { label: '🟡 PIN Issued', value: 'PIN_ISSUED' },
                    { label: '🌲 Activated', value: 'ACTIVATED' },
                    { label: '🔴 Rejected', value: 'REJECTED' },
                  ].map((tab) => (
                    <button
                      key={tab.value}
                      onClick={() => setActivationStatusFilter(tab.value)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer ${
                        activationStatusFilter === tab.value
                          ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs'
                          : 'bg-[#F7F4EC] text-[#69736F] hover:text-[#18211F] border border-[#E5E0D3]'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                <div className="relative w-full sm:w-64">
                  <Search className="w-4 h-4 text-[#69736F] absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Search user, code, ref..."
                    value={activationSearch}
                    onChange={(e) => setActivationSearch(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 bg-[#F7F4EC] border border-[#E5E0D3] rounded-xl text-xs text-[#18211F] placeholder:text-[#69736F] focus:outline-none focus:border-[#063B32]"
                  />
                </div>
              </div>

              {/* Table */}
              {loadingActivations ? (
                <div className="py-12 flex justify-center items-center gap-2 text-xs text-[#69736F]">
                  <Loader2 className="w-4 h-4 animate-spin text-[#C9A227]" />
                  <span>Loading activation requests...</span>
                </div>
              ) : activationData?.items && activationData.items.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-[#E5E0D3] text-[#69736F] font-mono uppercase text-[10px]">
                        <th className="py-3 px-3">Req Code / Date</th>
                        <th className="py-3 px-3">Member Details</th>
                        <th className="py-3 px-3">Sponsor / Parent</th>
                        <th className="py-3 px-3">Package / Amount</th>
                        <th className="py-3 px-3">Payment Ref</th>
                        <th className="py-3 px-3">Status</th>
                        <th className="py-3 px-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E5E0D3]/60">
                      {activationData.items.map((r) => {
                        const isLoadingThis = actionLoadingId === r.id;
                        return (
                          <tr key={r.id} className="hover:bg-[#F7F4EC]/60 transition-colors">
                            <td className="py-3.5 px-3">
                              <div className="font-mono font-bold text-[#18211F]">{r.request_code}</div>
                              <div className="text-[10px] text-[#69736F]">
                                {new Date(r.requested_at).toLocaleDateString()} {new Date(r.requested_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </div>
                            </td>
                            <td className="py-3.5 px-3 font-sans">
                              <div className="font-bold text-[#063B32]">{r.user_name || 'Member'}</div>
                              <div className="text-[10px] text-[#69736F] font-mono">{r.user_code}</div>
                              <div className="text-[10px] text-[#69736F]">{r.user_email}</div>
                            </td>
                            <td className="py-3.5 px-3 font-sans">
                              <div className="text-[#18211F] font-semibold">
                                Sponsor: <span className="text-[#063B32] font-bold">{r.sponsor_name || 'None'}</span>
                              </div>
                              <div className="text-[10px] text-[#69736F]">
                                Parent: {r.binary_parent_name || 'None'} ({r.binary_position || '-'})
                              </div>
                            </td>
                            <td className="py-3.5 px-3 font-mono">
                              <div className="font-bold text-[#18211F]">₹{r.package_amount.toLocaleString()}</div>
                              <div className="text-[10px] text-[#8C6C16] font-bold bg-[#FAF4DC] px-1.5 py-0.5 rounded w-fit mt-0.5">
                                {r.package_bv.toLocaleString()} BV
                              </div>
                            </td>
                            <td className="py-3.5 px-3 font-mono">
                              {r.payment_reference ? (
                                <div className="font-bold text-[#063B32] bg-white px-2 py-1 rounded border border-[#E5E0D3] w-fit">
                                  {r.payment_reference}
                                </div>
                              ) : (
                                <span className="text-[#69736F] italic">No reference</span>
                              )}
                              <div className="text-[10px] text-[#69736F] mt-0.5">{r.payment_method}</div>
                            </td>
                            <td className="py-3.5 px-3 font-sans">
                              <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold border ${
                                r.status === 'ACTIVATED'
                                  ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
                                  : r.status === 'PIN_ISSUED'
                                  ? 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766]'
                                  : r.status === 'PAYMENT_VERIFIED'
                                  ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
                                  : r.status === 'REJECTED'
                                  ? 'bg-red-50 text-red-700 border-red-200'
                                  : 'bg-amber-50 text-amber-800 border-amber-200'
                              }`}>
                                <span className={`w-1.5 h-1.5 rounded-full ${
                                  r.status === 'ACTIVATED' ? 'bg-[#0E9F6E]' : r.status === 'PIN_ISSUED' ? 'bg-[#C9A227]' : r.status === 'REJECTED' ? 'bg-red-600' : 'bg-amber-600'
                                }`} />
                                <span>{r.status.replace('_', ' ')}</span>
                              </span>
                            </td>
                            <td className="py-3.5 px-3 text-right">
                              <div className="flex items-center justify-end gap-1.5 flex-wrap">
                                {(r.status === 'PAYMENT_SUBMITTED' || r.status === 'UNDER_REVIEW' || r.status === 'PAYMENT_PENDING') && (
                                  <>
                                    <button
                                      onClick={() => handleVerifyPayment(r)}
                                      disabled={isLoadingThis}
                                      className="px-3 py-1.5 rounded-xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/30 text-xs font-bold transition-all shadow-xs cursor-pointer flex items-center gap-1"
                                    >
                                      {isLoadingThis ? <Loader2 className="w-3 h-3 animate-spin" /> : <ShieldCheck className="w-3 h-3 text-[#C9A227]" />}
                                      <span>Verify Payment</span>
                                    </button>
                                    <button
                                      onClick={() => setRejectingReq(r)}
                                      className="px-2.5 py-1.5 rounded-xl border border-red-200 text-red-700 hover:bg-red-50 text-xs font-bold transition-colors cursor-pointer"
                                    >
                                      Reject
                                    </button>
                                  </>
                                )}

                                {r.status === 'PAYMENT_VERIFIED' && (
                                  <>
                                    <button
                                      onClick={() => handleIssuePin(r)}
                                      disabled={isLoadingThis}
                                      className="px-3 py-1.5 rounded-xl bg-[#C9A227] hover:bg-[#B38F1E] text-[#18211F] text-xs font-extrabold transition-all shadow-xs cursor-pointer flex items-center gap-1"
                                    >
                                      {isLoadingThis ? <Loader2 className="w-3 h-3 animate-spin" /> : <KeyRound className="w-3 h-3" />}
                                      <span>ISSUE PIN</span>
                                    </button>
                                    <button
                                      onClick={() => setRejectingReq(r)}
                                      className="px-2.5 py-1.5 rounded-xl border border-red-200 text-red-700 hover:bg-red-50 text-xs font-bold transition-colors cursor-pointer"
                                    >
                                      Reject
                                    </button>
                                  </>
                                )}

                                {r.status === 'PIN_ISSUED' && (
                                  <div className="flex items-center gap-1.5">
                                    <button
                                      onClick={() => handleIssuePin(r)}
                                      disabled={isLoadingThis}
                                      className="px-2.5 py-1.5 rounded-xl border border-[#C9A227] bg-[#FAF4DC] text-[#8C6C16] hover:bg-[#F2E8C4] text-xs font-bold transition-colors cursor-pointer"
                                    >
                                      Re-issue PIN
                                    </button>
                                    {r.security_pin_id && (
                                      <button
                                        onClick={() => handleRevokePin(r.security_pin_id!)}
                                        className="px-2.5 py-1.5 rounded-xl border border-red-200 text-red-700 hover:bg-red-50 text-xs font-bold transition-colors cursor-pointer"
                                      >
                                        Revoke
                                      </button>
                                    )}
                                  </div>
                                )}

                                {r.status === 'ACTIVATED' && (
                                  <span className="text-[11px] text-[#063B32] font-bold flex items-center gap-1">
                                    <CheckCircle2 className="w-4 h-4 text-[#0E9F6E]" />
                                    <span>Activated</span>
                                  </span>
                                )}

                                {r.status === 'REJECTED' && (
                                  <span className="text-[10px] text-red-600 italic">
                                    {r.rejection_reason || 'Rejected by Admin'}
                                  </span>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-12 text-center text-xs text-[#69736F]">
                  No package activation requests found matching the selected filters.
                </div>
              )}
            </div>
          )}

          {/* SUBTAB 3: MASTER PIN INVENTORY */}
          {pinSubTab === 'inventory' && (
            <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card space-y-4">
              <div className="flex items-center justify-between border-b border-[#E5E0D3] pb-4">
                <div>
                  <h2 className="text-lg font-heading font-extrabold text-[#18211F]">Master Security PIN Inventory</h2>
                  <p className="text-xs text-[#69736F]">
                    All active, transferred, used, and revoked Security PINs with ownership lineage.
                  </p>
                </div>
                <span className="text-xs font-mono bg-[#F7F4EC] px-3 py-1.5 rounded-xl border border-[#E5E0D3] font-bold text-[#063B32]">
                  {masterPinsData?.total || 0} Master PINs
                </span>
              </div>

              {loadingMasterPins ? (
                <div className="py-12 flex justify-center items-center gap-2 text-xs text-[#69736F]">
                  <Loader2 className="w-4 h-4 animate-spin text-[#C9A227]" />
                  <span>Loading Master PINs...</span>
                </div>
              ) : masterPinsData?.items && masterPinsData.items.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse font-mono">
                    <thead>
                      <tr className="border-b border-[#E5E0D3] text-[#69736F] uppercase text-[10px]">
                        <th className="py-3 px-3">PIN Code</th>
                        <th className="py-3 px-3 font-sans">Current Owner</th>
                        <th className="py-3 px-3 font-sans">Original Buyer</th>
                        <th className="py-3 px-3">Status</th>
                        <th className="py-3 px-3">Amount / BV</th>
                        <th className="py-3 px-3">Issued Date</th>
                        <th className="py-3 px-3 text-right font-sans">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E5E0D3]/60">
                      {masterPinsData.items.map((p) => (
                        <tr key={p.id} className="hover:bg-[#F7F4EC]/60 transition-colors">
                          <td className="py-3 px-3 font-bold text-[#18211F]">{p.pin_code}</td>
                          <td className="py-3 px-3 font-sans">
                            <div className="font-bold text-[#063B32]">{p.owner_name || `User #${p.owner_user_id || p.user_id}`}</div>
                            <div className="text-[10px] text-[#69736F] font-mono">{p.owner_code}</div>
                          </td>
                          <td className="py-3 px-3 font-sans">
                            <div className="text-[#18211F]">{p.original_owner_name || 'Direct / Admin'}</div>
                            <div className="text-[10px] text-[#69736F] font-mono">{p.original_owner_code}</div>
                          </td>
                          <td className="py-3 px-3">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                              p.status === 'AVAILABLE' || p.status === 'ISSUED'
                                ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
                                : p.status === 'USED'
                                ? 'bg-[#F7F4EC] text-[#69736F] border-[#E5E0D3]'
                                : 'bg-red-50 text-red-700 border-red-200'
                            }`}>
                              {p.status}
                            </span>
                          </td>
                          <td className="py-3 px-3 font-bold text-[#18211F]">
                            ₹{p.amount?.toLocaleString()} <span className="text-[#8C6C16] text-[10px]">({p.bv?.toLocaleString()} BV)</span>
                          </td>
                          <td className="py-3 px-3 text-[#69736F]">
                            {new Date(p.created_at).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-3 text-right font-sans">
                            {p.status !== 'USED' && p.status !== 'REVOKED' && (
                              <button
                                onClick={() => handleRevokePin(p.id)}
                                className="px-2.5 py-1 rounded-xl border border-red-200 text-red-700 hover:bg-red-50 text-xs font-bold transition-colors cursor-pointer"
                              >
                                Revoke
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-12 text-center text-xs text-[#69736F]">No PINs found in master inventory.</div>
              )}
            </div>
          )}

          {/* SUBTAB 4: DOWNLINE TRANSFERS AUDIT */}
          {pinSubTab === 'transfers' && (
            <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card space-y-4">
              <div className="flex items-center justify-between border-b border-[#E5E0D3] pb-4">
                <div>
                  <h2 className="text-lg font-heading font-extrabold text-[#18211F]">PIN Transfers Audit Log</h2>
                  <p className="text-xs text-[#69736F]">
                    Auditable record of all Security PIN distributions from uplines to eligible downlines.
                  </p>
                </div>
                <span className="text-xs font-mono bg-[#F7F4EC] px-3 py-1.5 rounded-xl border border-[#E5E0D3] font-bold text-[#063B32]">
                  {pinTransfersData?.total || 0} Transfers
                </span>
              </div>

              {loadingPinTransfers ? (
                <div className="py-12 flex justify-center items-center gap-2 text-xs text-[#69736F]">
                  <Loader2 className="w-4 h-4 animate-spin text-[#C9A227]" />
                  <span>Loading transfers...</span>
                </div>
              ) : pinTransfersData?.items && pinTransfersData.items.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-[#E5E0D3] text-[#69736F] font-mono uppercase text-[10px]">
                        <th className="py-3 px-3">PIN Code</th>
                        <th className="py-3 px-3">From Upline</th>
                        <th className="py-3 px-3">To Downline</th>
                        <th className="py-3 px-3">Notes / Reason</th>
                        <th className="py-3 px-3">Transferred At</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E5E0D3]/60">
                      {pinTransfersData.items.map((t) => (
                        <tr key={t.id} className="hover:bg-[#F7F4EC]/60 transition-colors">
                          <td className="py-3 px-3 font-mono font-bold text-[#18211F]">{t.pin_code}</td>
                          <td className="py-3 px-3">
                            <div className="font-bold text-[#063B32]">{t.from_user_name}</div>
                            <div className="text-[10px] text-[#69736F] font-mono">{t.from_user_code}</div>
                          </td>
                          <td className="py-3 px-3">
                            <div className="font-bold text-[#8C6C16]">{t.to_user_name}</div>
                            <div className="text-[10px] text-[#69736F] font-mono">{t.to_user_code}</div>
                          </td>
                          <td className="py-3 px-3 text-[#69736F]">
                            {t.notes || 'Downline Distribution'}
                          </td>
                          <td className="py-3 px-3 font-mono text-[#69736F]">
                            {new Date(t.transferred_at).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-12 text-center text-xs text-[#69736F]">No PIN transfers recorded.</div>
              )}
            </div>
          )}

          {/* SUBTAB 5: MASTER AUDIT LEDGER */}
          {pinSubTab === 'ledger' && (
            <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card space-y-4">
              <div className="flex items-center justify-between border-b border-[#E5E0D3] pb-4">
                <div>
                  <h2 className="text-lg font-heading font-extrabold text-[#18211F]">Master Security PIN Audit Ledger</h2>
                  <p className="text-xs text-[#69736F]">
                    Append-only immutable record of all PIN creations, transfers, activations, and revocations.
                  </p>
                </div>
                <span className="text-xs font-mono bg-[#F7F4EC] px-3 py-1.5 rounded-xl border border-[#E5E0D3] font-bold text-[#063B32]">
                  {pinLedgerData?.total || 0} Ledger Entries
                </span>
              </div>

              {loadingPinLedger ? (
                <div className="py-12 flex justify-center items-center gap-2 text-xs text-[#69736F]">
                  <Loader2 className="w-4 h-4 animate-spin text-[#C9A227]" />
                  <span>Loading ledger...</span>
                </div>
              ) : pinLedgerData?.items && pinLedgerData.items.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse font-mono">
                    <thead>
                      <tr className="border-b border-[#E5E0D3] text-[#69736F] uppercase text-[10px]">
                        <th className="py-3 px-3 font-sans">Action</th>
                        <th className="py-3 px-3">PIN Code</th>
                        <th className="py-3 px-3 font-sans">Actor / Target</th>
                        <th className="py-3 px-3">Reference ID</th>
                        <th className="py-3 px-3 font-sans">Notes</th>
                        <th className="py-3 px-3">Timestamp</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E5E0D3]/60">
                      {pinLedgerData.items.map((l) => (
                        <tr key={l.id} className="hover:bg-[#F7F4EC]/60 transition-colors">
                          <td className="py-3 px-3 font-sans">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#FAF4DC] text-[#8C6C16] border border-[#E2C766]/60">
                              {l.action}
                            </span>
                          </td>
                          <td className="py-3 px-3 font-bold text-[#18211F]">{l.pin_code || `#${l.pin_id}`}</td>
                          <td className="py-3 px-3 font-sans">
                            <div className="font-bold text-[#063B32]">{l.user_name || `User #${l.user_id}`}</div>
                          </td>
                          <td className="py-3 px-3 text-[#69736F]">{l.reference_id || '-'}</td>
                          <td className="py-3 px-3 font-sans text-[#69736F]">{l.notes || '-'}</td>
                          <td className="py-3 px-3 text-[#69736F]">
                            {new Date(l.timestamp).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-12 text-center text-xs text-[#69736F]">No PIN ledger logs recorded.</div>
              )}
            </div>
          )}
        </div>
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
                { label: '🔵 Carry Forward', value: 'CARRY_COMMISSION' },
              ].map((tab) => (
                <button
                  key={tab.value}
                  onClick={() => setCommTypeFilter(tab.value)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer ${
                    commTypeFilter === tab.value
                      ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs'
                      : 'bg-[#F7F4EC] text-[#69736F] hover:text-[#18211F] border border-[#E5E0D3]'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 text-[#69736F] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search beneficiary, code..."
                value={commSearch}
                onChange={(e) => setCommSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-[#F7F4EC] border border-[#E5E0D3] rounded-xl text-xs text-[#18211F] placeholder:text-[#69736F] focus:outline-none focus:border-[#063B32]"
              />
            </div>
          </div>

          {/* Table */}
          {commissionsData?.items && commissionsData.items.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse font-mono">
                <thead>
                  <tr className="border-b border-[#E5E0D3] text-[#69736F] uppercase text-[10px]">
                    <th className="py-3 px-3">Slot / Time</th>
                    <th className="py-3 px-3 font-sans">Beneficiary</th>
                    <th className="py-3 px-3 font-sans">Type</th>
                    <th className="py-3 px-3 font-sans">Trigger Source</th>
                    <th className="py-3 px-3">Amount</th>
                    <th className="py-3 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E5E0D3]/60">
                  {commissionsData.items.map((c) => (
                    <tr key={c.id} className="hover:bg-[#F7F4EC]/60 transition-colors">
                      <td className="py-3 px-3 text-[#69736F]">
                        <div className="font-bold text-[#18211F]">{c.slot_id}</div>
                        <div className="text-[10px]">{new Date(c.created_at).toLocaleTimeString()}</div>
                      </td>
                      <td className="py-3 px-3 font-sans">
                        <div className="font-bold text-[#063B32]">{c.beneficiary_name}</div>
                      </td>
                      <td className="py-3 px-3 font-sans">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                          c.commission_type === 'DIRECT_REFERRAL' || c.commission_type === 'DIRECT_COMMISSION'
                            ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
                            : c.commission_type === 'PAIR_BONUS'
                            ? 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766]'
                            : c.commission_type === 'MATCHING_COMMISSION'
                            ? 'bg-orange-50 text-orange-800 border-orange-200'
                            : 'bg-blue-50 text-blue-800 border-blue-200'
                        }`}>
                          {c.commission_type.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3 px-3 font-sans">
                        <div className="text-[#18211F]">{c.source_user_name || 'System / Volume Match'}</div>
                        {c.source_user_code && <div className="text-[10px] text-[#69736F] font-mono">{c.source_user_code}</div>}
                      </td>
                      <td className="py-3 px-3 font-bold text-[#063B32] text-sm">
                        ₹{c.amount?.toLocaleString()}
                      </td>
                      <td className="py-3 px-3 text-right font-sans">
                        <button
                          onClick={() => setSelectedCommission(c)}
                          className="px-2.5 py-1 rounded-xl bg-[#F7F4EC] hover:bg-[#063B32] text-[#063B32] hover:text-[#FFFEF9] border border-[#E5E0D3] text-[11px] font-bold transition-colors cursor-pointer"
                        >
                          View Calc
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-12 text-center text-xs text-[#69736F]">No commissions found matching filters.</div>
          )}
        </div>
      )}

      {/* 2. Slot Settlements */}
      {adminTab === 'settlements' && (
        <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card space-y-4">
          <div className="flex items-center justify-between border-b border-[#E5E0D3] pb-4">
            <div>
              <h2 className="text-lg font-heading font-extrabold text-[#18211F]">12-Hour Slot Settlement History</h2>
              <p className="text-xs text-[#69736F]">
                Automated 12:00 PM and 12:00 AM India Time slot volume consumption and commission disbursements.
              </p>
            </div>
            <span className="text-xs font-mono bg-[#F7F4EC] px-3 py-1.5 rounded-xl border border-[#E5E0D3] font-bold text-[#063B32]">
              {settlementsData?.total || 0} Slots Settled
            </span>
          </div>

          {settlementsData?.items && settlementsData.items.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse font-mono">
                <thead>
                  <tr className="border-b border-[#E5E0D3] text-[#69736F] uppercase text-[10px]">
                    <th className="py-3 px-3">Slot ID</th>
                    <th className="py-3 px-3 font-sans">User</th>
                    <th className="py-3 px-3">Volumes (L / R)</th>
                    <th className="py-3 px-3">Pairs</th>
                    <th className="py-3 px-3">Pair Bonus</th>
                    <th className="py-3 px-3">Matching Comm</th>
                    <th className="py-3 px-3 font-sans">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E5E0D3]/60">
                  {settlementsData.items.map((s) => (
                    <tr key={s.id} className="hover:bg-[#F7F4EC]/60 transition-colors">
                      <td className="py-3 px-3 font-bold text-[#18211F]">{s.slot_id}</td>
                      <td className="py-3 px-3 font-sans">
                        <div className="font-bold text-[#063B32]">{s.user_name || `User #${s.user_id}`}</div>
                        <div className="text-[10px] text-[#69736F] font-mono">{s.user_code}</div>
                      </td>
                      <td className="py-3 px-3 text-[#69736F]">
                        L: ₹{s.left_before?.toLocaleString()} • R: ₹{s.right_before?.toLocaleString()}
                      </td>
                      <td className="py-3 px-3 font-bold text-[#C9A227]">{s.pairs_paid || 0}</td>
                      <td className="py-3 px-3 font-bold text-[#063B32]">₹{s.pair_bonus?.toLocaleString()}</td>
                      <td className="py-3 px-3 text-[#18211F]">₹{s.matching_commission?.toLocaleString()}</td>
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
            <div className="py-12 text-center text-xs text-[#69736F]">No slot settlement logs recorded yet.</div>
          )}
        </div>
      )}

      {/* 3. Volume Ledger */}
      {adminTab === 'volume_ledger' && (
        <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card space-y-4">
          <div className="flex items-center justify-between border-b border-[#E5E0D3] pb-4">
            <div>
              <h2 className="text-lg font-heading font-extrabold text-[#18211F]">Binary Volume Propagation Ledger</h2>
              <p className="text-xs text-[#69736F]">
                FIFO tracking of volume segments as 30,000 BV bubbles upward through Left & Right binary ancestry trees.
              </p>
            </div>
            <span className="text-xs font-mono bg-[#F7F4EC] px-3 py-1.5 rounded-xl border border-[#E5E0D3] font-bold text-[#063B32]">
              {volumeLedgerData?.total || 0} Ledger Entries
            </span>
          </div>

          {volumeLedgerData?.items && volumeLedgerData.items.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse font-mono">
                <thead>
                  <tr className="border-b border-[#E5E0D3] text-[#69736F] uppercase text-[10px]">
                    <th className="py-3 px-3 font-sans">Origin Buyer</th>
                    <th className="py-3 px-3 font-sans">Beneficiary Leg</th>
                    <th className="py-3 px-3">Side</th>
                    <th className="py-3 px-3">Slot</th>
                    <th className="py-3 px-3">Original BV</th>
                    <th className="py-3 px-3">Consumed</th>
                    <th className="py-3 px-3">Remaining BV</th>
                    <th className="py-3 px-3 font-sans">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E5E0D3]/60">
                  {volumeLedgerData.items.map((v) => (
                    <tr key={v.id} className="hover:bg-[#F7F4EC]/60 transition-colors">
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

      {/* ONE-TIME SECURITY PIN DISPLAY DIALOG */}
      {generatedPinModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
          <div 
            className="w-full max-w-lg rounded-3xl bg-[#FFFEF9] border-2 border-[#C9A227] shadow-wealth-gold p-6 sm:p-7 relative text-[#18211F]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-2 text-[#8C6C16] text-xs font-mono font-bold uppercase tracking-wider mb-2">
              <Sparkles className="w-4 h-4 text-[#C9A227]" />
              <span>One-Time Security PIN Issued</span>
            </div>

            <h3 className="text-2xl font-heading font-extrabold text-[#18211F] mb-1">
              Security PIN Generated
            </h3>
            <p className="text-xs text-[#69736F] mb-5">
              Provide this single-use activation PIN to <strong className="text-[#063B32]">{generatedPinModal.request?.user_name || 'the member'}</strong> ({generatedPinModal.request?.user_code}) to activate their ₹35,000 package.
            </p>

            {/* Secret PIN Box */}
            <div className="p-5 rounded-2xl bg-[#063B32] text-[#FFFEF9] text-center mb-4 relative overflow-hidden shadow-wealth-card">
              <div className="text-[10px] font-mono uppercase tracking-widest text-[#C9A227] mb-1">
                SECRET SINGLE-USE ACTIVATION PIN
              </div>
              <div className="text-3xl sm:text-4xl font-mono font-black tracking-[0.3em] text-[#FFFEF9] my-2 select-all">
                {generatedPinModal.raw_security_pin}
              </div>
              <div className="text-[10px] text-[#F7F4EC]/75 font-mono">
                Ref Code: {generatedPinModal.pin?.pin_code} • Valid for 7 days
              </div>
            </div>

            {/* Warning Alert */}
            <div className="p-3.5 rounded-2xl bg-[#FAF4DC] border border-[#E2C766] text-[#8C6C16] text-xs mb-5 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-[#C88A16] shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Security Notice:</span> For member privacy, this plaintext PIN will <strong>only be shown once</strong> in this dialog. Please copy or securely transmit it now.
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => handleCopyPin(generatedPinModal.raw_security_pin)}
                className="flex-1 py-3.5 rounded-2xl bg-[#C9A227] hover:bg-[#B38F1E] text-[#18211F] font-heading font-black text-xs transition-all shadow-xs flex items-center justify-center gap-2 cursor-pointer"
              >
                {copiedPin ? (
                  <>
                    <Check className="w-4 h-4 text-[#063B32]" />
                    <span>COPIED TO CLIPBOARD!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    <span>COPY SECURITY PIN</span>
                  </>
                )}
              </button>
              <button
                onClick={() => setGeneratedPinModal(null)}
                className="px-5 py-3.5 rounded-2xl border border-[#E5E0D3] hover:bg-[#EFECE2] text-[#18211F] font-bold text-xs transition-colors cursor-pointer"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* BATCH SECURITY PINS GENERATED MODAL (FOR BULK ORDERS) */}
      {batchGeneratedPinsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
          <div 
            className="w-full max-w-2xl rounded-3xl bg-[#FFFEF9] border-2 border-[#C9A227] shadow-wealth-gold p-6 sm:p-7 relative text-[#18211F] max-h-[90vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-2 text-[#8C6C16] text-xs font-mono font-bold uppercase tracking-wider mb-2">
              <Sparkles className="w-4 h-4 text-[#C9A227]" />
              <span>Batch Security PINs Issued</span>
            </div>

            <h3 className="text-2xl font-heading font-extrabold text-[#18211F] mb-1">
              {batchGeneratedPinsModal.pins.length} Security PINs Generated
            </h3>
            <p className="text-xs text-[#69736F] mb-4">
              Issued for <strong className="text-[#063B32]">{batchGeneratedPinsModal.order.buyer_name || 'Member'}</strong> ({batchGeneratedPinsModal.order.buyer_code}) under Order <code className="font-mono">{batchGeneratedPinsModal.order.order_code}</code>.
            </p>

            {/* List of Generated PINs */}
            <div className="flex-1 overflow-y-auto space-y-2 p-3 rounded-2xl bg-[#063B32] mb-4">
              {batchGeneratedPinsModal.pins.map((pinItem, idx) => {
                const rawPin = batchGeneratedPinsModal.raw_pins[idx] || 'N/A';
                return (
                  <div
                    key={pinItem.id || idx}
                    className="p-2.5 rounded-xl bg-[#042C26] border border-[#C9A227]/30 flex items-center justify-between text-xs text-[#FFFEF9]"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[#C9A227] font-bold">#{idx + 1}</span>
                      <span className="font-mono text-base font-black tracking-widest text-[#FFFEF9] select-all">
                        {rawPin}
                      </span>
                    </div>
                    <div className="text-[10px] text-[#F7F4EC]/60 font-mono">
                      Ref: {pinItem.pin_code}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Security Notice */}
            <div className="p-3 rounded-2xl bg-[#FAF4DC] border border-[#E2C766] text-[#8C6C16] text-xs mb-4 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-[#C88A16] shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Security Notice:</span> Plaintext PINs are only visible in this dialog. The buyer also has these PINs directly loaded in their personal <strong>PIN Wallet</strong>.
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  const allPinsFormatted = batchGeneratedPinsModal.pins.map((p, i) => 
                    `PIN #${i + 1}: ${batchGeneratedPinsModal.raw_pins[i]} (Ref: ${p.pin_code})`
                  ).join('\n');
                  navigator.clipboard.writeText(allPinsFormatted);
                  setCopiedBatch(true);
                  showToast('All PINs copied to clipboard!', 'success');
                  setTimeout(() => setCopiedBatch(false), 2500);
                }}
                className="flex-1 py-3 rounded-2xl bg-[#C9A227] hover:bg-[#B38F1E] text-[#18211F] font-heading font-black text-xs transition-all shadow-xs flex items-center justify-center gap-2 cursor-pointer"
              >
                {copiedBatch ? (
                  <>
                    <Check className="w-4 h-4 text-[#063B32]" />
                    <span>ALL PINS COPIED!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    <span>COPY ALL {batchGeneratedPinsModal.pins.length} PINS</span>
                  </>
                )}
              </button>
              <button
                onClick={() => setBatchGeneratedPinsModal(null)}
                className="px-6 py-3 rounded-2xl border border-[#E5E0D3] hover:bg-[#EFECE2] text-[#18211F] font-bold text-xs transition-colors cursor-pointer"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* REJECT REQUEST MODAL (SINGLE USER) */}
      {rejectingReq && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
          <div 
            className="w-full max-w-md rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-elevated p-6 relative text-[#18211F]"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-xl font-heading font-extrabold text-[#18211F] mb-1">
              Reject Activation Request
            </h3>
            <p className="text-xs text-[#69736F] mb-4">
              Specify reason for rejecting request <code className="font-mono font-bold text-[#18211F]">{rejectingReq.request_code}</code> from {rejectingReq.user_name}.
            </p>

            <form onSubmit={handleConfirmReject} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#18211F] mb-1">
                  Rejection Reason <span className="text-red-600">*</span>
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="e.g. Payment reference not found in bank statement / Incorrect amount"
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#E5E0D3] text-xs text-[#18211F] focus:outline-none focus:border-red-500"
                />
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setRejectingReq(null)}
                  className="flex-1 px-4 py-2.5 rounded-xl border border-[#E5E0D3] hover:bg-[#EFECE2] text-xs font-bold transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={rejectLoading || !rejectReason.trim()}
                  className="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition-colors disabled:opacity-50 cursor-pointer"
                >
                  {rejectLoading ? 'Rejecting...' : 'Confirm Reject'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* REJECT BULK PIN ORDER MODAL */}
      {rejectingPinOrder && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
          <div 
            className="w-full max-w-md rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-elevated p-6 relative text-[#18211F]"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-xl font-heading font-extrabold text-[#18211F] mb-1">
              Reject Bulk PIN Order
            </h3>
            <p className="text-xs text-[#69736F] mb-4">
              Specify reason for rejecting PIN Order <code className="font-mono font-bold text-[#18211F]">{rejectingPinOrder.order_code}</code> from {rejectingPinOrder.buyer_name}.
            </p>

            <form onSubmit={handleRejectPinOrderSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#18211F] mb-1">
                  Rejection Reason <span className="text-red-600">*</span>
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="e.g. Payment UTR could not be verified / Amount mismatch"
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#E5E0D3] text-xs text-[#18211F] focus:outline-none focus:border-red-500"
                />
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setRejectingPinOrder(null)}
                  className="flex-1 px-4 py-2.5 rounded-xl border border-[#E5E0D3] hover:bg-[#EFECE2] text-xs font-bold transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={rejectLoading || !rejectReason.trim()}
                  className="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition-colors disabled:opacity-50 cursor-pointer"
                >
                  {rejectLoading ? 'Rejecting...' : 'Confirm Reject'}
                </button>
              </div>
            </form>
          </div>
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

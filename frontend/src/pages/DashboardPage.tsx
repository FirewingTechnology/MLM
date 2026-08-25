import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useOutletContext, Link } from 'react-router-dom';
import api from '../services/api';
import { useToast } from '../context/ToastContext';
import { DashboardData, Commission, BinaryTreeNode } from '../types';
import { CommissionDetailModal } from '../components/modals/CommissionDetailModal';
import { WithdrawalModal } from '../components/modals/WithdrawalModal';
import { 
  Wallet, 
  TrendingUp, 
  Coins, 
  Users, 
  GitFork, 
  Copy, 
  Check, 
  ArrowUpRight, 
  ShoppingBag, 
  PackageCheck,
  ChevronRight,
  Sparkles
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { openPurchaseModal } = useOutletContext<{ openPurchaseModal: () => void }>();
  const { showToast } = useToast();

  const [copied, setCopied] = useState(false);
  const [selectedCommission, setSelectedCommission] = useState<Commission | null>(null);
  const [isWithdrawalModalOpen, setIsWithdrawalModalOpen] = useState(false);

  const { data, isLoading } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const res = await api.get('/dashboard');
      return res.data.data;
    },
    refetchInterval: 10000,
  });

  const { data: treeData } = useQuery<BinaryTreeNode>({
    queryKey: ['networkMiniTree'],
    queryFn: async () => {
      const res = await api.get('/network?depth=2');
      return res.data.data;
    },
  });

  const kpis = data?.kpis;
  const user = data?.user;

  const referralLink = user?.referral_code
    ? `${window.location.origin}/register?ref=${user.referral_code}`
    : '';

  const handleCopyReferral = () => {
    if (!referralLink) return;
    navigator.clipboard.writeText(referralLink);
    setCopied(true);
    showToast('Referral link copied to clipboard!', 'success');
    setTimeout(() => setCopied(false), 2500);
  };

  if (isLoading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-28 rounded-3xl bg-slate-800/40" />
        <div className="grid grid-cols-2 gap-3">
          <div className="h-24 rounded-2xl bg-slate-800/40" />
          <div className="h-24 rounded-2xl bg-slate-800/40" />
        </div>
      </div>
    );
  }

  const leftBv = kpis?.left_bv || 0;
  const rightBv = kpis?.right_bv || 0;

  return (
    <div className="space-y-4 sm:space-y-6 max-w-5xl mx-auto">
      {/* 1. Main Virtual Wallet Card */}
      <div className="rounded-3xl glass-panel p-5 sm:p-6 border border-slate-800 relative overflow-hidden bg-gradient-to-br from-navy-900 via-navy-950 to-slate-900 shadow-xl">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span className="text-[11px] font-bold uppercase tracking-wider text-brand-400 flex items-center gap-1.5">
            <Wallet className="w-4 h-4" />
            <span>Virtual Wallet</span>
          </span>
          <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
            Demo Balance
          </span>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 mt-1">
          <div className="text-3xl sm:text-4xl font-black text-white font-mono tracking-tight">
            ₹{kpis?.wallet_balance?.toLocaleString() || 0}
          </div>
          <div className="text-xs text-emerald-400 font-mono">
            Total Earned: ₹{kpis?.total_earnings?.toLocaleString() || 0}
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <span>{user?.full_name} ({user?.user_code})</span>
          <button
            onClick={() => setIsWithdrawalModalOpen(true)}
            className="text-emerald-400 hover:text-emerald-300 font-bold flex items-center gap-1"
          >
            <span>Demo Withdrawal</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 2. Two Volume Cards: Left BV & Right BV */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4">
        {/* Left BV */}
        <div className="rounded-2xl glass-panel p-4 border border-slate-800 relative glass-panel-hover">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-300">Left BV</span>
            <span className="text-[10px] bg-slate-800 text-emerald-400 px-2 py-0.5 rounded font-mono font-bold">LEFT</span>
          </div>
          <div className="text-xl sm:text-2xl font-black text-white font-mono">
            ₹{leftBv.toLocaleString()}
          </div>
          <div className="text-[10px] text-emerald-400 font-mono mt-1">
            Carry: ₹{kpis?.carry_left_bv?.toLocaleString() || 0}
          </div>
        </div>

        {/* Right BV */}
        <div className="rounded-2xl glass-panel p-4 border border-slate-800 relative glass-panel-hover">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-300">Right BV</span>
            <span className="text-[10px] bg-slate-800 text-blue-400 px-2 py-0.5 rounded font-mono font-bold">RIGHT</span>
          </div>
          <div className="text-xl sm:text-2xl font-black text-white font-mono">
            ₹{rightBv.toLocaleString()}
          </div>
          <div className="text-[10px] text-blue-400 font-mono mt-1">
            Carry: ₹{kpis?.carry_right_bv?.toLocaleString() || 0}
          </div>
        </div>
      </div>

      {/* 3. Main Action: BUY ₹35,000 PACKAGE */}
      <button
        onClick={openPurchaseModal}
        className="w-full flex items-center justify-center gap-2.5 py-4 rounded-2xl bg-gradient-to-r from-brand-500 via-emerald-500 to-teal-500 hover:from-brand-400 hover:to-emerald-400 text-navy-950 font-black text-base shadow-glow-emerald transition-all transform hover:scale-[1.01] active:scale-[0.99]"
      >
        <ShoppingBag className="w-5 h-5" />
        <span>BUY ₹35,000 PACKAGE</span>
      </button>

      {/* 4. Referral Section */}
      <div className="rounded-2xl glass-panel p-4 sm:p-5 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-brand-400" />
            <span>Your Referral</span>
          </div>
          <span className="text-[10px] text-brand-400 font-bold">10% Direct Bonus</span>
        </div>

        <div className="flex items-center justify-between p-2.5 rounded-xl bg-navy-950 border border-slate-800 gap-2">
          <div className="min-w-0 flex-1 pl-1">
            <div className="text-sm font-mono font-black text-white tracking-wider truncate">
              {user?.referral_code}
            </div>
            <div className="text-[10px] text-slate-500 truncate font-mono">
              {referralLink}
            </div>
          </div>
          <button
            onClick={handleCopyReferral}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-400 text-navy-950 font-bold text-xs shrink-0 transition-all"
          >
            {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      {/* 5. Binary Network Preview */}
      <div className="rounded-2xl glass-panel p-4 sm:p-5 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <GitFork className="w-3.5 h-3.5 text-blue-400" />
            <span>Binary Network Preview</span>
          </div>
          <Link
            to="/network"
            className="text-xs text-brand-400 hover:text-brand-300 font-bold flex items-center gap-1"
          >
            <span>View Full Network</span>
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Small Visual Binary Subtree */}
        <div className="p-4 rounded-xl bg-navy-950/80 border border-slate-800/80 flex flex-col items-center">
          {/* Root Node */}
          <div className="px-4 py-2 rounded-xl bg-navy-900 border border-brand-500/50 text-center shadow-sm">
            <div className="text-xs font-bold text-white">{treeData?.full_name || user?.full_name}</div>
            <div className="text-[10px] text-brand-400 font-mono">YOU ({treeData?.user_code || user?.user_code})</div>
          </div>

          {/* Connectors */}
          <div className="w-32 h-4 border-b border-slate-700 border-l border-r my-1" />

          {/* Left / Right Children */}
          <div className="w-full flex justify-between gap-2 max-w-xs">
            {/* Left */}
            <div className="flex-1 p-2 rounded-lg bg-navy-900 border border-slate-800 text-center">
              <div className="text-[9px] font-bold uppercase text-emerald-400">Left Leg</div>
              <div className="text-xs font-semibold text-slate-200 truncate">
                {treeData?.left ? treeData.left.full_name : 'Open Slot'}
              </div>
            </div>

            {/* Right */}
            <div className="flex-1 p-2 rounded-lg bg-navy-900 border border-slate-800 text-center">
              <div className="text-[9px] font-bold uppercase text-blue-400">Right Leg</div>
              <div className="text-xs font-semibold text-slate-200 truncate">
                {treeData?.right ? treeData.right.full_name : 'Open Slot'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      <CommissionDetailModal
        commission={selectedCommission}
        onClose={() => setSelectedCommission(null)}
      />

      <WithdrawalModal
        isOpen={isWithdrawalModalOpen}
        onClose={() => setIsWithdrawalModalOpen(false)}
        availableBalance={kpis?.wallet_balance || 0}
      />
    </div>
  );
};

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useOutletContext, Link } from 'react-router-dom';
import api from '../services/api';
import { useToast } from '../context/ToastContext';
import { DashboardData, Commission, MatchingTreeNode, ReferralLinksData, ActivationStatusResponse, PinWalletData, EarningCapOverviewResponse } from '../types';
import { CommissionDetailModal } from '../components/modals/CommissionDetailModal';
import { WithdrawalModal } from '../components/modals/WithdrawalModal';
import { PinWalletModal } from '../components/modals/PinWalletModal';
import { SlotCard } from '../components/dashboard/SlotCard';
import { PairSummaryCard } from '../components/dashboard/PairSummaryCard';
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
  Sparkles,
  KeyRound,
  Clock,
  ShieldCheck,
  DownloadCloud,
  Send,
  ArrowRightLeft,
  Award,
  Crown,
  Star,
  AlertTriangle,
  RefreshCw,
  Zap
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { openPurchaseModal } = useOutletContext<{ openPurchaseModal: () => void }>();
  const { showToast } = useToast();

  const [copied, setCopied] = useState(false);
  const [selectedCommission, setSelectedCommission] = useState<Commission | null>(null);
  const [isWithdrawalModalOpen, setIsWithdrawalModalOpen] = useState(false);
  const [isPinWalletModalOpen, setIsPinWalletModalOpen] = useState(false);
  const [pinWalletTab, setPinWalletTab] = useState<'overview' | 'buy' | 'give' | 'request' | 'incoming' | 'history'>('overview');

  const { data: pinWallet, refetch: refetchPinWallet } = useQuery<PinWalletData>({
    queryKey: ['pinWallet'],
    queryFn: async () => {
      const res = await api.get('/security-pins/inventory');
      return res.data.data;
    },
    refetchInterval: 8000,
  });

  const { data, isLoading } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const res = await api.get('/dashboard');
      return res.data.data;
    },
    refetchInterval: 10000,
  });

  const { data: treeData } = useQuery<MatchingTreeNode>({
    queryKey: ['networkMiniTree'],
    queryFn: async () => {
      const res = await api.get('/network?depth=2');
      return res.data.data;
    },
  });

  const [copiedLeft, setCopiedLeft] = useState(false);
  const [copiedRight, setCopiedRight] = useState(false);

  const kpis = data?.kpis;
  const user = data?.user;

  const { data: linksData } = useQuery<ReferralLinksData>({
    queryKey: ['referralLinks'],
    queryFn: async () => {
      const res = await api.get('/referral/links');
      return res.data.data;
    },
  });

  const { data: activationStatus } = useQuery<ActivationStatusResponse>({
    queryKey: ['activationStatus'],
    queryFn: async () => {
      const res = await api.get('/package/activation-status');
      return res.data.data;
    },
  });

  const { data: earningCap } = useQuery<EarningCapOverviewResponse>({
    queryKey: ['earningCapOverview'],
    queryFn: async () => {
      const res = await api.get('/earning-cap/overview');
      return res.data;
    },
    refetchInterval: 10000,
  });

  const leftUrl = linksData?.left?.token
    ? `${window.location.origin}/register?ref=${linksData.left.token}`
    : user?.referral_code
      ? `${window.location.origin}/register?ref=${user.referral_code}`
      : '';

  const rightUrl = linksData?.right?.token
    ? `${window.location.origin}/register?ref=${linksData.right.token}`
    : user?.referral_code
      ? `${window.location.origin}/register?ref=${user.referral_code}`
      : '';

  const handleCopyLeft = () => {
    if (!leftUrl) return;
    navigator.clipboard.writeText(leftUrl);
    setCopiedLeft(true);
    showToast('LEFT Referral Link copied!', 'success');
    setTimeout(() => setCopiedLeft(false), 2500);
  };

  const handleCopyRight = () => {
    if (!rightUrl) return;
    navigator.clipboard.writeText(rightUrl);
    setCopiedRight(true);
    showToast('RIGHT Referral Link copied!', 'success');
    setTimeout(() => setCopiedRight(false), 2500);
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

  const carryData = data?.carry || data?.carry_summary || kpis?.carry || kpis?.carry_summary;

  const leftCarryCount = carryData?.left?.count ?? carryData?.left?.carry_count ?? (Math.floor((kpis?.carry_left_bv || 0) / 30000));
  const leftPaidCount = carryData?.left?.paid_count ?? carryData?.left?.paid_members ?? carryData?.left?.paid_pairs ?? 0;
  const leftUnpaidCount = carryData?.left?.unpaid_count ?? carryData?.left?.unpaid_members ?? carryData?.left?.unpaid_pairs ?? 0;

  const rightCarryCount = carryData?.right?.count ?? carryData?.right?.carry_count ?? (Math.floor((kpis?.carry_right_bv || 0) / 30000));
  const rightPaidCount = carryData?.right?.paid_count ?? carryData?.right?.paid_members ?? carryData?.right?.paid_pairs ?? 0;
  const rightUnpaidCount = carryData?.right?.unpaid_count ?? carryData?.right?.unpaid_members ?? carryData?.right?.unpaid_pairs ?? 0;

  // Dynamic greeting based on current hour
  const currentHour = new Date().getHours();
  const greeting = currentHour < 12 ? 'Good Morning' : currentHour < 17 ? 'Good Afternoon' : 'Good Evening';

  return (
    <div className="space-y-5 sm:space-y-6 max-w-5xl mx-auto">
      {/* 0. Welcome Hero Section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-[#18211F] tracking-tight">
              {greeting}, {user?.full_name?.split(' ')[0] || 'Distributor'} 👋
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-[#69736F] font-medium">
            Private Wealth Platform • Matching Network Volume • ₹15,000 Pair Rewards
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${user?.is_active
                ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
                : 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766]'
              }`}
          >
            <span className={`w-2 h-2 rounded-full ${user?.is_active ? 'bg-[#0E9F6E]' : 'bg-[#C88A16]'}`} />
            <span>{user?.is_active ? 'Active Wealth Member' : 'Inactive Account'}</span>
          </span>
        </div>
      </div>

      {/* 1. Live India Time & 12-Hour Slot Card */}
      <SlotCard
        slotEarnings={kpis?.slot_earnings}
        slotCommissionsCount={kpis?.slot_commissions_count}
      />

      {/* 2. Main Wealth Card (Visual Centerpiece in Deep Emerald) */}
      <div className="rounded-3xl wealth-hero p-6 sm:p-7 relative overflow-hidden text-[#FFFEF9]">
        <div className="flex items-center justify-between text-[#F7F4EC]/75 mb-2">
          <span className="text-xs font-bold uppercase tracking-widest text-[#C9A227] flex items-center gap-1.5 font-mono">
            <Wallet className="w-4 h-4 text-[#C9A227]" />
            <span>Income Wallet</span>
          </span>
          <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#FAF4DC]/15 text-[#E2C766] border border-[#C9A227]/30 font-mono">
            Available Balance
          </span>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-3 mt-1">
          <div>
            <div className="text-3xl sm:text-5xl font-heading font-black text-[#E2C766] font-mono tracking-tight">
              ₹{kpis?.wallet_balance?.toLocaleString() || 0}
            </div>
            <div className="text-xs text-[#F7F4EC]/80 font-medium mt-1">
              Eligible for instant payout settlement
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-[#042C26] border border-[#C9A227]/25 text-left">
              <div className="text-[10px] text-[#C9A227] font-bold uppercase font-sans">Pair Bonus</div>
              <div className="text-sm font-bold text-[#FFFEF9] font-mono">+₹{(kpis?.pair_summary?.pair_bonus_earned || kpis?.pair_commissions || 0).toLocaleString()}</div>
            </div>
            <div className="p-3 rounded-2xl bg-[#042C26] border border-[#C9A227]/25 text-left">
              <div className="text-[10px] text-[#E0F3EE] font-bold uppercase font-sans">Total Earned</div>
              <div className="text-sm font-bold text-[#E2C766] font-mono">+₹{(kpis?.total_earnings || 0).toLocaleString()}</div>
            </div>
          </div>
        </div>

        <div className="mt-5 pt-4 border-t border-[#0B5145] flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="text-[#F7F4EC]/75 font-mono">
            {user?.full_name} <span className="text-[#C9A227]/80">({user?.user_code})</span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsWithdrawalModalOpen(true)}
              className="text-[#18211F] hover:bg-[#F4E7B4] font-bold flex items-center gap-1.5 bg-[#E2C766] px-3.5 py-1.5 rounded-xl border border-[#C9A227] transition-all cursor-pointer shadow-sm"
            >
              <span>Request Payout</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
            <Link
              to="/wallet"
              className="text-[#FFFEF9] hover:bg-[#0A4D42] font-bold flex items-center gap-1 bg-[#042C26] px-3.5 py-1.5 rounded-xl border border-[#C9A227]/30 transition-colors"
            >
              <span>View Ledger</span>
              <ChevronRight className="w-3.5 h-3.5 text-[#C9A227]" />
            </Link>
          </div>
        </div>
      </div>

      {/* 1b. ₹3,00,000 EARNING LIMIT / RETOPUP CARD */}
      {earningCap && (
        <div className={`p-5 sm:p-6 rounded-3xl border shadow-wealth-card transition-all ${earningCap.is_retopup_required
            ? 'bg-gradient-to-br from-[#FFF5F5] via-[#FFF8F8] to-[#FFEBEB] border-[#E53E3E]'
            : earningCap.progress_percentage >= 80
              ? 'bg-gradient-to-br from-[#FFFDF5] via-[#FFFEF9] to-[#FFF9E6] border-[#D69E2E]'
              : 'bg-[#FFFEF9] border-[#E5E0D3]'
          }`}>
          {earningCap.is_retopup_required ? (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-2xl bg-[#C53030] text-white flex items-center justify-center shrink-0 shadow-sm animate-pulse">
                    <AlertTriangle className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-[#C53030] text-white">
                        RETOPUP REQUIRED
                      </span>
                      <span className="text-xs font-mono font-bold text-[#742A2A]">
                        Cycle #{earningCap.cycle_number} Limit Reached
                      </span>
                    </div>
                    <h3 className="text-lg font-heading font-extrabold text-[#9B2C2C] mt-0.5">
                      ₹{earningCap.total_eligible_income?.toLocaleString()} / ₹{earningCap.earning_cap?.toLocaleString()}
                    </h3>
                  </div>
                </div>

                <button
                  onClick={() => openPurchaseModal()}
                  className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] text-sm font-extrabold shadow-md hover:shadow-lg transition-all cursor-pointer border border-[#C9A227]/40 shrink-0"
                >
                  <RefreshCw className="w-4 h-4 text-[#E2C766]" />
                  <span>RE-PURCHASE / TOP UP</span>
                </button>
              </div>

              <div className="p-3.5 rounded-2xl bg-white/90 border border-[#FEB2B2] text-xs font-medium text-[#742A2A] flex items-start gap-2.5">
                <Zap className="w-4 h-4 text-[#E53E3E] shrink-0 mt-0.5" />
                <div>
                  Your current earning cycle has reached the ₹3,00,000 limit. Please purchase/renew the qualifying package to activate your next earning cycle and resume receiving Direct and Pairing bonuses.
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-3.5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <div className="w-10 h-10 rounded-2xl bg-[#063B32] text-[#E2C766] flex items-center justify-center shrink-0">
                    <Zap className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] uppercase font-bold tracking-widest text-[#69736F] font-mono">
                        Active Earning Window (Cycle #{earningCap.cycle_number})
                      </span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#E0F3EE] text-[#063B32] border border-[#8DCFBF]">
                        {earningCap.status}
                      </span>
                    </div>
                    <div className="text-base font-heading font-extrabold text-[#18211F]">
                      ₹{earningCap.total_eligible_income?.toLocaleString()} <span className="text-xs font-medium text-[#69736F]">/ ₹{earningCap.earning_cap?.toLocaleString()} Cap</span>
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-[10px] uppercase font-bold text-[#69736F]">Remaining Capacity</div>
                  <div className="text-sm font-extrabold text-[#063B32] font-mono">
                    ₹{earningCap.remaining_capacity?.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-1.5">
                <div className="w-full h-2.5 rounded-full bg-[#E5E0D3] overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${earningCap.progress_percentage >= 80
                        ? 'bg-gradient-to-r from-[#D69E2E] to-[#C53030]'
                        : 'bg-gradient-to-r from-[#063B32] to-[#C9A227]'
                      }`}
                    style={{ width: `${Math.min(100, earningCap.progress_percentage)}%` }}
                  />
                </div>
                <div className="flex justify-between items-center text-[11px] text-[#69736F] font-medium">
                  <span>Direct: ₹{earningCap.direct_income?.toLocaleString()} + Pairing: ₹{earningCap.pairing_income?.toLocaleString()}</span>
                  <span className="font-bold text-[#18211F]">{earningCap.progress_percentage}% Utilized</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 2. RANK & REWARDS MILESTONE BANNER */}
      <div className="p-4 sm:p-5 rounded-3xl bg-gradient-to-r from-[#FAF4DC] via-[#FFFEF9] to-[#FAF4DC] border border-[#E2C766] shadow-wealth-card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-2xl bg-[#063B32] border border-[#C9A227]/40 flex items-center justify-center text-[#E2C766] shadow-sm shrink-0">
            <Award className="w-6 h-6 text-[#E2C766]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase font-bold tracking-widest text-[#8C6C16] font-mono">
                Leadership Milestone
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-[#063B32] text-[#FFFEF9] border border-[#C9A227]/30">
                {user?.current_rank || 'DISTRIBUTOR'}
              </span>
            </div>
            <div className="text-sm sm:text-base font-heading font-extrabold text-[#18211F]">
              Rank & Rewards Sprint Program
            </div>
            <div className="text-xs text-[#69736F] font-medium">
              Earn ₹2,100 Star, ₹5,100 Super Star, and ₹51,000 Cash or EV Scooter VIP awards.
            </div>
          </div>
        </div>

        <Link
          to="/ranks"
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/40 text-xs font-bold transition-all shadow-sm shrink-0 cursor-pointer"
        >
          <span>View Rank Progress</span>
          <ArrowUpRight className="w-4 h-4 text-[#C9A227]" />
        </Link>
      </div>

      {/* 2a. SECURITY PIN PREPAID WALLET CARD */}
      <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E5E0D3] pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#FAF4DC] border border-[#E2C766] flex items-center justify-center text-[#8C6C16] shadow-2xs">
              <KeyRound className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base sm:text-lg font-heading font-extrabold text-[#18211F]">
                  Security PIN Wallet
                </h2>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#E0F3EE] text-[#063B32] border border-[#8DCFBF] font-mono">
                  Prepaid Credits
                </span>
              </div>
              <p className="text-xs text-[#69736F]">
                Transfer single-use activation credits to downline members or order bulk PIN inventory from Admin.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setPinWalletTab('overview');
                setIsPinWalletModalOpen(true);
              }}
              className="px-3.5 py-1.5 rounded-xl bg-[#063B32] hover:bg-[#063B32]/90 text-[#FFFEF9] text-xs font-bold shadow-xs transition-all cursor-pointer flex items-center gap-1.5"
            >
              <KeyRound className="w-3.5 h-3.5 text-[#C9A227]" />
              <span>Open PIN Wallet</span>
            </button>
          </div>
        </div>

        {/* PIN Inventory Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div
            onClick={() => {
              setPinWalletTab('overview');
              setIsPinWalletModalOpen(true);
            }}
            className="p-3.5 rounded-2xl bg-[#F7F4EC]/70 border border-[#E5E0D3] hover:border-[#063B32] cursor-pointer transition-all"
          >
            <div className="text-[10px] text-[#69736F] font-bold uppercase">Available PINs</div>
            <div className="text-2xl font-heading font-black text-[#063B32] font-mono mt-0.5">
              {pinWallet?.wallet?.available ?? 0}
            </div>
            <div className="text-[10px] text-[#0E9F6E] font-medium mt-0.5 flex items-center gap-1">
              <span>Ready for activation</span>
            </div>
          </div>

          <div
            onClick={() => {
              setPinWalletTab('give');
              setIsPinWalletModalOpen(true);
            }}
            className="p-3.5 rounded-2xl bg-[#F7F4EC]/70 border border-[#E5E0D3] hover:border-[#063B32] cursor-pointer transition-all"
          >
            <div className="text-[10px] text-[#69736F] font-bold uppercase">Transferred</div>
            <div className="text-2xl font-heading font-black text-[#8C6C16] font-mono mt-0.5">
              {pinWallet?.wallet?.transferred ?? 0}
            </div>
            <div className="text-[10px] text-[#69736F] font-medium mt-0.5">Given to downlines</div>
          </div>

          <div
            onClick={() => {
              setPinWalletTab('overview');
              setIsPinWalletModalOpen(true);
            }}
            className="p-3.5 rounded-2xl bg-[#F7F4EC]/70 border border-[#E5E0D3] hover:border-[#063B32] cursor-pointer transition-all"
          >
            <div className="text-[10px] text-[#69736F] font-bold uppercase">Received / Used</div>
            <div className="text-2xl font-heading font-black text-[#18211F] font-mono mt-0.5">
              {pinWallet?.wallet?.received ?? 0} <span className="text-xs text-[#69736F] font-normal">/ {pinWallet?.wallet?.used ?? 0}</span>
            </div>
            <div className="text-[10px] text-[#69736F] font-medium mt-0.5">From sponsor / Activated</div>
          </div>

          <div
            onClick={() => {
              setPinWalletTab('buy');
              setIsPinWalletModalOpen(true);
            }}
            className="p-3.5 rounded-2xl bg-gradient-to-br from-[#FAF4DC] to-[#F7F4EC] border border-[#E2C766] hover:shadow-xs cursor-pointer transition-all flex flex-col justify-between"
          >
            <div>
              <div className="text-[10px] text-[#8C6C16] font-bold uppercase">Order from Admin</div>
              <div className="text-xs font-bold text-[#18211F] mt-1">₹35,000 / 30k BV</div>
            </div>
            <div className="text-[10px] font-bold text-[#063B32] flex items-center gap-1 mt-2">
              <span>Buy Bulk PINs</span>
              <ArrowUpRight className="w-3 h-3" />
            </div>
          </div>
        </div>

        {/* Quick Actions Row */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <button
            onClick={() => {
              setPinWalletTab('buy');
              setIsPinWalletModalOpen(true);
            }}
            className="px-3 py-1.5 rounded-xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#063B32] text-xs font-bold hover:bg-[#E5E0D3] transition-colors cursor-pointer flex items-center gap-1.5"
          >
            <DownloadCloud className="w-3.5 h-3.5" />
            <span>Get PINs (Admin)</span>
          </button>

          <button
            onClick={() => {
              setPinWalletTab('give');
              setIsPinWalletModalOpen(true);
            }}
            className="px-3 py-1.5 rounded-xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#8C6C16] text-xs font-bold hover:bg-[#E5E0D3] transition-colors cursor-pointer flex items-center gap-1.5"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Give PIN to Downline</span>
          </button>

          <button
            onClick={() => {
              setPinWalletTab('request');
              setIsPinWalletModalOpen(true);
            }}
            className="px-3 py-1.5 rounded-xl bg-[#F7F4EC] border border-[#E5E0D3] text-blue-800 text-xs font-bold hover:bg-[#E5E0D3] transition-colors cursor-pointer flex items-center gap-1.5"
          >
            <ArrowRightLeft className="w-3.5 h-3.5" />
            <span>Request from Sponsor</span>
          </button>

          {(pinWallet?.wallet?.pending_downline_requests ?? 0) > 0 && (
            <button
              onClick={() => {
                setPinWalletTab('incoming');
                setIsPinWalletModalOpen(true);
              }}
              className="px-3 py-1.5 rounded-xl bg-amber-100 border border-amber-300 text-amber-900 text-xs font-bold hover:bg-amber-200 transition-colors cursor-pointer flex items-center gap-1.5 animate-pulse"
            >
              <span>{pinWallet?.wallet?.pending_downline_requests} Downline Request(s)</span>
            </button>
          )}
        </div>
      </div>

      {/* 2b. Four Performance & Carry Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* Direct Commission */}
        <div className="p-4 rounded-2xl bg-[#FFFEF9] border border-[#8DCFBF] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase text-[#063B32]">
              <span className="w-2 h-2 rounded-full bg-[#0E9F6E]" />
              <span>Direct Sponsor</span>
            </div>
            <div className="text-lg sm:text-xl font-heading font-black text-[#063B32] font-mono mt-1">
              ₹{(kpis?.direct_commissions || 0).toLocaleString()}
            </div>
          </div>
          <div className="text-[10px] text-[#69736F] mt-2 pt-2 border-t border-[#E5E0D3]">10% on direct purchases</div>
        </div>

        {/* Pair Bonus */}
        <div className="p-4 rounded-2xl bg-[#FFFEF9] border border-[#E2C766] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase text-[#8C6C16]">
              <span className="w-2 h-2 rounded-full bg-[#C9A227]" />
              <span>Pair Bonus</span>
            </div>
            <div className="text-lg sm:text-xl font-heading font-black text-[#8C6C16] font-mono mt-1">
              ₹{(kpis?.pair_commissions || 0).toLocaleString()}
            </div>
          </div>
          <div className="text-[10px] text-[#69736F] mt-2 pt-2 border-t border-[#E5E0D3]">₹15k max 1/slot</div>
        </div>

        {/* Left Carry Card */}
        <div className="p-4 rounded-2xl bg-[#FFFEF9] border border-[#8DCFBF] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase text-[#063B32]">
                <span className="w-2 h-2 rounded-full bg-[#0E9F6E]" />
                <span>LEFT CARRY</span>
              </div>
              <span className="text-[9px] font-mono font-bold bg-[#E0F3EE] text-[#063B32] border border-[#8DCFBF]/60 px-1.5 py-0.5 rounded">
                LEFT
              </span>
            </div>
            <div className="text-xl sm:text-2xl font-heading font-black text-[#18211F] font-mono mt-2 tracking-tight">
              {leftCarryCount} CARRY
            </div>
          </div>
          <div className="pt-2.5 mt-2.5 border-t border-[#E5E0D3] grid grid-cols-2 gap-2 text-left">
            <div>
              <div className="flex items-center gap-1 text-[9px] font-bold uppercase tracking-wider text-[#0E9F6E]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#0E9F6E]" />
                <span>PAID</span>
              </div>
              <div className="text-sm sm:text-base font-black font-mono text-[#0E9F6E] mt-0.5">
                {leftPaidCount}
              </div>
            </div>
            <div>
              <div className="flex items-center gap-1 text-[9px] font-bold uppercase tracking-wider text-[#E02424]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#E02424]" />
                <span>UNPAID</span>
              </div>
              <div className="text-sm sm:text-base font-black font-mono text-[#E02424] mt-0.5">
                {leftUnpaidCount}
              </div>
            </div>
          </div>
        </div>

        {/* Right Carry Card */}
        <div className="p-4 rounded-2xl bg-[#FFFEF9] border border-[#E2C766] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase text-[#8C6C16]">
                <span className="w-2 h-2 rounded-full bg-[#C9A227]" />
                <span>RIGHT CARRY</span>
              </div>
              <span className="text-[9px] font-mono font-bold bg-[#FAF4DC] text-[#8C6C16] border border-[#E2C766]/60 px-1.5 py-0.5 rounded">
                RIGHT
              </span>
            </div>
            <div className="text-xl sm:text-2xl font-heading font-black text-[#18211F] font-mono mt-2 tracking-tight">
              {rightCarryCount} CARRY
            </div>
          </div>
          <div className="pt-2.5 mt-2.5 border-t border-[#E5E0D3] grid grid-cols-2 gap-2 text-left">
            <div>
              <div className="flex items-center gap-1 text-[9px] font-bold uppercase tracking-wider text-[#0E9F6E]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#0E9F6E]" />
                <span>PAID</span>
              </div>
              <div className="text-sm sm:text-base font-black font-mono text-[#0E9F6E] mt-0.5">
                {rightPaidCount}
              </div>
            </div>
            <div>
              <div className="flex items-center gap-1 text-[9px] font-bold uppercase tracking-wider text-[#E02424]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#E02424]" />
                <span>UNPAID</span>
              </div>
              <div className="text-sm sm:text-base font-black font-mono text-[#E02424] mt-0.5">
                {rightUnpaidCount}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Matching Pair Bonus & Carry Forward Engine Card */}
      <PairSummaryCard pairSummary={data?.pair_summary || kpis?.pair_summary} />

      {/* 4. Two Volume Cards: Left BV & Right BV */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4">
        {/* Left BV */}
        <div className="rounded-3xl bg-[#FFFEF9] p-5 border border-[#E5E0D3] shadow-wealth-card wealth-card-hover">
          <div className="flex items-center justify-between text-[#69736F] mb-1.5">
            <span className="text-xs font-bold uppercase tracking-wider text-[#063B32]">Left BV</span>
            <span className="text-[10px] bg-[#E0F3EE] text-[#063B32] border border-[#8DCFBF] px-2 py-0.5 rounded-md font-mono font-bold">LEFT</span>
          </div>
          <div className="text-2xl sm:text-3xl font-heading font-black text-[#18211F] font-mono">
            ₹{leftBv.toLocaleString()}
          </div>
          <div className="text-[11px] text-[#063B32] font-mono font-bold mt-1">
            Carry-Forward: ₹{kpis?.carry_left_bv?.toLocaleString() || 0}
          </div>
        </div>

        {/* Right BV */}
        <div className="rounded-3xl bg-[#FFFEF9] p-5 border border-[#E5E0D3] shadow-wealth-card wealth-card-hover">
          <div className="flex items-center justify-between text-[#69736F] mb-1.5">
            <span className="text-xs font-bold uppercase tracking-wider text-[#8C6C16]">Right BV</span>
            <span className="text-[10px] bg-[#FAF4DC] text-[#8C6C16] border border-[#E2C766]/60 px-2 py-0.5 rounded-md font-mono font-bold">RIGHT</span>
          </div>
          <div className="text-2xl sm:text-3xl font-heading font-black text-[#18211F] font-mono">
            ₹{rightBv.toLocaleString()}
          </div>
          <div className="text-[11px] text-[#8C6C16] font-mono font-bold mt-1">
            Carry-Forward: ₹{kpis?.carry_right_bv?.toLocaleString() || 0}
          </div>
        </div>
      </div>

      {/* 5. Main Action: Security PIN Package Activation */}
      {!user?.is_active && (
        <div className="space-y-3">
          {activationStatus?.activation_request?.status === 'PIN_ISSUED' ? (
            <div className="p-4 rounded-3xl bg-[#FAF4DC] border-2 border-[#E2C766] shadow-wealth-gold flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-[#C9A227] text-[#18211F] flex items-center justify-center font-bold shrink-0">
                  <KeyRound className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xs font-bold uppercase tracking-wider text-[#8C6C16] flex items-center gap-1.5 font-mono">
                    <Sparkles className="w-3.5 h-3.5 text-[#C9A227]" />
                    <span>Security PIN Issued — Ready for Activation</span>
                  </div>
                  <div className="text-xs text-[#18211F] font-semibold mt-0.5">
                    Your single-use Security PIN is available. Enter PIN to activate ₹35,000 package (+30,000 BV).
                  </div>
                </div>
              </div>
              <button
                onClick={openPurchaseModal}
                className="px-5 py-2.5 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/40 text-xs font-heading font-black shadow-wealth-card transition-all transform hover:scale-[1.02] active:scale-[0.98] shrink-0 cursor-pointer flex items-center gap-1.5"
              >
                <KeyRound className="w-4 h-4 text-[#C9A227]" />
                <span>ENTER PIN & ACTIVATE</span>
              </button>
            </div>
          ) : activationStatus?.activation_request?.status === 'PAYMENT_SUBMITTED' ? (
            <div className="p-4 rounded-3xl bg-[#E0F3EE] border border-[#8DCFBF] shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-[#063B32] text-[#FFFEF9] flex items-center justify-center shrink-0">
                  <Clock className="w-5 h-5 text-[#C9A227]" />
                </div>
                <div>
                  <div className="text-xs font-bold uppercase tracking-wider text-[#063B32] font-mono">
                    Payment Reference Submitted (Under Admin Review)
                  </div>
                  <div className="text-xs text-[#69736F] font-medium mt-0.5">
                    Ref: <code className="bg-white px-1.5 py-0.5 rounded text-[#18211F] font-mono font-bold">{activationStatus.activation_request.payment_reference}</code>. Admin is reviewing to issue your Security PIN.
                  </div>
                </div>
              </div>
              <button
                onClick={openPurchaseModal}
                className="px-4 py-2 rounded-2xl bg-white border border-[#8DCFBF] hover:bg-[#EFECE2] text-[#063B32] text-xs font-bold transition-colors shrink-0 cursor-pointer"
              >
                View Status
              </button>
            </div>
          ) : null}

          <button
            onClick={openPurchaseModal}
            className="w-full flex items-center justify-center gap-2.5 py-4 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/40 font-heading font-black text-base shadow-wealth-card transition-all transform hover:scale-[1.01] active:scale-[0.99] cursor-pointer"
          >
            <KeyRound className="w-5 h-5 text-[#C9A227]" />
            <span>
              {activationStatus?.activation_request?.status === 'PIN_ISSUED'
                ? 'ENTER SECURITY PIN TO ACTIVATE (+30,000 BV)'
                : activationStatus?.activation_request?.status === 'PAYMENT_SUBMITTED'
                  ? 'VIEW ACTIVATION STATUS & SECURITY PIN'
                  : 'REQUEST SECURITY PIN & ACTIVATE PACKAGE (₹35,000)'}
            </span>
          </button>
        </div>
      )}

      {/* 6. Referral / Invitation Section */}
      <div className="rounded-3xl bg-[#FFFEF9] p-5 sm:p-6 border border-[#E5E0D3] shadow-wealth-card space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold uppercase tracking-wider text-[#18211F] flex items-center gap-1.5">
            <Users className="w-4 h-4 text-[#063B32]" />
            <span>Build Your Network (Locked Placement Links)</span>
          </div>
          <span className="text-[10px] text-[#8C6C16] font-bold bg-[#FAF4DC] px-2 py-0.5 rounded-md border border-[#E2C766]/50">
            10% Direct Sponsor Bonus
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Left Referral */}
          <div className="p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#8DCFBF] flex items-center justify-between gap-2">
            <div className="min-w-0 flex-1 pl-1">
              <div className="flex items-center gap-1 text-xs font-bold text-[#063B32]">
                <span className="w-2 h-2 rounded-full bg-[#063B32]" />
                <span>LEFT LEG PLACEMENT</span>
              </div>
              <div className="text-[10px] text-[#69736F] truncate font-mono mt-0.5">
                {leftUrl}
              </div>
            </div>
            <button
              onClick={handleCopyLeft}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/30 font-bold text-xs transition-all shadow-sm shrink-0 cursor-pointer"
            >
              {copiedLeft ? <Check className="w-3.5 h-3.5 text-[#C9A227]" /> : <Copy className="w-3.5 h-3.5 text-[#C9A227]" />}
              <span>{copiedLeft ? 'Copied' : 'Copy LEFT'}</span>
            </button>
          </div>

          {/* Right Referral */}
          <div className="p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E2C766] flex items-center justify-between gap-2">
            <div className="min-w-0 flex-1 pl-1">
              <div className="flex items-center gap-1 text-xs font-bold text-[#8C6C16]">
                <span className="w-2 h-2 rounded-full bg-[#C9A227]" />
                <span>RIGHT LEG PLACEMENT</span>
              </div>
              <div className="text-[10px] text-[#69736F] truncate font-mono mt-0.5">
                {rightUrl}
              </div>
            </div>
            <button
              onClick={handleCopyRight}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/30 font-bold text-xs transition-all shadow-sm shrink-0 cursor-pointer"
            >
              {copiedRight ? <Check className="w-3.5 h-3.5 text-[#C9A227]" /> : <Copy className="w-3.5 h-3.5 text-[#C9A227]" />}
              <span>{copiedRight ? 'Copied' : 'Copy RIGHT'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* 7. Matching Network Preview */}
      <div className="rounded-3xl bg-[#FFFEF9] p-5 sm:p-6 border border-[#E5E0D3] shadow-wealth-card space-y-4">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold uppercase tracking-wider text-[#18211F] flex items-center gap-1.5">
            <GitFork className="w-4 h-4 text-[#063B32]" />
            <span>Matching Network Preview</span>
          </div>
          <Link
            to="/network"
            className="text-xs text-[#063B32] hover:text-[#042C26] font-bold flex items-center gap-1"
          >
            <span>Explore Full Network</span>
            <ChevronRight className="w-4 h-4 text-[#C9A227]" />
          </Link>
        </div>

        {/* Small Visual Binary Subtree */}
        <div className="p-5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] flex flex-col items-center">
          {/* Root Node */}
          <div className="px-4 py-2.5 rounded-2xl bg-[#FFFEF9] border-2 border-[#C9A227] text-center shadow-wealth-gold">
            <div className="text-xs font-bold text-[#18211F]">{treeData?.full_name || user?.full_name}</div>
            <div className="text-[10px] text-[#063B32] font-mono font-bold">YOU ({treeData?.user_code || user?.user_code})</div>
          </div>

          {/* Connectors */}
          <div className="w-32 h-4 border-b-2 border-[#D3CCA9] border-l-2 border-r-2 my-1" />

          {/* Left / Right Children */}
          <div className="w-full flex justify-between gap-3 max-w-xs">
            {/* Left */}
            <div className="flex-1 p-2.5 rounded-xl bg-[#FFFEF9] border border-[#E5E0D3] text-center shadow-2xs">
              <div className="text-[9px] font-bold uppercase text-[#063B32]">Left Leg</div>
              <div className="text-xs font-semibold text-[#18211F] truncate mt-0.5">
                {treeData?.left ? treeData.left.full_name : 'Open Slot'}
              </div>
            </div>

            {/* Right */}
            <div className="flex-1 p-2.5 rounded-xl bg-[#FFFEF9] border border-[#E5E0D3] text-center shadow-2xs">
              <div className="text-[9px] font-bold uppercase text-[#8C6C16]">Right Leg</div>
              <div className="text-xs font-semibold text-[#18211F] truncate mt-0.5">
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

      <PinWalletModal
        isOpen={isPinWalletModalOpen}
        onClose={() => setIsPinWalletModalOpen(false)}
        initialTab={pinWalletTab}
        onSuccess={() => {
          refetchPinWallet();
        }}
      />
    </div>
  );
};


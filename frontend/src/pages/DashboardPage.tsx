import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useOutletContext, Link } from 'react-router-dom';
import api from '../services/api';
import { useToast } from '../context/ToastContext';
import { DashboardData, Commission, BinaryTreeNode } from '../types';
import { CommissionDetailModal } from '../components/modals/CommissionDetailModal';
import { WithdrawalModal } from '../components/modals/WithdrawalModal';
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

  const carryData = data?.carry || data?.carry_summary || kpis?.carry || kpis?.carry_summary;

  const leftCarryCount = carryData?.left?.count ?? carryData?.left?.unpaid_count ?? (Math.floor((kpis?.carry_left_bv || 0) / 30000));
  const leftPaidCount = carryData?.left?.paid_count ?? carryData?.left?.paid_pairs ?? (Math.floor((carryData?.left?.paid || 0) / 30000));
  const leftUnpaidCount = carryData?.left?.unpaid_count ?? carryData?.left?.unpaid_pairs ?? (Math.floor((kpis?.carry_left_bv || 0) / 30000));

  const rightCarryCount = carryData?.right?.count ?? carryData?.right?.unpaid_count ?? (Math.floor((kpis?.carry_right_bv || 0) / 30000));
  const rightPaidCount = carryData?.right?.paid_count ?? carryData?.right?.paid_pairs ?? (Math.floor((carryData?.right?.paid || 0) / 30000));
  const rightUnpaidCount = carryData?.right?.unpaid_count ?? carryData?.right?.unpaid_pairs ?? (Math.floor((kpis?.carry_right_bv || 0) / 30000));

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
            Private Wealth Platform • Binary Network Volume • ₹15,000 Pair Rewards
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${
              user?.is_active
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

      {/* 2. Main Virtual Wealth Card (Visual Centerpiece in Deep Emerald) */}
      <div className="rounded-3xl wealth-hero p-6 sm:p-7 relative overflow-hidden text-[#FFFEF9]">
        <div className="flex items-center justify-between text-[#F7F4EC]/75 mb-2">
          <span className="text-xs font-bold uppercase tracking-widest text-[#C9A227] flex items-center gap-1.5 font-mono">
            <Wallet className="w-4 h-4 text-[#C9A227]" />
            <span>Virtual Wealth Wallet</span>
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
              Eligible for instant virtual payout settlement
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

      {/* 3. Binary Pair Bonus & Carry Forward Engine Card */}
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

      {/* 5. Main Action: BUY ₹35,000 PACKAGE */}
      <button
        onClick={openPurchaseModal}
        className="w-full flex items-center justify-center gap-2.5 py-4 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/40 font-heading font-black text-base shadow-wealth-card transition-all transform hover:scale-[1.01] active:scale-[0.99] cursor-pointer"
      >
        <ShoppingBag className="w-5 h-5 text-[#C9A227]" />
        <span>ACTIVATE ₹35,000 BUSINESS PACKAGE (30,000 BV)</span>
      </button>

      {/* 6. Referral / Invitation Section */}
      <div className="rounded-3xl bg-[#FFFEF9] p-5 sm:p-6 border border-[#E5E0D3] shadow-wealth-card space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold uppercase tracking-wider text-[#18211F] flex items-center gap-1.5">
            <Users className="w-4 h-4 text-[#063B32]" />
            <span>Build Your Network</span>
          </div>
          <span className="text-[10px] text-[#8C6C16] font-bold bg-[#FAF4DC] px-2 py-0.5 rounded-md border border-[#E2C766]/50">
            10% Direct Sponsor Bonus
          </span>
        </div>

        <div className="flex items-center justify-between p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] gap-2">
          <div className="min-w-0 flex-1 pl-1">
            <div className="text-sm font-mono font-black text-[#063B32] tracking-wider truncate">
              {user?.referral_code}
            </div>
            <div className="text-[11px] text-[#69736F] truncate font-mono">
              {referralLink}
            </div>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <button
              onClick={handleCopyReferral}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/30 font-bold text-xs transition-all shadow-sm cursor-pointer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-[#C9A227]" /> : <Copy className="w-3.5 h-3.5 text-[#C9A227]" />}
              <span>{copied ? 'Copied' : 'Copy Invitation'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* 7. Binary Network Preview */}
      <div className="rounded-3xl bg-[#FFFEF9] p-5 sm:p-6 border border-[#E5E0D3] shadow-wealth-card space-y-4">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold uppercase tracking-wider text-[#18211F] flex items-center gap-1.5">
            <GitFork className="w-4 h-4 text-[#063B32]" />
            <span>Binary Network Preview</span>
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
    </div>
  );
};


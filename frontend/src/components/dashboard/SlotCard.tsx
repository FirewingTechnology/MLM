import React from 'react';
import { useTime } from '../../context/TimeContext';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import { RankOverviewResponse } from '../../types';
import { Link } from 'react-router-dom';
import { Clock, Timer, Zap, Star, Sparkles, Award, ArrowRight } from 'lucide-react';

interface SlotCardProps {
  slotEarnings?: number;
  slotCommissionsCount?: number;
}

export const SlotCard: React.FC<SlotCardProps> = ({ slotEarnings = 0, slotCommissionsCount = 0 }) => {
  const { slotInfo, currentDisplayTime, remainingFormatted, remainingSeconds } = useTime();

  // Fetch Rank & Rewards 7-day qualification status
  const { data: rankOverview } = useQuery<RankOverviewResponse>({
    queryKey: ['rankOverview'],
    queryFn: async () => {
      const res = await api.get('/rank-rewards/overview');
      return res.data.data;
    },
    refetchInterval: 10000,
  });

  if (!slotInfo) {
    return (
      <div className="rounded-3xl bg-[#FFFEF9] p-4 border border-[#E5E0D3] animate-pulse shadow-wealth-card">
        <div className="h-16 rounded-2xl bg-[#F7F4EC]" />
      </div>
    );
  }

  // 12-hour slot is 43,200 seconds total
  const totalSlotSeconds = 12 * 3600;
  const elapsedSeconds = Math.max(0, totalSlotSeconds - remainingSeconds);
  const progressPercent = Math.min(100, Math.max(0, (elapsedSeconds / totalSlotSeconds) * 100));

  const isSlot1 = slotInfo.slot_number === 1;

  // Compute 7-day timer display
  const starProg = rankOverview?.tiers?.find(t => t.rank_name === 'STAR');
  const superStarProg = rankOverview?.tiers?.find(t => t.rank_name === 'SUPER_STAR');
  const isStarAchieved = starProg?.status === 'ACHIEVED' || rankOverview?.current_rank === 'STAR' || rankOverview?.current_rank === 'SUPER_STAR' || rankOverview?.current_rank === 'VIP';
  const isSuperStarAchieved = superStarProg?.status === 'ACHIEVED' || rankOverview?.current_rank === 'SUPER_STAR' || rankOverview?.current_rank === 'VIP';

  let sevenDayTitle = '7-DAY STAR TIMER';
  let sevenDaySubtitle = '2 Directs in 7 Days (₹2,100 Award)';
  let sevenDayTime = '';
  let sevenDayBadge = '7-Day Star';
  let sevenDayAchieved = false;

  if (isSuperStarAchieved) {
    sevenDayTitle = 'SUPER STAR ACHIEVED';
    sevenDaySubtitle = 'Rank Level 2 Achieved (₹5,100 Award)';
    sevenDayTime = 'Promoted ⭐⭐';
    sevenDayBadge = 'Super Star';
    sevenDayAchieved = true;
  } else if (isStarAchieved) {
    if (superStarProg && superStarProg.status === 'IN_PROGRESS') {
      const remainingSecs = superStarProg.remaining_seconds || 0;
      const days = Math.floor(remainingSecs / 86400);
      const hours = Math.floor((remainingSecs % 86400) / 3600);
      sevenDayTitle = '7-DAY SUPER STAR TIMER';
      sevenDaySubtitle = '2 Directs must each do 2 (₹5,100 Award)';
      sevenDayTime = `${days}d ${hours}h remaining`;
      sevenDayBadge = 'Super Star Window';
    } else {
      sevenDayTitle = 'STAR RANK ACHIEVED';
      sevenDaySubtitle = 'Level 1 Achieved (₹2,100 Award Credited)';
      sevenDayTime = 'STAR ⭐';
      sevenDayBadge = 'Star Level 1';
      sevenDayAchieved = true;
    }
  } else if (starProg && starProg.status === 'IN_PROGRESS') {
    const remainingSecs = starProg.remaining_seconds || 0;
    const days = Math.floor(remainingSecs / 86400);
    const hours = Math.floor((remainingSecs % 86400) / 3600);
    const activeDirects = starProg.current_count || 0;
    const target = starProg.required_directs || 2;
    sevenDayTitle = '7-DAY STAR TIMER';
    sevenDaySubtitle = `${activeDirects}/${target} Directs • ₹2,100 Award`;
    sevenDayTime = `${days}d ${hours}h left`;
    sevenDayBadge = `${activeDirects}/${target} Directs`;
  } else if (starProg && starProg.status === 'EXPIRED') {
    sevenDayTitle = '7-DAY STAR WINDOW';
    sevenDaySubtitle = 'Initial 7-day qualification period ended';
    sevenDayTime = 'Window Closed';
    sevenDayBadge = 'Expired';
  } else {
    sevenDayTitle = '7-DAY STAR TIMER';
    sevenDaySubtitle = 'Refer 2 Direct in 7 days for ₹2,100 Award';
    sevenDayTime = '7 Days on Activation';
    sevenDayBadge = '₹2,100 Award';
  }

  return (
    <div className="rounded-3xl bg-[#FFFEF9] p-4 sm:p-5 border border-[#E5E0D3] transition-all duration-200 shadow-wealth-card">
      {/* Top Header Row */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          {/* Mode Pill Badge */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#E0F3EE] border border-[#8DCFBF] text-[#063B32] text-[10px] font-extrabold tracking-wider uppercase">
            <span className="w-2 h-2 rounded-full bg-[#0E9F6E] animate-ping" />
            <span>LIVE INDIA TIME</span>
          </div>

          <div className="flex items-center gap-1 text-[11px] font-mono text-[#18211F] font-semibold px-2 py-0.5 rounded-md bg-[#F7F4EC] border border-[#E5E0D3]">
            <Clock className="w-3.5 h-3.5 text-[#69736F]" />
            <span>{currentDisplayTime}</span>
          </div>
        </div>

        {/* Slot ID & 7-Day Badge */}
        <div className="flex items-center gap-2">
          <Link
            to="/rank-rewards"
            className="flex items-center gap-1 text-[10px] font-mono font-bold text-[#8C6C16] bg-[#FAF4DC] px-2.5 py-0.5 rounded-lg border border-[#E2C766]/60 hover:bg-[#F4E7B4] transition-colors"
            title="View 7-Day Rank & Reward Qualification"
          >
            <Star className="w-3 h-3 text-[#C9A227] fill-[#C9A227]" />
            <span>{sevenDayBadge}</span>
          </Link>
          <div className="text-[11px] font-mono font-bold text-[#8C6C16] bg-[#FAF4DC] px-2.5 py-0.5 rounded-lg border border-[#E2C766]/50">
            {slotInfo.slot_id}
          </div>
        </div>
      </div>

      {/* Main Grid: Slot & Countdowns */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 sm:gap-4 items-center">
        {/* Left Col: Current Slot (5 cols) */}
        <div className="lg:col-span-5 space-y-1">
          <div className="flex items-center gap-2.5">
            <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-heading font-black text-xs shadow-sm shrink-0 ${
              isSlot1 
                ? 'bg-[#063B32] text-[#E2C766] border border-[#C9A227]/40' 
                : 'bg-[#8C6C16] text-[#FFFEF9]'
            }`}>
              {isSlot1 ? 'S1' : 'S2'}
            </div>
            <div>
              <div className="text-sm sm:text-base font-heading font-extrabold text-[#18211F] tracking-tight flex items-center gap-2">
                <span>{slotInfo.slot_name}</span>
                <span className="text-[11px] font-semibold text-[#69736F] font-mono">
                  ({slotInfo.slot_start_formatted} → {slotInfo.slot_end_formatted})
                </span>
              </div>
              <div className="text-[10px] text-[#69736F] font-medium">
                12-Hour India Standard Time Distribution Cycle
              </div>
            </div>
          </div>
        </div>

        {/* Right Col: Timers Box (7 cols) - 12h Slot Countdown + 7-Day Rank Qualification Countdown */}
        <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {/* 1. 12-Hour Slot Countdown */}
          <div className="flex sm:flex-col items-center sm:items-start justify-between sm:justify-center p-2.5 px-3 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3]">
            <div className="text-[10px] uppercase font-bold tracking-wider text-[#69736F] flex items-center gap-1">
              <Timer className="w-3.5 h-3.5 text-[#063B32]" />
              <span>Slot Ends In</span>
            </div>
            <div className="text-base sm:text-lg font-heading font-black font-mono tracking-tight text-[#18211F]">
              {remainingFormatted}
            </div>
          </div>

          {/* 2. 7-Day Star / Super Star Rank Qualification Window */}
          <Link
            to="/rank-rewards"
            className="flex sm:flex-col items-center sm:items-start justify-between sm:justify-center p-2.5 px-3 rounded-2xl bg-gradient-to-br from-[#FFFDF2] to-[#FAF4DC] border border-[#E2C766] hover:border-[#C9A227] transition-all group"
          >
            <div className="text-[10px] uppercase font-bold tracking-wider text-[#8C6C16] flex items-center gap-1">
              {sevenDayAchieved ? (
                <Sparkles className="w-3.5 h-3.5 text-[#C9A227]" />
              ) : (
                <Star className="w-3.5 h-3.5 text-[#C9A227] fill-[#C9A227]/40" />
              )}
              <span className="truncate">{sevenDayTitle}</span>
            </div>
            <div className="flex items-center gap-1 text-sm sm:text-base font-heading font-black font-mono tracking-tight text-[#063B32] group-hover:text-[#C9A227] transition-colors">
              <span>{sevenDayTime || '7-Day Window'}</span>
              <ArrowRight className="w-3 h-3 text-[#8C6C16] opacity-60 group-hover:translate-x-0.5 transition-transform" />
            </div>
            <div className="hidden sm:block text-[9px] text-[#8C6C16] font-medium truncate max-w-full">
              {sevenDaySubtitle}
            </div>
          </Link>
        </div>
      </div>

      {/* Progress Bar with Gold styling */}
      <div className="mt-3">
        <div className="w-full h-2 bg-[#EFECE2] rounded-full overflow-hidden">
          <div 
            className="h-full transition-all duration-1000 ease-linear rounded-full bg-gradient-to-r from-[#C9A227] to-[#E2C766]"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <div className="flex justify-between items-center text-[10px] font-mono text-[#69736F] mt-1">
          <span>{slotInfo.slot_start_formatted} IST</span>
          <span className="font-semibold text-[#063B32]">{progressPercent.toFixed(1)}% Cycle Elapsed</span>
          <span>{slotInfo.slot_end_formatted} IST</span>
        </div>
      </div>

      {/* Slot Earnings / Activity Footer */}
      {(slotEarnings > 0 || slotCommissionsCount > 0) && (
        <div className="mt-3 pt-2.5 border-t border-[#EFECE2] flex items-center justify-between text-xs font-medium">
          <div className="text-[#69736F] flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-[#C9A227]" />
            <span>Earned This Slot:</span>
          </div>
          <div className="text-[#063B32] font-mono font-bold">
            +₹{slotEarnings.toLocaleString()} ({slotCommissionsCount} {slotCommissionsCount === 1 ? 'payout' : 'payouts'})
          </div>
        </div>
      )}
    </div>
  );
};

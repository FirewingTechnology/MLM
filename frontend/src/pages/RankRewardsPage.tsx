import React from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { RankOverviewResponse, RankTierProgress } from '../types';
import { 
  Award, 
  Star, 
  Sparkles, 
  Crown, 
  Clock, 
  CheckCircle2, 
  Lock, 
  AlertCircle, 
  Users, 
  ArrowRight, 
  ShieldCheck, 
  HelpCircle,
  TrendingUp,
  Zap,
  Bike
} from 'lucide-react';

export const RankRewardsPage: React.FC = () => {
  const { data: rankData, isLoading, error } = useQuery<RankOverviewResponse>({
    queryKey: ['rankOverview'],
    queryFn: async () => {
      const res = await api.get('/rank-rewards/overview');
      return res.data.data;
    },
    refetchInterval: 10000,
  });

  const getRankBadge = (rank: string) => {
    switch (rank) {
      case 'STAR':
        return {
          label: 'STAR',
          icon: Star,
          color: 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766]',
          badgeText: 'Level 1 Achiever',
          shimmer: true
        };
      case 'SUPER_STAR':
        return {
          label: 'SUPER STAR',
          icon: Sparkles,
          color: 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]',
          badgeText: 'Level 2 Leader',
          shimmer: true
        };
      case 'VIP':
        return {
          label: 'VIP',
          icon: Crown,
          color: 'bg-[#FAF4DC] text-[#C9A227] border-[#C9A227]',
          badgeText: 'Elite VIP Crown',
          shimmer: true
        };
      default:
        return {
          label: 'DISTRIBUTOR',
          icon: Award,
          color: 'bg-[#F7F4EC] text-[#69736F] border-[#E5E0D3]',
          badgeText: 'Independent Partner',
          shimmer: false
        };
    }
  };

  const formatRemainingTime = (seconds: number) => {
    if (seconds <= 0) return 'Window Closed';
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    if (days > 0) {
      return `${days}d ${hours}h ${mins}m remaining`;
    }
    return `${hours}h ${mins}m remaining`;
  };

  if (isLoading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center gap-3">
        <div className="w-10 h-10 rounded-full border-2 border-[#063B32] border-t-[#C9A227] animate-spin" />
        <div className="text-xs text-[#69736F] font-medium font-mono">Loading Rank & Rewards System...</div>
      </div>
    );
  }

  const currentRankInfo = getRankBadge(rankData?.current_rank || 'DISTRIBUTOR');
  const RankIcon = currentRankInfo.icon;

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* 1. Page Header & Current Rank Hero */}
      <div className="rounded-3xl bg-[#063B32] text-[#FFFEF9] p-6 sm:p-8 border border-[#042C26] shadow-2xl relative overflow-hidden">
        {/* Subtle decorative background glow */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#C9A227]/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#0A4D42] border border-[#C9A227]/30 text-[#E2C766] text-xs font-bold uppercase tracking-wider">
              <Award className="w-3.5 h-3.5" />
              <span>Achievement & Milestone Hierarchy</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-heading font-extrabold tracking-tight text-[#FFFEF9]">
              Rank & Rewards Program
            </h1>
            <p className="text-xs sm:text-sm text-[#F7F4EC]/80 font-medium">
              Accelerate your leadership with 7-day direct sponsorship sprints. Earn ₹2,100 Star bonus, ₹5,100 Super Star bonus, and ₹51,000 Cash or EV Scooter VIP award.
            </p>
          </div>

          {/* Current Rank Badge Card */}
          <div className="p-5 rounded-2xl bg-[#042C26] border border-[#C9A227]/40 shadow-wealth-gold flex items-center gap-4 shrink-0 backdrop-blur-md">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#C9A227] to-[#8C6C16] flex items-center justify-center text-[#FFFEF9] shadow-lg shrink-0">
              <RankIcon className="w-7 h-7" />
            </div>
            <div>
              <div className="text-[10px] font-mono uppercase font-bold text-[#E2C766] tracking-widest">
                Current Standing
              </div>
              <div className="text-xl font-heading font-black text-[#FFFEF9]">
                {currentRankInfo.label}
              </div>
              <div className="text-xs text-[#F7F4EC]/70 font-medium mt-0.5">
                {currentRankInfo.badgeText}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Three Tiers Hierarchy Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {rankData?.tiers.map((tier: RankTierProgress) => {
          const isStar = tier.rank_name === 'STAR';
          const isSuperStar = tier.rank_name === 'SUPER_STAR';
          const isVIP = tier.rank_name === 'VIP';
          const isAchieved = tier.status === 'ACHIEVED';
          const isInProgress = tier.status === 'IN_PROGRESS';
          const isExpired = tier.status === 'EXPIRED';
          const isLocked = tier.status === 'LOCKED';

          const TierIcon = isStar ? Star : isSuperStar ? Sparkles : Crown;

          return (
            <div
              key={tier.rank_name}
              className={`rounded-3xl p-5 sm:p-6 transition-all duration-200 flex flex-col justify-between relative bg-[#FFFEF9] border ${
                isAchieved
                  ? 'border-[#C9A227] ring-2 ring-[#FAF4DC] shadow-wealth-gold'
                  : isInProgress
                  ? 'border-[#063B32] shadow-wealth-elevated'
                  : 'border-[#E5E0D3] shadow-wealth-card opacity-90'
              }`}
            >
              {/* Card Header */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold ${
                        isAchieved
                          ? 'bg-[#063B32] text-[#E2C766] border border-[#C9A227]/40 shadow-xs'
                          : isInProgress
                          ? 'bg-[#E0F3EE] text-[#063B32]'
                          : 'bg-[#F7F4EC] text-[#69736F]'
                      }`}
                    >
                      <TierIcon className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#8C6C16]">
                        Level {tier.level}
                      </span>
                      <h3 className="text-lg font-heading font-extrabold text-[#18211F] leading-tight">
                        {tier.display_name}
                      </h3>
                    </div>
                  </div>

                  {/* Status Badge */}
                  <span
                    className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border ${
                      isAchieved
                        ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
                        : isInProgress
                        ? 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766] animate-pulse'
                        : isExpired
                        ? 'bg-[#FDF2F2] text-[#C94B4B] border-[#F8B4B4]'
                        : 'bg-[#F7F4EC] text-[#69736F] border-[#E5E0D3]'
                    }`}
                  >
                    {isAchieved
                      ? '● Achieved'
                      : isInProgress
                      ? '● In Progress'
                      : isExpired
                      ? '● Expired'
                      : '● Locked'}
                  </span>
                </div>

                {/* Requirement Description */}
                <div className="p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-xs space-y-1">
                  <div className="text-[10px] uppercase font-bold text-[#69736F]">Qualification Sprint</div>
                  <div className="font-semibold text-[#18211F]">
                    {isStar && 'Personally refer 2 direct partners within 7 days.'}
                    {isSuperStar && 'Your 2 qualifying directs each complete 2 directs (Star) in 7 days.'}
                    {isVIP && 'Your 2 qualifying directs both achieve Super Star in 7 days.'}
                  </div>
                </div>

                {/* Reward Highlight Banner */}
                <div className="p-3.5 rounded-2xl bg-[#FAF4DC]/70 border border-[#E2C766]/60 text-xs flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {tier.reward_type === 'EV_SCOOTER' ? (
                      <Bike className="w-4 h-4 text-[#8C6C16]" />
                    ) : (
                      <Award className="w-4 h-4 text-[#C9A227]" />
                    )}
                    <div>
                      <div className="text-[10px] uppercase font-bold text-[#8C6C16]">Award</div>
                      <div className="font-black text-[#18211F] text-sm">
                        {tier.reward_type === 'EV_SCOOTER' ? 'EV Scooter' : `₹${tier.reward_amount.toLocaleString()}`}
                      </div>
                    </div>
                  </div>

                  {/* Reward Status Pill */}
                  <div className="text-right">
                    {tier.reward_status === 'CREDITED' && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#063B32] bg-[#E0F3EE] px-2 py-0.5 rounded-md border border-[#8DCFBF]">
                        <CheckCircle2 className="w-3 h-3 text-[#063B32]" />
                        Wallet Credited
                      </span>
                    )}
                    {tier.reward_status === 'PENDING_FULFILLMENT' && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#8C6C16] bg-[#FAF4DC] px-2 py-0.5 rounded-md border border-[#E2C766]">
                        Delivery Pending
                      </span>
                    )}
                    {tier.reward_status === 'FULFILLED' && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#063B32] bg-[#E0F3EE] px-2 py-0.5 rounded-md border border-[#8DCFBF]">
                        <CheckCircle2 className="w-3 h-3 text-[#063B32]" />
                        Fulfilled
                      </span>
                    )}
                    {tier.reward_status === 'PENDING' && !isAchieved && (
                      <span className="text-[10px] font-medium text-[#69736F]">
                        Upon Completion
                      </span>
                    )}
                  </div>
                </div>

                {/* Progress Bar & Counter */}
                <div className="space-y-1.5 pt-1">
                  <div className="flex items-center justify-between text-xs font-mono font-bold">
                    <span className="text-[#69736F] font-sans font-medium text-[11px]">
                      {isStar ? 'Direct Referrals' : isSuperStar ? 'Direct Stars' : 'Direct Super Stars'}
                    </span>
                    <span className="text-[#063B32]">
                      {tier.current_count} / {tier.required_directs}
                    </span>
                  </div>
                  <div className="w-full h-2.5 rounded-full bg-[#E5E0D3] overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-[#063B32] to-[#C9A227] transition-all duration-300 rounded-full"
                      style={{ width: `${tier.progress_percentage}%` }}
                    />
                  </div>
                </div>

                {/* Contributing Members Breakdown */}
                {tier.qualifying_members && tier.qualifying_members.length > 0 && (
                  <div className="pt-2 border-t border-[#EFECE2]">
                    <div className="text-[10px] uppercase font-bold text-[#69736F] mb-1.5 flex items-center gap-1">
                      <Users className="w-3 h-3 text-[#063B32]" />
                      <span>Contributing Partners ({tier.qualifying_members.length})</span>
                    </div>
                    <div className="space-y-1">
                      {tier.qualifying_members.map((m) => (
                        <div
                          key={m.id}
                          className="flex items-center justify-between p-2 rounded-xl bg-[#F7F4EC] text-xs"
                        >
                          <span className="font-bold text-[#18211F] truncate max-w-[140px]">{m.full_name}</span>
                          <span className="text-[10px] font-mono font-bold text-[#063B32] bg-[#E0F3EE] px-1.5 py-0.5 rounded border border-[#8DCFBF]">
                            {m.user_code}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Card Footer: Timers & Dates */}
              <div className="pt-4 mt-4 border-t border-[#EFECE2] text-[11px] font-mono">
                {isAchieved ? (
                  <div className="flex items-center justify-between text-[#063B32] font-bold">
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Promoted</span>
                    </span>
                    <span className="text-[10px]">
                      {tier.achieved_at ? new Date(tier.achieved_at).toLocaleDateString() : 'Achieved'}
                    </span>
                  </div>
                ) : isInProgress ? (
                  <div className="flex items-center justify-between text-[#8C6C16] font-bold">
                    <span className="flex items-center gap-1 font-sans text-xs">
                      <Clock className="w-3.5 h-3.5 text-[#C9A227] animate-spin" />
                      <span>Deadline:</span>
                    </span>
                    <span className="text-[11px]">
                      {formatRemainingTime(tier.remaining_seconds)}
                    </span>
                  </div>
                ) : isExpired ? (
                  <div className="flex items-center justify-between text-[#C94B4B] font-bold">
                    <span className="flex items-center gap-1 font-sans text-xs">
                      <AlertCircle className="w-3.5 h-3.5" />
                      <span>7-Day Cutoff Passed</span>
                    </span>
                    <span className="text-[10px]">Expired</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-between text-[#69736F]">
                    <span className="flex items-center gap-1 font-sans text-xs">
                      <Lock className="w-3.5 h-3.5" />
                      <span>Unlock with Level {tier.level - 1}</span>
                    </span>
                    <span>Locked</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* 3. Program Rule Summary Guide */}
      <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card space-y-4">
        <div className="flex items-center gap-2 text-sm font-bold text-[#18211F]">
          <HelpCircle className="w-4 h-4 text-[#C9A227]" />
          <span>Rank & Reward Policy & Rules</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-[#69736F] divide-y md:divide-y-0 md:divide-x divide-[#EFECE2]">
          <div className="space-y-1.5 pr-2">
            <div className="font-bold text-[#18211F] flex items-center gap-1">
              <Star className="w-3.5 h-3.5 text-[#C9A227]" />
              <span>Level 1 — Star Sprint</span>
            </div>
            <p>
              Starts automatically from your registration/activation. Sponsor 2 personal direct members within 7 days to qualify for Star rank and earn ₹2,100 instantly.
            </p>
          </div>

          <div className="space-y-1.5 pt-3 md:pt-0 md:px-4">
            <div className="font-bold text-[#18211F] flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-[#063B32]" />
              <span>Level 2 — Super Star Sprint</span>
            </div>
            <p>
              Empower your 2 qualifying direct members to each achieve Star within 7 days. Once both achieve Star rank, you advance to Super Star and receive ₹5,100.
            </p>
          </div>

          <div className="space-y-1.5 pt-3 md:pt-0 md:pl-4">
            <div className="font-bold text-[#18211F] flex items-center gap-1">
              <Crown className="w-3.5 h-3.5 text-[#C9A227]" />
              <span>Level 3 — VIP Crown</span>
            </div>
            <p>
              When your 2 qualifying direct members achieve Super Star rank within their 7-day sprint, you are promoted to VIP and receive the configured ₹51,000 Cash or EV Scooter award.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

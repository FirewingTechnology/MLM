import React from 'react';
import { useTime } from '../../context/TimeContext';
import { Clock, Timer, Zap } from 'lucide-react';

interface SlotCardProps {
  slotEarnings?: number;
  slotCommissionsCount?: number;
}

export const SlotCard: React.FC<SlotCardProps> = ({ slotEarnings = 0, slotCommissionsCount = 0 }) => {
  const { slotInfo, currentDisplayTime, remainingFormatted, remainingSeconds } = useTime();

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

  return (
    <div className="rounded-3xl bg-[#FFFEF9] p-4 sm:p-5 border border-[#E5E0D3] transition-all duration-200 shadow-wealth-card">
      {/* Top Header Row */}
      <div className="flex items-center justify-between gap-2 mb-3">
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

        {/* Slot ID Badge */}
        <div className="text-[11px] font-mono font-bold text-[#8C6C16] bg-[#FAF4DC] px-2.5 py-0.5 rounded-lg border border-[#E2C766]/50">
          {slotInfo.slot_id}
        </div>
      </div>

      {/* Main Grid: Slot & Countdown */}
      <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 sm:gap-4 items-center">
        {/* Left Col: Current Slot (7 cols) */}
        <div className="sm:col-span-7 space-y-1">
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

        {/* Right Col: Live Countdown (5 cols) */}
        <div className="sm:col-span-5 flex sm:flex-col items-center sm:items-end justify-between sm:justify-center p-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3]">
          <div className="text-[10px] uppercase font-bold tracking-wider text-[#69736F] flex items-center gap-1">
            <Timer className="w-3.5 h-3.5 text-[#063B32]" />
            <span>Slot Ends In</span>
          </div>
          <div className="text-lg sm:text-xl font-heading font-black font-mono tracking-tight text-[#18211F]">
            {remainingFormatted}
          </div>
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


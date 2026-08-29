import React from 'react';
import { AlertTriangle, Clock } from 'lucide-react';
import { useTime } from '../../context/TimeContext';

export const DemoBanner: React.FC = () => {
  const { slotInfo, currentDisplayTime, isDemoMode } = useTime();

  return (
    <div className={`border-b px-4 py-1 text-xs font-medium flex items-center justify-between transition-colors duration-200 ${
      isDemoMode 
        ? 'bg-[#FAF4DC] border-[#E2C766]/60 text-[#8C6C16]' 
        : 'bg-[#EFECE2] border-[#E5E0D3] text-[#69736F]'
    }`}>
      {/* Left / Center Message */}
      <div className="flex items-center gap-2">
        <AlertTriangle className="w-3.5 h-3.5 text-[#C88A16] shrink-0" />
        <span className="tracking-wider uppercase font-bold text-[#8C6C16] text-[10px]">DEMO SANDBOX</span>
        <span className="hidden md:inline text-[#69736F]/50">—</span>
        <span className="hidden md:inline text-[#69736F] text-[11px]">100% Virtual Wealth Simulator (Virtual ₹35,000 Package, 30,000 BV & ₹10,000 Pair Bonus).</span>
      </div>

      {/* Right Slot Indicator */}
      {slotInfo && (
        <div className="flex items-center gap-2">
          {isDemoMode ? (
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#FFFEF9] text-[#8C6C16] border border-[#E2C766] font-mono text-[10px] font-bold">
              <span className="w-1.5 h-1.5 rounded-full bg-[#C88A16] animate-pulse" />
              <span>DEMO TIME: {currentDisplayTime} ({slotInfo.slot_name})</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#E0F3EE] text-[#063B32] border border-[#8DCFBF] font-mono text-[10px] font-bold">
              <span className="w-1.5 h-1.5 rounded-full bg-[#0E9F6E] animate-ping" />
              <span>LIVE IST: {currentDisplayTime} ({slotInfo.slot_name})</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};



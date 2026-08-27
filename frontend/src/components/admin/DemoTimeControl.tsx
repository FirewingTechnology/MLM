import React, { useState, useEffect } from 'react';
import { useTime } from '../../context/TimeContext';
import { useToast } from '../../context/ToastContext';
import { 
  Clock, 
  RotateCcw, 
  FastForward, 
  Rewind, 
  Calendar, 
  Check, 
  Radio, 
  Zap, 
  Sparkles,
  Sliders,
  ChevronRight
} from 'lucide-react';

export const DemoTimeControl: React.FC = () => {
  const { 
    slotInfo, 
    isDemoMode, 
    currentDisplayTime, 
    remainingFormatted, 
    setMode, 
    setExactTime, 
    advanceTime, 
    nextSlot, 
    previousSlot, 
    resetToRealTime 
  } = useTime();

  const { showToast } = useToast();

  const [customDate, setCustomDate] = useState<string>('');
  const [customTime, setCustomTime] = useState<string>('11:55');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // Initialize date picker with current slot date
  useEffect(() => {
    if (slotInfo?.date) {
      setCustomDate(slotInfo.date);
    }
  }, [slotInfo?.date]);

  const handleModeSwitch = async (newMode: 'REAL' | 'DEMO') => {
    try {
      setIsSubmitting(true);
      await setMode(newMode);
      showToast(newMode === 'REAL' ? 'Switched to LIVE REAL IST mode!' : 'Switched to DEMO TIME mode!', 'success');
    } catch (err: any) {
      showToast(err.response?.data?.error?.message || 'Failed to switch time mode', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSetExactTime = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customDate || !customTime) {
      showToast('Please enter both date and time', 'error');
      return;
    }

    try {
      setIsSubmitting(true);
      const combined = `${customDate}T${customTime}:00`;
      const res = await setExactTime(combined);
      showToast(`Demo time set to ${res.date} ${res.time_formatted} (${res.slot_name})`, 'success');
    } catch (err: any) {
      showToast(err.response?.data?.error?.message || 'Failed to set virtual time', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAdvance = async (minutes: number, label: string) => {
    try {
      setIsSubmitting(true);
      const res = await advanceTime(minutes);
      showToast(`Clock advanced by ${label} → ${res.time_formatted} (${res.slot_name})`, 'success');
    } catch (err: any) {
      showToast(err.response?.data?.error?.message || 'Failed to advance time', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNextSlot = async () => {
    try {
      setIsSubmitting(true);
      const res = await nextSlot();
      showToast(`Jumped to Next Slot: ${res.slot_name} (${res.slot_id}) at ${res.time_formatted}`, 'success');
    } catch (err: any) {
      showToast(err.response?.data?.error?.message || 'Failed to jump to next slot', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePreviousSlot = async () => {
    try {
      setIsSubmitting(true);
      const res = await previousSlot();
      showToast(`Jumped to Previous Slot: ${res.slot_name} (${res.slot_id}) at ${res.time_formatted}`, 'success');
    } catch (err: any) {
      showToast(err.response?.data?.error?.message || 'Failed to jump to previous slot', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetToReal = async () => {
    try {
      setIsSubmitting(true);
      await resetToRealTime();
      showToast('Demo clock reset! Live India Standard Time resumed.', 'success');
    } catch (err: any) {
      showToast(err.response?.data?.error?.message || 'Failed to reset time', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rounded-3xl bg-[#FFFEF9] p-5 sm:p-6 border border-[#E5E0D3] shadow-wealth-card relative overflow-hidden text-[#18211F]">
      {/* Header & Mode Switch */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#E5E0D3]">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-[#8C6C16]">
            <Sliders className="w-4 h-4 text-[#C9A227]" />
            <span>DEMO TIME ENGINE & CYCLE CONTROL</span>
            <span className="text-[10px] bg-[#FAF4DC] text-[#8C6C16] px-2 py-0.5 rounded-full border border-[#E2C766]/60 font-bold">
              Server-Side
            </span>
          </div>
          <div className="text-sm text-[#69736F] font-medium mt-0.5">
            Manually simulate 12-hour MLM cycle transitions across all connected clients.
          </div>
        </div>

        {/* Mode Toggle Pills */}
        <div className="flex items-center p-1 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] self-start sm:self-auto">
          <button
            type="button"
            disabled={isSubmitting}
            onClick={() => handleModeSwitch('REAL')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              !isDemoMode 
                ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs' 
                : 'text-[#69736F] hover:text-[#18211F]'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${!isDemoMode ? 'bg-[#0E9F6E]' : 'bg-[#69736F]'}`} />
            <span>REAL TIME</span>
          </button>
          <button
            type="button"
            disabled={isSubmitting}
            onClick={() => handleModeSwitch('DEMO')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              isDemoMode 
                ? 'bg-[#C88A16] text-[#FFFEF9] shadow-xs' 
                : 'text-[#69736F] hover:text-[#18211F]'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${isDemoMode ? 'bg-[#FFFEF9]' : 'bg-[#69736F]'}`} />
            <span>DEMO TIME</span>
          </button>
        </div>
      </div>

      {/* Current System State Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-4">
        <div className="p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3]">
          <div className="text-[10px] uppercase font-bold text-[#69736F] tracking-wider">Clock Status</div>
          <div className="text-sm font-heading font-extrabold mt-0.5 flex items-center gap-1.5">
            {isDemoMode ? (
              <span className="text-[#8C6C16] flex items-center gap-1 font-bold">
                <span className="w-2 h-2 rounded-full bg-[#C88A16] animate-pulse" />
                DEMO TIME
              </span>
            ) : (
              <span className="text-[#063B32] flex items-center gap-1 font-bold">
                <span className="w-2 h-2 rounded-full bg-[#0E9F6E] animate-ping" />
                LIVE IST
              </span>
            )}
          </div>
        </div>

        <div className="p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3]">
          <div className="text-[10px] uppercase font-bold text-[#69736F] tracking-wider">India Time (IST)</div>
          <div className="text-sm font-bold font-mono text-[#18211F] mt-0.5 truncate">
            {currentDisplayTime}
          </div>
        </div>

        <div className="p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3]">
          <div className="text-[10px] uppercase font-bold text-[#69736F] tracking-wider">Current Slot</div>
          <div className="text-sm font-extrabold text-[#063B32] mt-0.5 font-mono">
            {slotInfo?.slot_name} ({slotInfo?.slot_id})
          </div>
        </div>

        <div className="p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3]">
          <div className="text-[10px] uppercase font-bold text-[#69736F] tracking-wider">Time Remaining</div>
          <div className="text-sm font-bold font-mono text-[#18211F] mt-0.5">
            {remainingFormatted}
          </div>
        </div>
      </div>

      {/* Manual Controls Grid */}
      <div className="space-y-4 pt-1">
        {/* Step 1: Set Exact Virtual Date & Time */}
        <form onSubmit={handleSetExactTime} className="p-4 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3]">
          <div className="text-xs font-heading font-bold text-[#18211F] mb-2 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-[#C9A227]" />
            <span>Set Exact Virtual India Time</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            <div>
              <label className="block text-[10px] font-mono text-[#69736F] uppercase tracking-wider mb-1">Date</label>
              <input
                type="date"
                value={customDate}
                onChange={(e) => setCustomDate(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-[#FFFEF9] border border-[#E5E0D3] text-xs font-mono text-[#18211F] focus:outline-none focus:border-[#063B32]"
                required
              />
            </div>
            <div>
              <label className="block text-[10px] font-mono text-[#69736F] uppercase tracking-wider mb-1">Time (24h or HH:MM)</label>
              <input
                type="time"
                value={customTime}
                onChange={(e) => setCustomTime(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-[#FFFEF9] border border-[#E5E0D3] text-xs font-mono text-[#18211F] focus:outline-none focus:border-[#063B32]"
                required
              />
            </div>
            <div className="flex items-end">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2.5 px-4 rounded-xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/40 font-heading font-bold text-xs shadow-xs transition-all disabled:opacity-50 cursor-pointer"
              >
                {isSubmitting ? 'Updating...' : 'SET TIME'}
              </button>
            </div>
          </div>
        </form>

        {/* Step 2: Step Forward Buttons */}
        <div className="p-4 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3]">
          <div className="text-xs font-heading font-bold text-[#18211F] mb-2 flex items-center gap-1.5">
            <FastForward className="w-3.5 h-3.5 text-[#063B32]" />
            <span>Quick Advance Controls (Forward In Time)</span>
          </div>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
            {[
              { mins: 1, label: '+1 MIN' },
              { mins: 5, label: '+5 MIN' },
              { mins: 30, label: '+30 MIN' },
              { mins: 60, label: '+1 HOUR' },
              { mins: 360, label: '+6 HOURS' },
              { mins: 720, label: '+12 HOURS' },
            ].map((btn) => (
              <button
                key={btn.mins}
                type="button"
                disabled={isSubmitting}
                onClick={() => handleAdvance(btn.mins, btn.label)}
                className="py-2.5 px-2 rounded-xl bg-[#FFFEF9] hover:bg-[#FAF4DC] hover:border-[#C9A227] text-[#18211F] border border-[#E5E0D3] text-xs font-black font-mono transition-all transform active:scale-95 text-center shadow-xs cursor-pointer"
              >
                {btn.label}
              </button>
            ))}
          </div>
        </div>

        {/* Step 3: Slot Boundary Jump & Reset Actions */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          <button
            type="button"
            disabled={isSubmitting}
            onClick={handlePreviousSlot}
            className="py-3 px-3 rounded-2xl bg-[#FFFEF9] hover:bg-[#EFECE2] text-[#18211F] border border-[#E5E0D3] text-xs font-heading font-bold flex items-center justify-center gap-2 transition-all active:scale-95 shadow-xs cursor-pointer"
          >
            <Rewind className="w-4 h-4 text-[#69736F]" />
            <span>PREVIOUS SLOT</span>
          </button>

          <button
            type="button"
            disabled={isSubmitting}
            onClick={handleNextSlot}
            className="py-3 px-3 rounded-2xl bg-[#FAF4DC] hover:bg-[#F2E8C4] text-[#8C6C16] border border-[#E2C766] text-xs font-heading font-bold flex items-center justify-center gap-2 transition-all active:scale-95 shadow-xs cursor-pointer"
          >
            <FastForward className="w-4 h-4 text-[#C9A227]" />
            <span>NEXT SLOT</span>
          </button>

          <button
            type="button"
            disabled={isSubmitting}
            onClick={handleResetToReal}
            className="py-3 px-3 rounded-2xl bg-[#E0F3EE] hover:bg-[#CBECE3] text-[#063B32] border border-[#8DCFBF] text-xs font-heading font-bold flex items-center justify-center gap-2 transition-all active:scale-95 shadow-xs cursor-pointer"
          >
            <RotateCcw className="w-4 h-4 text-[#063B32]" />
            <span>RESET TO REAL TIME</span>
          </button>
        </div>
      </div>
    </div>
  );
};


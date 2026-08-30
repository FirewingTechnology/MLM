import React, { useState } from 'react';
import { useTime } from '../../context/TimeContext';
import { useToast } from '../../context/ToastContext';
import api from '../../services/api';
import { 
  Clock, 
  Calendar, 
  Database, 
  ShieldCheck, 
  Download, 
  Sparkles, 
  ArrowUpRight,
  Activity,
  CheckCircle2,
  Loader2
} from 'lucide-react';

interface LiveSystemClockProps {
  onBackupCreated?: () => void;
}

export const LiveSystemClock: React.FC<LiveSystemClockProps> = ({ onBackupCreated }) => {
  const { slotInfo, currentDisplayTime } = useTime();
  const { showToast } = useToast();
  const [isBackingUp, setIsBackingUp] = useState(false);

  const handleCreateSnapshot = async () => {
    setIsBackingUp(true);
    try {
      const res = await api.post('/admin/system/backup', { notes: 'Live Admin Dashboard Snapshot' });
      if (res.data?.success) {
        showToast(`Snapshot created: ${res.data.data.filename} (${res.data.data.size_mb} MB)`, 'success');
        if (onBackupCreated) onBackupCreated();
      } else {
        showToast(res.data?.error?.message || 'Failed to create database snapshot.', 'error');
      }
    } catch (err: any) {
      showToast(err.response?.data?.error?.message || 'Failed to create backup.', 'error');
    } finally {
      setIsBackingUp(false);
    }
  };

  if (!slotInfo) return null;

  const isSlot1 = slotInfo.slot_number === 1;

  return (
    <div className="rounded-3xl bg-[#FFFEF9] p-5 sm:p-6 border border-[#E5E0D3] shadow-wealth-card relative overflow-hidden text-[#18211F]">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-5 border-b border-[#E5E0D3]">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-[#063B32]">
            <Activity className="w-4 h-4 text-[#0E9F6E]" />
            <span>LIVE SYSTEM CLOCK & 12-HOUR CYCLE STATUS</span>
            <span className="text-[10px] bg-[#E0F3EE] text-[#063B32] px-2.5 py-0.5 rounded-full border border-[#8DCFBF] font-extrabold flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#0E9F6E] animate-ping" />
              AUTHORITATIVE IST
            </span>
          </div>
          <p className="text-xs sm:text-sm text-[#69736F] font-medium mt-1">
            Server-side real-time calculation engine with automatic dual-slot settlement (12 AM & 12 PM IST).
          </p>
        </div>

        {/* Instant Backup Snapshot CTA */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCreateSnapshot}
            disabled={isBackingUp}
            className="flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-[#F7F4EC] hover:bg-[#EFECE2] text-[#063B32] border border-[#E5E0D3] text-xs font-bold transition-all shadow-xs cursor-pointer disabled:opacity-50"
          >
            {isBackingUp ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin text-[#063B32]" />
                <span>Creating Snapshot...</span>
              </>
            ) : (
              <>
                <Database className="w-3.5 h-3.5 text-[#063B32]" />
                <span>Create Live DB Snapshot</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Grid: Clock & Slot Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-5">
        {/* Card 1: Real India Time */}
        <div className="p-4 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase font-bold text-[#69736F] flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-[#063B32]" />
              <span>Current Server Time</span>
            </div>
            <div className="text-xl sm:text-2xl font-mono font-black text-[#18211F] mt-1">
              {currentDisplayTime || slotInfo.time_formatted}
            </div>
            <div className="text-[11px] text-[#69736F] font-medium mt-0.5">
              {slotInfo.date} • IST (UTC+05:30)
            </div>
          </div>
          <div className="w-10 h-10 rounded-2xl bg-[#E0F3EE] border border-[#8DCFBF] flex items-center justify-center text-[#063B32] shrink-0">
            <CheckCircle2 className="w-5 h-5 text-[#0E9F6E]" />
          </div>
        </div>

        {/* Card 2: Active Distribution Cycle */}
        <div className="p-4 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase font-bold text-[#69736F] flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-[#C9A227]" />
              <span>Active Cycle</span>
            </div>
            <div className="text-xl sm:text-2xl font-mono font-black text-[#8C6C16] mt-1">
              {slotInfo.slot_name}
            </div>
            <div className="text-[11px] text-[#69736F] font-mono mt-0.5">
              {slotInfo.slot_start_formatted} – {slotInfo.slot_end_formatted} ({slotInfo.slot_id})
            </div>
          </div>
          <div className="px-3 py-1.5 rounded-xl bg-[#FAF4DC] border border-[#E2C766]/60 text-xs font-mono font-bold text-[#8C6C16]">
            Cycle #{slotInfo.slot_number}
          </div>
        </div>

        {/* Card 3: Countdown to Settlement */}
        <div className="p-4 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase font-bold text-[#69736F] flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-[#0E9F6E]" />
              <span>Settlement Countdown</span>
            </div>
            <div className="text-xl sm:text-2xl font-mono font-black text-[#063B32] mt-1">
              {slotInfo.remaining_formatted}
            </div>
            <div className="text-[11px] text-[#69736F] font-medium mt-0.5">
              Next Cycle: <span className="font-mono font-semibold">{slotInfo.next_slot_id}</span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-2xl bg-[#063B32] text-[#FFFEF9] flex items-center justify-center font-bold text-xs shrink-0">
            12H
          </div>
        </div>
      </div>
    </div>
  );
};

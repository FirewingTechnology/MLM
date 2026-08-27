import React, { createContext, useContext, useEffect, useState, useRef, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { SlotInfo } from '../types';

interface TimeContextType {
  slotInfo: SlotInfo | null;
  isLoading: boolean;
  isDemoMode: boolean;
  currentDisplayTime: string;
  remainingSeconds: number;
  remainingFormatted: string;
  refetchTime: () => Promise<any>;
  // Admin helpers
  setMode: (mode: 'REAL' | 'DEMO') => Promise<SlotInfo>;
  setExactTime: (datetime: string) => Promise<SlotInfo>;
  advanceTime: (minutes: number) => Promise<SlotInfo>;
  nextSlot: () => Promise<SlotInfo>;
  previousSlot: () => Promise<SlotInfo>;
  resetToRealTime: () => Promise<SlotInfo>;
}

const TimeContext = createContext<TimeContextType | undefined>(undefined);

export const TimeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = useQueryClient();
  const prevSlotIdRef = useRef<string | null>(null);
  const serverBaseTimeRef = useRef<number | null>(null);
  const clientSyncTimestampRef = useRef<number | null>(null);

  // Poll server slot info every 2 seconds
  const { data: slotInfo, isLoading, refetch } = useQuery<SlotInfo>({
    queryKey: ['serverTime'],
    queryFn: async () => {
      const res = await api.get('/time/current');
      return res.data.data;
    },
    refetchInterval: 2000,
    staleTime: 1000,
  });

  // Local state for smooth seconds display & countdown
  const [localSecondsRemaining, setLocalSecondsRemaining] = useState<number>(0);
  const [currentDisplayTime, setCurrentDisplayTime] = useState<string>('--:--:--');

  // Format an arbitrary timestamp into IST 12-hour formatted time (e.g. "10:42:17 AM")
  const formatIST = (timestampMs: number): string => {
    try {
      return new Intl.DateTimeFormat('en-US', {
        timeZone: 'Asia/Kolkata',
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
      }).format(new Date(timestampMs));
    } catch {
      return new Date(timestampMs).toLocaleTimeString();
    }
  };

  // Sync reference anchors whenever fresh server data arrives
  useEffect(() => {
    if (slotInfo) {
      serverBaseTimeRef.current = new Date(slotInfo.current_time).getTime();
      clientSyncTimestampRef.current = Date.now();
      setLocalSecondsRemaining(slotInfo.remaining_seconds);
      setCurrentDisplayTime(slotInfo.time_formatted);

      // Check if slot transitioned on server
      if (prevSlotIdRef.current && prevSlotIdRef.current !== slotInfo.slot_id) {
        // Slot has changed! Invalidate relevant queries so all UI updates seamlessly
        queryClient.invalidateQueries({ queryKey: ['dashboard'] });
        queryClient.invalidateQueries({ queryKey: ['adminDashboard'] });
        queryClient.invalidateQueries({ queryKey: ['commissions'] });
        queryClient.invalidateQueries({ queryKey: ['networkMiniTree'] });
        queryClient.invalidateQueries({ queryKey: ['wallet'] });
      }
      prevSlotIdRef.current = slotInfo.slot_id;
    }
  }, [slotInfo, queryClient]);

  // 1-second interval ticker for smooth continuous seconds advancement
  useEffect(() => {
    const timer = setInterval(() => {
      if (serverBaseTimeRef.current && clientSyncTimestampRef.current && slotInfo) {
        if (slotInfo.mode === 'REAL') {
          // In REAL mode, tick forward from the server anchor
          const elapsed = Date.now() - clientSyncTimestampRef.current;
          const currentTimestamp = serverBaseTimeRef.current + elapsed;
          setCurrentDisplayTime(formatIST(currentTimestamp));
        } else {
          // In DEMO mode, show exact virtual time
          setCurrentDisplayTime(slotInfo.time_formatted);
        }
      }

      setLocalSecondsRemaining((prev) => {
        if (prev <= 1) {
          // Reached 0: re-fetch from server immediately to roll over slot
          refetch();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [slotInfo, refetch]);

  // Format local remaining seconds into HH:MM:SS
  const formatRemaining = (totalSecs: number): string => {
    const s = Math.max(0, totalSecs);
    const hrs = Math.floor(s / 3600);
    const mins = Math.floor((s % 3600) / 60);
    const secs = s % 60;
    return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  // Helper function to handle server time mutation and query cache synchronization
  const handleTimeMutation = useCallback(async (action: () => Promise<any>): Promise<SlotInfo> => {
    const res = await action();
    const newSlotInfo: SlotInfo = res.data.data;
    serverBaseTimeRef.current = new Date(newSlotInfo.current_time).getTime();
    clientSyncTimestampRef.current = Date.now();
    queryClient.setQueryData(['serverTime'], newSlotInfo);
    setLocalSecondsRemaining(newSlotInfo.remaining_seconds);
    setCurrentDisplayTime(newSlotInfo.time_formatted);
    prevSlotIdRef.current = newSlotInfo.slot_id;

    // Invalidate dependent views immediately
    queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    queryClient.invalidateQueries({ queryKey: ['adminDashboard'] });
    queryClient.invalidateQueries({ queryKey: ['commissions'] });
    queryClient.invalidateQueries({ queryKey: ['networkMiniTree'] });
    return newSlotInfo;
  }, [queryClient]);

  const setMode = useCallback(async (mode: 'REAL' | 'DEMO') => {
    return handleTimeMutation(() => api.post('/admin/time/mode', { mode }));
  }, [handleTimeMutation]);

  const setExactTime = useCallback(async (datetime: string) => {
    return handleTimeMutation(() => api.post('/admin/time/set', { datetime }));
  }, [handleTimeMutation]);

  const advanceTime = useCallback(async (minutes: number) => {
    return handleTimeMutation(() => api.post('/admin/time/advance', { minutes }));
  }, [handleTimeMutation]);

  const nextSlot = useCallback(async () => {
    return handleTimeMutation(() => api.post('/admin/time/next-slot'));
  }, [handleTimeMutation]);

  const previousSlot = useCallback(async () => {
    return handleTimeMutation(() => api.post('/admin/time/previous-slot'));
  }, [handleTimeMutation]);

  const resetToRealTime = useCallback(async () => {
    return handleTimeMutation(() => api.post('/admin/time/reset'));
  }, [handleTimeMutation]);

  const value: TimeContextType = {
    slotInfo: slotInfo || null,
    isLoading,
    isDemoMode: slotInfo?.mode === 'DEMO',
    currentDisplayTime,
    remainingSeconds: localSecondsRemaining,
    remainingFormatted: formatRemaining(localSecondsRemaining),
    refetchTime: refetch,
    setMode,
    setExactTime,
    advanceTime,
    nextSlot,
    previousSlot,
    resetToRealTime,
  };

  return <TimeContext.Provider value={value}>{children}</TimeContext.Provider>;
};


export const useTime = () => {
  const context = useContext(TimeContext);
  if (!context) {
    throw new Error('useTime must be used within a TimeProvider');
  }
  return context;
};

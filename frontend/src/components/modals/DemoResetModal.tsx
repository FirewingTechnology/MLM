import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useToast } from '../../context/ToastContext';
import { useAuth } from '../../context/AuthContext';
import { X, RotateCcw, AlertTriangle, Loader2 } from 'lucide-react';

interface DemoResetModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DemoResetModal: React.FC<DemoResetModalProps> = ({ isOpen, onClose }) => {
  const { showToast } = useToast();
  const { refreshUser } = useAuth();
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleReset = async () => {
    setLoading(true);
    try {
      const res = await api.post('/admin/demo/reset');
      if (res.data?.success) {
        showToast('Demo environment reset successfully to default state.', 'success');
        queryClient.invalidateQueries();
        await refreshUser();
        onClose();
      }
    } catch (err: any) {
      showToast(err.response?.data?.error?.message || 'Failed to reset demo environment.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="w-full max-w-md rounded-2xl glass-panel border border-rose-500/40 shadow-2xl p-6 relative overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="w-12 h-12 rounded-2xl bg-rose-500/20 border border-rose-500/40 text-rose-400 flex items-center justify-center mb-4">
          <AlertTriangle className="w-6 h-6" />
        </div>

        <h2 className="text-xl font-bold text-white mb-2">
          Reset Demo Environment?
        </h2>
        <p className="text-xs text-slate-300 mb-4 leading-relaxed">
          This action will permanently wipe all test purchases, commissions, withdrawals, and custom users, and recreate the default clean demo seed network (Amol, Rahul, Priya, Akash, etc.).
        </p>

        <div className="p-3 rounded-xl bg-navy-900 border border-slate-800 text-[11px] text-slate-400 mb-5">
          ✓ Ideal for starting a fresh demonstration for new clients or investors.
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-300 text-xs font-semibold"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={handleReset}
            className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold shadow-lg shadow-rose-950 transition-colors disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Resetting...</span>
              </>
            ) : (
              <>
                <RotateCcw className="w-4 h-4" />
                <span>Reset Demo Now</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

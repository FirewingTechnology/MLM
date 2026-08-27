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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
      <div 
        className="w-full max-w-md rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-elevated p-6 relative overflow-hidden text-[#18211F]"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-[#69736F] hover:text-[#18211F] hover:bg-[#EFECE2] transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="w-12 h-12 rounded-2xl bg-[#FAF4DC] border border-[#E2C766] text-[#8C6C16] flex items-center justify-center mb-4">
          <AlertTriangle className="w-6 h-6 text-[#C88A16]" />
        </div>

        <h2 className="text-xl font-heading font-extrabold text-[#18211F] mb-2 tracking-tight">
          Reset Demo Environment?
        </h2>
        <p className="text-xs text-[#69736F] mb-4 leading-relaxed">
          This action will permanently wipe all test purchases, commissions, withdrawals, and custom users, and recreate the default clean demo seed network (Amol, Rahul, Priya, Akash, etc.).
        </p>

        <div className="p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[11px] text-[#063B32] mb-5 font-medium">
          ✓ Ideal for starting a fresh demonstration for new clients or investors.
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-3 rounded-2xl border border-[#E5E0D3] hover:bg-[#EFECE2] text-[#18211F] text-xs font-semibold cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={handleReset}
            className="flex-1 flex items-center justify-center gap-1.5 py-3 rounded-2xl bg-[#C94B4B] hover:bg-[#A83838] text-white text-xs font-heading font-bold shadow-sm transition-colors disabled:opacity-50 cursor-pointer"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Reseting...</span>
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


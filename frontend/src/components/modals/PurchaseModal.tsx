import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import confetti from 'canvas-confetti';
import api from '../../services/api';
import { useToast } from '../../context/ToastContext';
import { useAuth } from '../../context/AuthContext';
import { 
  X, 
  Sparkles, 
  CheckCircle2, 
  ShieldAlert, 
  ShoppingBag, 
  Award, 
  TrendingUp, 
  Loader2 
} from 'lucide-react';

interface PurchaseModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PurchaseModal: React.FC<PurchaseModalProps> = ({ isOpen, onClose }) => {
  const { refreshUser } = useAuth();
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const [loading, setLoading] = useState(false);
  const [successEvent, setSuccessEvent] = useState<any>(null);

  if (!isOpen) return null;

  const handlePurchase = async () => {
    setLoading(true);
    try {
      const idempotencyKey = `PUR-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
      const res = await api.post('/purchases', { idempotency_key: idempotencyKey });
      
      if (res.data?.success) {
        // Fire festive wealth confetti
        confetti({
          particleCount: 80,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#063B32', '#C9A227', '#E2C766', '#0E9F6E']
        });

        setSuccessEvent(res.data.data);
        showToast('Demo purchase successful! 30,000 BV credited to your account.', 'success');
        
        // Invalidate queries to refresh live UI across all screens
        queryClient.invalidateQueries({ queryKey: ['dashboard'] });
        queryClient.invalidateQueries({ queryKey: ['network'] });
        queryClient.invalidateQueries({ queryKey: ['wallet'] });
        queryClient.invalidateQueries({ queryKey: ['transactions'] });
        queryClient.invalidateQueries({ queryKey: ['commissions'] });
        queryClient.invalidateQueries({ queryKey: ['adminDashboard'] });
        queryClient.invalidateQueries({ queryKey: ['adminUsers'] });
        
        await refreshUser();
      }
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Purchase could not be processed.';
      showToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setSuccessEvent(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
      <div 
        className="w-full max-w-lg rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-elevated p-6 relative overflow-hidden text-[#18211F]"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-[#69736F] hover:text-[#18211F] hover:bg-[#EFECE2] transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {!successEvent ? (
          <div>
            <div className="flex items-center gap-2 text-[#063B32] text-xs font-mono font-bold uppercase tracking-wider mb-1.5">
              <Sparkles className="w-4 h-4 text-[#C9A227]" />
              <span>Sub Franchise Activation</span>
            </div>

            <h2 className="text-2xl font-heading font-extrabold text-[#18211F] mb-1 tracking-tight">
              Premium Sub Franchise Package
            </h2>
            <p className="text-[#69736F] text-xs mb-5">
              Unlock your distributor status, generate 30,000 personal BV, and activate binary matching commissions.
            </p>

            {/* Price breakdown card */}
            <div className="rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] p-4 sm:p-5 mb-5 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-[#69736F] font-medium">Product / Business Value</span>
                <span className="font-semibold text-[#18211F] font-mono">₹30,000</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-[#69736F] font-medium">GST (18% Applicable)</span>
                <span className="font-semibold text-[#18211F] font-mono">₹5,000</span>
              </div>
              <div className="h-px bg-[#E5E0D3]" />
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-[#18211F]">Total Sub Franchise Price</span>
                <span className="text-2xl font-heading font-black text-[#063B32] font-mono">₹35,000</span>
              </div>
              <div className="flex items-center justify-between pt-1">
                <span className="text-xs text-[#18211F] font-semibold flex items-center gap-1.5">
                  <TrendingUp className="w-4 h-4 text-[#C9A227]" />
                  Business Volume (BV) Generated:
                </span>
                <span className="font-mono font-bold text-xs bg-[#FAF4DC] text-[#8C6C16] border border-[#E2C766]/60 px-3 py-1 rounded-xl">
                  30,000 BV
                </span>
              </div>
            </div>

            {/* Feature highlights */}
            <div className="space-y-2.5 mb-6">
              <div className="flex items-center gap-2.5 text-xs text-[#18211F]">
                <Award className="w-4 h-4 text-[#063B32] shrink-0" />
                <span>10% Direct Referral Bonus (₹3,000) for your direct sponsor</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-[#18211F]">
                <Award className="w-4 h-4 text-[#063B32] shrink-0" />
                <span>30,000 BV propagates up your binary upline tree</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-[#C9A227] shrink-0">
                <Award className="w-4 h-4 text-[#C9A227] shrink-0" />
                <span>Qualifies for ₹10,000 Binary Pair Bonus per 30k/30k match</span>
              </div>
            </div>

            {/* Package Notice */}
            <div className="flex items-start gap-2.5 p-3 rounded-2xl bg-[#FAF4DC] border border-[#E2C766] text-[#8C6C16] text-xs mb-6">
              <ShieldAlert className="w-4 h-4 text-[#C88A16] shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Sub Franchise Purchase:</span> Instant activation with 30,000 personal BV credited to your account.
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleClose}
                className="flex-1 px-4 py-3 rounded-2xl border border-[#E5E0D3] hover:bg-[#EFECE2] text-[#18211F] text-xs font-semibold transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={loading}
                onClick={handlePurchase}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/30 text-xs font-heading font-bold shadow-wealth-card transition-all transform hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 cursor-pointer"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-[#C9A227]" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <ShoppingBag className="w-4 h-4 text-[#C9A227]" />
                    <span>Activate Sub Franchise Package</span>
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <div className="w-16 h-16 rounded-2xl bg-[#FAF4DC] border border-[#E2C766] text-[#8C6C16] flex items-center justify-center mx-auto mb-4 animate-bounce">
              <CheckCircle2 className="w-10 h-10 text-[#063B32]" />
            </div>

            <h3 className="text-2xl font-heading font-extrabold text-[#18211F] mb-1">Sub Franchise Activated!</h3>
            <p className="text-[#063B32] font-bold text-sm mb-4">
              ₹35,000 Sub Franchise Package Activation Successful
            </p>

            <div className="p-4 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] mb-6 text-left space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-[#69736F] font-medium">Transaction Ref:</span>
                <span className="font-mono text-[#18211F] font-bold">{successEvent.purchase?.purchase_code}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#69736F] font-medium">BV Added:</span>
                <span className="text-[#063B32] font-bold font-mono">+30,000 BV</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#69736F] font-medium">Status:</span>
                <span className="text-[#063B32] font-semibold">Active Distributor</span>
              </div>
              {successEvent.events && successEvent.events.length > 0 && (
                <div className="pt-2 border-t border-[#E5E0D3]">
                  <div className="text-[#18211F] mb-1 font-semibold">Commissions Triggered:</div>
                  {successEvent.events.map((ev: any, idx: number) => (
                    <div key={idx} className="text-[#69736F] flex justify-between">
                      <span>• {ev.type === 'DIRECT_REFERRAL' ? 'Direct Bonus' : 'Matching Bonus'} to {ev.beneficiary}</span>
                      <span className="text-[#0E9F6E] font-mono font-bold">+₹{ev.amount?.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={handleClose}
              className="w-full py-3 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/30 text-xs font-bold transition-colors cursor-pointer"
            >
              Continue to Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
};


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
        // Fire festive confetti
        confetti({
          particleCount: 80,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#10b981', '#34d399', '#f59e0b', '#3b82f6']
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="w-full max-w-lg rounded-2xl glass-panel border border-slate-700/80 shadow-2xl p-6 relative overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Glow accent */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-brand-500/20 rounded-full blur-3xl pointer-events-none" />

        <button
          onClick={handleClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {!successEvent ? (
          <div>
            <div className="flex items-center gap-2 text-brand-400 text-xs font-bold uppercase tracking-wider mb-2">
              <Sparkles className="w-4 h-4" />
              <span>Demo Package Activation</span>
            </div>

            <h2 className="text-2xl font-extrabold text-white mb-2">
              Premium Business Package
            </h2>
            <p className="text-slate-400 text-xs mb-5">
              Unlock your virtual MLM distributor status, generate 30,000 personal BV, and activate binary matching commissions.
            </p>

            {/* Price breakdown card */}
            <div className="rounded-xl bg-navy-900/80 border border-slate-800 p-4 mb-5 space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">Product / Business Value</span>
                <span className="font-semibold text-slate-200">₹30,000</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">GST (18% Fictional)</span>
                <span className="font-semibold text-slate-200">₹5,000</span>
              </div>
              <div className="h-px bg-slate-800" />
              <div className="flex items-center justify-between">
                <span className="text-base font-bold text-white">Total Virtual Price</span>
                <span className="text-2xl font-extrabold text-brand-400">₹35,000</span>
              </div>
              <div className="flex items-center justify-between pt-1">
                <span className="text-xs text-brand-300 font-medium flex items-center gap-1.5">
                  <TrendingUp className="w-4 h-4 text-brand-400" />
                  Business Volume (BV) Generated:
                </span>
                <span className="font-mono font-bold text-sm bg-brand-500/20 text-brand-300 border border-brand-500/30 px-2.5 py-0.5 rounded-lg">
                  30,000 BV
                </span>
              </div>
            </div>

            {/* Feature highlights */}
            <div className="space-y-2 mb-6">
              <div className="flex items-center gap-2.5 text-xs text-slate-300">
                <Award className="w-4 h-4 text-brand-400 shrink-0" />
                <span>10% Direct Referral Bonus (₹3,000) for your direct sponsor</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-slate-300">
                <Award className="w-4 h-4 text-brand-400 shrink-0" />
                <span>30,000 BV propagates up your binary upline tree</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-slate-300">
                <Award className="w-4 h-4 text-brand-400 shrink-0" />
                <span>10% Binary matching bonus calculated on matched volume</span>
              </div>
            </div>

            {/* Virtual Demo Notice */}
            <div className="flex items-start gap-2.5 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs mb-6">
              <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Virtual Demo Purchase:</span> No credit card, UPI, or real bank account will be charged. This simulates a real package activation instantly in the database.
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleClose}
                className="flex-1 px-4 py-2.5 rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-300 text-sm font-semibold transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={loading}
                onClick={handlePurchase}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-400 hover:to-emerald-500 text-navy-950 text-sm font-bold shadow-glow-emerald transition-all transform hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Processing Demo...</span>
                  </>
                ) : (
                  <>
                    <ShoppingBag className="w-4 h-4" />
                    <span>Buy Virtual Package</span>
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center justify-center mx-auto mb-4 animate-bounce">
              <CheckCircle2 className="w-10 h-10" />
            </div>

            <h3 className="text-2xl font-black text-white mb-1">Package Activated!</h3>
            <p className="text-emerald-400 font-semibold text-sm mb-4">
              ₹35,000 Virtual Package Successful
            </p>

            <div className="p-4 rounded-xl bg-navy-900/80 border border-slate-800 mb-6 text-left space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Transaction Ref:</span>
                <span className="font-mono text-slate-200 font-bold">{successEvent.purchase?.purchase_code}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">BV Added:</span>
                <span className="text-brand-400 font-bold font-mono">+30,000 BV</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Status:</span>
                <span className="text-emerald-400 font-semibold">Active Distributor</span>
              </div>
              {successEvent.events && successEvent.events.length > 0 && (
                <div className="pt-2 border-t border-slate-800">
                  <div className="text-slate-400 mb-1 font-semibold">Commissions Triggered:</div>
                  {successEvent.events.map((ev: any, idx: number) => (
                    <div key={idx} className="text-slate-300 flex justify-between">
                      <span>• {ev.type === 'DIRECT_REFERRAL' ? 'Direct Bonus' : 'Matching Bonus'} to {ev.beneficiary}</span>
                      <span className="text-brand-400 font-mono font-bold">+₹{ev.amount?.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={handleClose}
              className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-sm font-bold transition-colors"
            >
              Continue to Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

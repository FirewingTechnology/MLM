import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useOutletContext } from 'react-router-dom';
import api from '../services/api';
import { Package } from '../types';
import { 
  PackageCheck, 
  Sparkles, 
  CheckCircle2, 
  ShieldAlert, 
  ShoppingBag, 
  Award, 
  Coins, 
  TrendingUp 
} from 'lucide-react';

export const PackagesPage: React.FC = () => {
  const { openPurchaseModal } = useOutletContext<{ openPurchaseModal: () => void }>();

  const { data: packages, isLoading } = useQuery<Package[]>({
    queryKey: ['packages'],
    queryFn: async () => {
      const res = await api.get('/packages');
      return res.data.data;
    },
  });

  const pkg = packages?.[0] || {
    name: 'Premium Business Package',
    description: 'Virtual Business Ownership Package with 30,000 BV and active distributor rights.',
    price: 35000,
    product_value: 30000,
    gst_amount: 5000,
    bv: 30000,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-brand-400 mb-1">
          <PackageCheck className="w-4 h-4" />
          <span>Virtual Marketplace</span>
        </div>
        <h1 className="text-2xl font-black text-white">Business Packages</h1>
        <p className="text-xs text-slate-400">
          Activate distributor status and generate Business Volume (BV) across your binary network.
        </p>
      </div>

      <div className="max-w-xl mx-auto pt-4">
        <div className="rounded-3xl glass-panel p-6 sm:p-8 border border-slate-800 relative overflow-hidden glass-panel-hover">
          <div className="absolute top-0 right-0 w-64 h-64 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="flex items-center justify-between mb-4">
            <span className="text-[10px] font-bold uppercase tracking-wider bg-brand-500/20 text-brand-300 border border-brand-500/40 px-3 py-1 rounded-full">
              Standard Qualifying Tier
            </span>
            <span className="text-xs font-mono font-bold text-slate-400">100% VIRTUAL DEMO</span>
          </div>

          <h2 className="text-2xl sm:text-3xl font-black text-white mb-2">
            {pkg.name}
          </h2>
          <p className="text-xs text-slate-300 mb-6 leading-relaxed">
            {pkg.description}
          </p>

          {/* Pricing breakdown */}
          <div className="p-4 rounded-2xl bg-navy-950/80 border border-slate-800 space-y-3 mb-6 font-mono text-xs">
            <div className="flex justify-between text-slate-400">
              <span className="font-sans">Business Value:</span>
              <span className="text-slate-200 font-bold">₹{pkg.product_value.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span className="font-sans">Simulated GST:</span>
              <span className="text-slate-200 font-bold">₹{pkg.gst_amount.toLocaleString()}</span>
            </div>
            <div className="h-px bg-slate-800" />
            <div className="flex justify-between items-center text-sm">
              <span className="font-sans font-bold text-white">Total Package Price:</span>
              <span className="text-2xl font-black text-brand-400">₹{pkg.price.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center pt-2 border-t border-slate-800/80">
              <span className="font-sans text-brand-300 font-semibold flex items-center gap-1">
                <TrendingUp className="w-4 h-4" />
                BV Credited to Network:
              </span>
              <span className="bg-brand-500/20 text-brand-300 border border-brand-500/30 px-3 py-0.5 rounded-lg font-bold">
                {pkg.bv.toLocaleString()} BV
              </span>
            </div>
          </div>

          {/* Feature highlights */}
          <div className="space-y-3 mb-8 text-xs text-slate-300">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0" />
              <span>Direct Sponsor receives <strong className="text-white">10% referral commission (₹3,000)</strong></span>
            </div>
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0" />
              <span>Full <strong className="text-white">30,000 BV</strong> propagates upward through the binary ancestry</span>
            </div>
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0" />
              <span>Generates <strong className="text-white">10% Binary Matching Bonus</strong> on matched volume</span>
            </div>
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0" />
              <span>Activates full Virtual Wallet withdrawal rights in the demo</span>
            </div>
          </div>

          {/* CTA */}
          <button
            onClick={openPurchaseModal}
            className="w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-400 hover:to-emerald-500 text-navy-950 font-black text-sm shadow-glow-emerald transition-all transform hover:scale-[1.01] active:scale-[0.99]"
          >
            <ShoppingBag className="w-4 h-4" />
            <span>Buy Virtual Package (₹35,000)</span>
          </button>
        </div>
      </div>
    </div>
  );
};

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useOutletContext } from 'react-router-dom';
import api from '../services/api';
import { Package } from '../types';
import { 
  PackageCheck, 
  Sparkles, 
  CheckCircle2, 
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
    <div className="space-y-5 sm:space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
        <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-[#C9A227] mb-1">
          <PackageCheck className="w-4 h-4 text-[#063B32]" />
          <span>Virtual Marketplace</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-[#18211F] tracking-tight">Business Packages</h1>
        <p className="text-xs sm:text-sm text-[#69736F] font-medium">
          Activate distributor status and generate Business Volume (BV) across your binary network.
        </p>
      </div>

      <div className="max-w-xl mx-auto pt-2">
        <div className="rounded-3xl bg-[#FFFEF9] p-6 sm:p-8 border-2 border-[#C9A227]/40 shadow-wealth-gold relative overflow-hidden">
          {/* Top Gold Ribbon */}
          <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-[#C9A227] via-[#E2C766] to-[#C9A227]" />

          <div className="flex items-center justify-between mb-4 mt-1">
            <span className="text-[10px] font-bold uppercase tracking-wider bg-[#FAF4DC] text-[#8C6C16] border border-[#E2C766]/60 px-3 py-1 rounded-full flex items-center gap-1 font-mono">
              <Sparkles className="w-3 h-3 text-[#C9A227]" />
              <span>Standard Qualifying Tier</span>
            </span>
            <span className="text-xs font-mono font-bold text-[#69736F]">100% VIRTUAL SIMULATION</span>
          </div>

          <h2 className="text-2xl sm:text-3xl font-heading font-extrabold text-[#18211F] mb-2 tracking-tight">
            {pkg.name}
          </h2>
          <p className="text-xs text-[#69736F] mb-6 leading-relaxed">
            {pkg.description}
          </p>

          {/* Pricing breakdown */}
          <div className="p-5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] space-y-3 mb-6 font-mono text-xs">
            <div className="flex justify-between text-[#69736F]">
              <span className="font-sans">Business Value:</span>
              <span className="text-[#18211F] font-bold">₹{pkg.product_value.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-[#69736F]">
              <span className="font-sans">Simulated GST:</span>
              <span className="text-[#18211F] font-bold">₹{pkg.gst_amount.toLocaleString()}</span>
            </div>
            <div className="h-px bg-[#E5E0D3]" />
            <div className="flex justify-between items-center text-sm">
              <span className="font-sans font-bold text-[#18211F]">Total Package Price:</span>
              <span className="text-2xl sm:text-3xl font-heading font-black text-[#063B32]">₹{pkg.price.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center pt-2 border-t border-[#E5E0D3]">
              <span className="font-sans text-[#18211F] font-semibold flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4 text-[#C9A227]" />
                BV Credited to Network:
              </span>
              <span className="bg-[#FAF4DC] text-[#8C6C16] border border-[#E2C766]/60 px-3 py-0.5 rounded-lg font-bold">
                {pkg.bv.toLocaleString()} BV
              </span>
            </div>
          </div>

          {/* Feature highlights */}
          <div className="space-y-3 mb-8 text-xs text-[#18211F]">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-4 h-4 text-[#063B32] shrink-0" />
              <span>Direct Sponsor receives <strong className="text-[#063B32]">10% referral commission (₹3,000)</strong></span>
            </div>
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-4 h-4 text-[#063B32] shrink-0" />
              <span>Full <strong className="text-[#063B32]">30,000 BV</strong> propagates upward through the binary ancestry</span>
            </div>
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-4 h-4 text-[#063B32] shrink-0" />
              <span>Qualifies for <strong className="text-[#8C6C16]">₹15,000 Binary Pair Bonus</strong> per 30k/30k match</span>
            </div>
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-4 h-4 text-[#063B32] shrink-0" />
              <span>Activates full Virtual Wallet withdrawal rights in the demo</span>
            </div>
          </div>

          {/* CTA */}
          <button
            onClick={openPurchaseModal}
            className="w-full flex items-center justify-center gap-2 py-4 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/40 font-heading font-black text-sm shadow-wealth-card transition-all transform hover:scale-[1.01] active:scale-[0.99] cursor-pointer"
          >
            <ShoppingBag className="w-4 h-4 text-[#C9A227]" />
            <span>ACTIVATE VIRTUAL PACKAGE (₹35,000)</span>
          </button>
        </div>
      </div>
    </div>
  );
};


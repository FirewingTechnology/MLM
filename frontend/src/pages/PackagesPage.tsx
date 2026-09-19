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
    name: 'Premium Sub Franchise',
    description: 'Sub Franchise Business Ownership Package with 30,000 BV and active distributor rights.',
    price: 35400,
    product_value: 30000,
    gst_amount: 5400,
    bv: 30000,
  };

  const [qrImgError, setQrImgError] = React.useState(false);

  return (
    <div className="space-y-5 sm:space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
        <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-[#C9A227] mb-1">
          <PackageCheck className="w-4 h-4 text-[#063B32]" />
          <span>Sub Franchise Marketplace</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-[#18211F] tracking-tight">Sub Franchise Packages</h1>
        <p className="text-xs sm:text-sm text-[#69736F] font-medium">
          Activate distributor status and generate Business Volume (BV) across your matching franchise network.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-2">
        {/* Left Column: Package Configuration Details */}
        <div className="lg:col-span-7">
          <div className="rounded-3xl bg-[#FFFEF9] p-6 sm:p-8 border-2 border-[#C9A227]/40 shadow-wealth-gold relative overflow-hidden h-full flex flex-col justify-between">
            {/* Top Gold Ribbon */}
            <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-[#C9A227] via-[#E2C766] to-[#C9A227]" />

            <div>
              <div className="flex items-center justify-between mb-4 mt-1">
                <span className="text-[10px] font-bold uppercase tracking-wider bg-[#FAF4DC] text-[#8C6C16] border border-[#E2C766]/60 px-3 py-1 rounded-full flex items-center gap-1 font-mono">
                  <Sparkles className="w-3 h-3 text-[#C9A227]" />
                  <span>Standard Qualifying Tier</span>
                </span>
                <span className="text-xs font-mono font-bold text-[#69736F]">SUB FRANCHISE PACKAGE</span>
              </div>

              <h2 className="text-2xl sm:text-3xl font-heading font-extrabold text-[#18211F] mb-2 tracking-tight">
                {pkg.name}
              </h2>
              <p className="text-xs text-[#69736F] mb-6 leading-relaxed">
                {pkg.description}
              </p>

              {/* Pricing breakdown */}
              <div className="p-5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] space-y-3 mb-6 font-mono text-xs">
                <div className="flex justify-between items-center text-[#69736F]">
                  <span className="font-sans">Product Value:</span>
                  <span className="text-[#18211F] font-bold">₹{pkg.product_value.toLocaleString()}</span>
                </div>
                <div className="flex justify-between items-center text-[#69736F]">
                  <span className="font-sans">GST (18%):</span>
                  <span className="text-[#18211F] font-bold">₹{pkg.gst_amount.toLocaleString()}</span>
                </div>
                <div className="h-px bg-[#E5E0D3]" />
                <div className="flex justify-between items-center text-sm">
                  <span className="font-sans font-bold text-[#18211F]">Package Total Price:</span>
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
              <div className="space-y-3 mb-6 text-xs text-[#18211F]">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-4 h-4 text-[#063B32] shrink-0" />
                  <span>Direct Sponsor receives <strong className="text-[#063B32]">10% referral commission (₹3,000)</strong></span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-4 h-4 text-[#063B32] shrink-0" />
                  <span>Full <strong className="text-[#063B32]">30,000 BV</strong> propagates upward through the Matching ancestry</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-4 h-4 text-[#063B32] shrink-0" />
                  <span>Qualifies for <strong className="text-[#8C6C16]">₹10,000 Matching Pair Bonus</strong> per 30k/30k match</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-4 h-4 text-[#063B32] shrink-0" />
                  <span>Activates full Income Wallet withdrawal rights</span>
                </div>
              </div>
            </div>

            {/* Security Notice */}
            <div className="p-3.5 rounded-2xl bg-[#FAF4DC] border border-[#E2C766] text-[#8C6C16] text-xs flex items-center gap-2">
              <span className="font-bold font-mono">SECURE PIN:</span>
              <span>Package requires an authorized single-use Security PIN to activate and release 30,000 BV.</span>
            </div>
          </div>
        </div>

        {/* Right Column: Scan & Pay Static QR Section */}
        <div className="lg:col-span-5">
          <div className="rounded-3xl bg-[#FFFEF9] p-6 sm:p-7 border-2 border-[#E2C766] shadow-wealth-card flex flex-col justify-between h-full space-y-5">
            {/* Section Header */}
            <div className="border-b border-[#E5E0D3] pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-xl bg-[#FAF4DC] border border-[#E2C766] text-[#8C6C16] flex items-center justify-center">
                    <Coins className="w-4 h-4 text-[#C9A227]" />
                  </div>
                  <div>
                    <h3 className="text-base font-heading font-extrabold text-[#18211F] tracking-tight">
                      Scan & Pay
                    </h3>
                    <p className="text-[11px] text-[#69736F]">
                      Official Static Payment QR
                    </p>
                  </div>
                </div>
                <span className="text-[10px] font-mono font-bold bg-[#E0F3EE] text-[#063B32] border border-[#8DCFBF] px-2.5 py-0.5 rounded-full">
                  VERIFIED
                </span>
              </div>
            </div>

            {/* Static QR Code Card */}
            <div className="flex flex-col items-center justify-center p-4 bg-[#F7F4EC]/70 rounded-2xl border border-[#E5E0D3] text-center">
              <div className="p-3 bg-white rounded-2xl border-2 border-[#E2C766]/60 shadow-xs mb-3 flex items-center justify-center max-w-[210px] w-full aspect-square">
                {!qrImgError ? (
                  <img
                    src="/payment-qr.png"
                    alt="Static Payment QR Code"
                    onError={() => setQrImgError(true)}
                    className="w-full h-full object-contain rounded-xl"
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center p-4 text-[#69736F] text-xs">
                    <Coins className="w-10 h-10 text-[#C9A227] mb-2" />
                    <span>Payment QR Image</span>
                    <span className="text-[10px] text-[#8C6C16] font-mono mt-1">/payment-qr.png</span>
                  </div>
                )}
              </div>

              <p className="text-xs text-[#18211F] font-medium leading-relaxed max-w-xs">
                Scan this QR code using your UPI/payment application.
              </p>

              {/* Payment Amount Display */}
              <div className="mt-3 w-full p-2.5 bg-white rounded-xl border border-[#E5E0D3] flex items-center justify-between font-mono text-xs">
                <span className="text-[#69736F] font-sans font-bold uppercase text-[10px]">Payment Amount</span>
                <span className="text-lg font-heading font-black text-[#063B32]">
                  ₹{pkg.price.toLocaleString()}
                </span>
              </div>
            </div>

            {/* Simple and Clear Payment Instructions */}
            <div className="space-y-2 text-xs">
              <div className="p-3 rounded-xl bg-[#FAF4DC]/70 border border-[#E2C766]/60 text-[#8C6C16] space-y-1 text-[11px] leading-relaxed">
                <p className="font-semibold text-[#6D530F]">
                  Scan the QR code to make the package payment of ₹{pkg.price.toLocaleString()}.
                </p>
                <p className="text-[#8C6C16]">
                  After completing payment, submit/continue through the existing payment verification process.
                </p>
              </div>
            </div>

            {/* CTA — Opens Existing Payment Verification Flow */}
            <button
              onClick={openPurchaseModal}
              className="w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/40 font-heading font-black text-xs sm:text-sm shadow-wealth-card transition-all transform hover:scale-[1.01] active:scale-[0.99] cursor-pointer"
            >
              <ShoppingBag className="w-4 h-4 text-[#C9A227]" />
              <span>REQUEST SECURITY PIN & ACTIVATE (₹{pkg.price.toLocaleString()})</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};


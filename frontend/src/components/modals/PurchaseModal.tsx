import React, { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import confetti from 'canvas-confetti';
import api from '../../services/api';
import { useToast } from '../../context/ToastContext';
import { useAuth } from '../../context/AuthContext';
import { ActivationStatusResponse } from '../../types';
import {
  X,
  Sparkles,
  CheckCircle2,
  ShieldCheck,
  ShoppingBag,
  Award,
  TrendingUp,
  Loader2,
  KeyRound,
  CreditCard,
  Clock,
  ArrowRight,
  UserCheck,
  AlertCircle,
  Copy,
  Check,
  Building2
} from 'lucide-react';
import { UpiQrPaymentCard } from '../common/UpiQrPaymentCard';

interface PurchaseModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PurchaseModal: React.FC<PurchaseModalProps> = ({ isOpen, onClose }) => {
  const { user, refreshUser } = useAuth();
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const [activeStep, setActiveStep] = useState<'OVERVIEW' | 'PAYMENT' | 'PIN'>('OVERVIEW');
  const [paymentMethod, setPaymentMethod] = useState('UPI_TRANSFER');
  const [paymentRef, setPaymentRef] = useState('');
  const [securityPin, setSecurityPin] = useState('');
  const [submittingPayment, setSubmittingPayment] = useState(false);
  const [activatingPin, setActivatingPin] = useState(false);
  const [successEvent, setSuccessEvent] = useState<any>(null);

  // Fetch live activation status
  const { data: statusData, isLoading: loadingStatus, refetch: refetchStatus } = useQuery<ActivationStatusResponse>({
    queryKey: ['activationStatus'],
    queryFn: async () => {
      const res = await api.get('/package/activation-status');
      return res.data.data;
    },
    enabled: isOpen,
  });

  const req = statusData?.activation_request;
  const isPinIssued = req?.status === 'PIN_ISSUED';
  const isPaymentSubmitted = req?.status === 'PAYMENT_SUBMITTED' || req?.status === 'UNDER_REVIEW';
  const isPaymentVerified = req?.status === 'PAYMENT_VERIFIED';

  useEffect(() => {
    if (isPinIssued || isPaymentVerified) {
      setActiveStep('PIN');
    } else if (isPaymentSubmitted) {
      setActiveStep('PAYMENT');
    } else {
      setActiveStep('OVERVIEW');
    }
  }, [req?.status, isPinIssued, isPaymentVerified, isPaymentSubmitted]);

  if (!isOpen) return null;

  const handleSubmitPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!paymentRef.trim()) {
      showToast('Please provide a valid Payment Reference (UTR / Txn ID).', 'error');
      return;
    }

    setSubmittingPayment(true);
    try {
      const res = await api.post('/package/payment-submit', {
        request_id: req?.id,
        payment_method: paymentMethod,
        payment_reference: paymentRef.trim()
      });

      if (res.data?.success) {
        showToast('Payment submitted successfully! Admin will verify and issue your Security PIN.', 'success');
        await refetchStatus();
        queryClient.invalidateQueries({ queryKey: ['dashboard'] });
        setActiveStep('PAYMENT');
      }
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Could not submit payment reference.';
      showToast(msg, 'error');
    } finally {
      setSubmittingPayment(false);
    }
  };

  const handleActivateWithPin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!securityPin.trim()) {
      showToast('Please enter your 8-character Security PIN.', 'error');
      return;
    }

    setActivatingPin(true);
    try {
      const res = await api.post('/package/activate', {
        pin: securityPin.trim().toUpperCase(),
        request_id: req?.id
      });

      if (res.data?.success) {
        // Fire celebration confetti
        confetti({
          particleCount: 100,
          spread: 80,
          origin: { y: 0.6 },
          colors: ['#063B32', '#C9A227', '#E2C766', '#0E9F6E']
        });

        setSuccessEvent(res.data.data);
        showToast('Package activated successfully! 30,000 BV credited to your account.', 'success');

        // Invalidate live data across pages
        queryClient.invalidateQueries({ queryKey: ['dashboard'] });
        queryClient.invalidateQueries({ queryKey: ['network'] });
        queryClient.invalidateQueries({ queryKey: ['wallet'] });
        queryClient.invalidateQueries({ queryKey: ['transactions'] });
        queryClient.invalidateQueries({ queryKey: ['commissions'] });
        queryClient.invalidateQueries({ queryKey: ['adminDashboard'] });
        queryClient.invalidateQueries({ queryKey: ['adminUsers'] });
        queryClient.invalidateQueries({ queryKey: ['activationStatus'] });

        await refreshUser();
      }
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Invalid or unavailable Security PIN.';
      showToast(msg, 'error');
    } finally {
      setActivatingPin(false);
    }
  };

  const handleClose = () => {
    setSuccessEvent(null);
    setSecurityPin('');
    setPaymentRef('');
    onClose();
  };

  const recipient = statusData?.payment_recipient;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="w-full max-w-xl rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-elevated p-6 sm:p-7 relative overflow-hidden text-[#18211F] max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-[#69736F] hover:text-[#18211F] hover:bg-[#EFECE2] transition-colors cursor-pointer z-10"
        >
          <X className="w-5 h-5" />
        </button>

        {!successEvent ? (
          <div>
            {/* Header */}
            <div className="flex items-center gap-2 text-[#063B32] text-xs font-mono font-bold uppercase tracking-wider mb-1">
              <ShieldCheck className="w-4 h-4 text-[#C9A227]" />
              <span>Secure Paid PIN Package Activation</span>
            </div>

            <h2 className="text-2xl font-heading font-extrabold text-[#18211F] mb-1 tracking-tight">
              {statusData?.package?.name || 'Premium Sub Franchise'} (₹{(statusData?.package?.price || 35400).toLocaleString()})
            </h2>
            <p className="text-[#69736F] text-xs mb-5">
              Strict 4-stage verified activation workflow. Generates 30,000 personal BV upon PIN authorization.
            </p>

            {/* Workflow Step Tracker */}
            <div className="grid grid-cols-4 gap-1.5 mb-6 p-2 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[10px] font-bold text-center">
              <div className={`p-2 rounded-xl transition-all ${activeStep === 'OVERVIEW' ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs' : 'text-[#69736F]'}`}>
                1. Overview
              </div>
              <div className={`p-2 rounded-xl transition-all ${activeStep === 'PAYMENT' ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs' : isPaymentSubmitted || isPaymentVerified || isPinIssued ? 'bg-[#E0F3EE] text-[#063B32]' : 'text-[#69736F]'}`}>
                2. Payment
              </div>
              <div className={`p-2 rounded-xl transition-all ${isPaymentVerified ? 'bg-[#E0F3EE] text-[#063B32]' : 'text-[#69736F]'}`}>
                3. Verification
              </div>
              <div className={`p-2 rounded-xl transition-all ${activeStep === 'PIN' || isPinIssued ? 'bg-[#C9A227] text-[#18211F] font-extrabold shadow-xs' : 'text-[#69736F]'}`}>
                4. Enter PIN
              </div>
            </div>

            {/* STEP 1: OVERVIEW */}
            {activeStep === 'OVERVIEW' && (
              <div className="space-y-4">
                {/* Price breakdown card */}
                <div className="rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] p-4 sm:p-5 space-y-2.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#69736F] font-medium">Product / Business Value</span>
                    <span className="font-semibold text-[#18211F] font-mono">₹{(statusData?.package?.product_value || 30000).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#69736F] font-medium">GST (18% Applicable)</span>
                    <span className="font-semibold text-[#18211F] font-mono">₹{(statusData?.package?.gst_amount || 5400).toLocaleString()}</span>
                  </div>
                  <div className="h-px bg-[#E5E0D3]" />
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-[#18211F]">Total Package Payable</span>
                    <span className="text-2xl font-heading font-black text-[#063B32] font-mono">₹{(statusData?.package?.price || 35400).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-xs text-[#18211F] font-semibold flex items-center gap-1.5">
                      <TrendingUp className="w-4 h-4 text-[#C9A227]" />
                      Personal BV Credited:
                    </span>
                    <span className="font-mono font-bold text-xs bg-[#FAF4DC] text-[#8C6C16] border border-[#E2C766]/60 px-3 py-0.5 rounded-lg">
                      30,000 BV
                    </span>
                  </div>
                </div>

                {/* Features */}
                <div className="space-y-2 text-xs text-[#18211F] py-1">
                  <div className="flex items-center gap-2.5">
                    <Award className="w-4 h-4 text-[#063B32] shrink-0" />
                    <span>10% Direct Sponsor Commission (₹3,000) rewarded on activation</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Award className="w-4 h-4 text-[#063B32] shrink-0" />
                    <span>Full 30,000 BV propagates upward through your Matching upline leg</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Award className="w-4 h-4 text-[#C9A227] shrink-0" />
                    <span>Qualifies for ₹10,000 Matching Pair Bonus (30k:30k match)</span>
                  </div>
                </div>

                {/* Security Gate Notice */}
                <div className="p-3.5 rounded-2xl bg-[#FAF4DC] border border-[#E2C766] text-[#8C6C16] text-xs flex items-start gap-2.5">
                  <KeyRound className="w-4 h-4 text-[#C88A16] shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Security PIN Requirement:</span> Packages are activated exclusively with a single-use Security PIN generated after payment verification.
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-3 pt-2">
                  <button
                    type="button"
                    onClick={handleClose}
                    className="flex-1 px-4 py-3 rounded-2xl border border-[#E5E0D3] hover:bg-[#EFECE2] text-[#18211F] text-xs font-semibold transition-colors cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveStep('PAYMENT')}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/30 text-xs font-heading font-bold shadow-wealth-card transition-all cursor-pointer"
                  >
                    <span>Proceed to Payment</span>
                    <ArrowRight className="w-4 h-4 text-[#C9A227]" />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 2: PAYMENT SUBMISSION */}
            {activeStep === 'PAYMENT' && (
              <form onSubmit={handleSubmitPayment} className="space-y-4">
                {/* Recipient Uplink Card */}
                <div className="p-4 rounded-2xl bg-[#F7F4EC] border border-[#8DCFBF] text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#063B32] flex items-center gap-1.5">
                      <UserCheck className="w-4 h-4 text-[#063B32]" />
                      Payment Beneficiary / Recipient
                    </span>
                    <span className="bg-[#E0F3EE] text-[#063B32] px-2.5 py-0.5 rounded-full font-bold text-[10px]">
                      {recipient?.relationship || 'Direct Sponsor'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-[#18211F] pt-1">
                    <div>
                      <div className="font-bold text-sm">{recipient?.full_name || 'Admin Franchise'}</div>
                      <div className="text-[10px] text-[#69736F] font-mono">Code: {recipient?.user_code || 'ADM-001'}</div>
                    </div>
                    <div className="text-right font-mono">
                      <div className="text-xs text-[#69736F]">Payable Amount</div>
                      <div className="font-bold text-base text-[#063B32]">₹{(statusData?.package?.price || 35400).toLocaleString()}</div>
                    </div>
                  </div>
                </div>

                {/* Status Notice if already submitted */}
                {isPaymentSubmitted && (
                  <div className="p-3.5 rounded-2xl bg-[#E0F3EE] border border-[#8DCFBF] text-[#063B32] text-xs flex items-start gap-2.5">
                    <Clock className="w-4 h-4 text-[#0E9F6E] shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold">Payment Under Admin Review:</span> Reference <code className="bg-white/80 px-1 py-0.5 rounded font-mono font-bold">{req?.payment_reference}</code> is currently being verified.
                    </div>
                  </div>
                )}

                {/* Payment Input Fields */}
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-bold text-[#18211F] mb-1">
                      Payment Method
                    </label>
                    <select
                      value={paymentMethod}
                      onChange={(e) => setPaymentMethod(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#E5E0D3] text-xs text-[#18211F] focus:outline-none focus:border-[#063B32] font-sans"
                    >
                      <option value="UPI_TRANSFER">UPI Transfer (Google Pay / PhonePe / Paytm)</option>
                      <option value="BANK_TRANSFER">Bank IMPS / NEFT Transfer</option>
                      <option value="CASH_DEPOSIT">Cash / Direct Upline Settlement</option>
                    </select>
                  </div>

                  {/* UPI QR Code Payment Card */}
                  {paymentMethod === 'UPI_TRANSFER' && (
                    <UpiQrPaymentCard
                      amount={statusData?.package?.price || 35400}
                      upiId={statusData?.upi_details?.upi_id || 'mystatusads@icici'}
                      payeeName={statusData?.upi_details?.payee_name || recipient?.full_name || 'MyStatus Platform'}
                      transactionNote={`Package Activation ${user?.user_code || ''}`}
                      customQrImageUrl={statusData?.upi_details?.qr_image_url || '/payment-qr.png'}
                      packageTitle={statusData?.package?.name || 'Premium Sub Franchise (₹35,400)'}
                    />
                  )}

                  {/* Bank Transfer Details Card */}
                  {paymentMethod === 'BANK_TRANSFER' && (
                    <div className="p-4 rounded-2xl bg-[#F7F4EC] border border-[#8DCFBF] space-y-2.5 text-xs">
                      <div className="flex items-center gap-1.5 font-bold text-[#063B32]">
                        <Building2 className="w-4 h-4 text-[#063B32]" />
                        <span>Official Bank Account Details</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 font-mono text-[11px]">
                        <div className="p-2.5 bg-white rounded-xl border border-[#E5E0D3]">
                          <span className="text-[10px] text-[#69736F] font-sans block">Bank Name:</span>
                          <strong className="text-[#18211F]">ICICI Bank Ltd</strong>
                        </div>
                        <div className="p-2.5 bg-white rounded-xl border border-[#E5E0D3]">
                          <span className="text-[10px] text-[#69736F] font-sans block">Account Holder:</span>
                          <strong className="text-[#18211F]">MyStatus Media & Ent Pvt Ltd</strong>
                        </div>
                        <div className="p-2.5 bg-white rounded-xl border border-[#E5E0D3]">
                          <span className="text-[10px] text-[#69736F] font-sans block">Account Number:</span>
                          <strong className="text-[#18211F] text-xs">123405009988</strong>
                        </div>
                        <div className="p-2.5 bg-white rounded-xl border border-[#E5E0D3]">
                          <span className="text-[10px] text-[#69736F] font-sans block">IFSC Code:</span>
                          <strong className="text-[#18211F] text-xs">ICIC0001234</strong>
                        </div>
                      </div>
                      <p className="text-[10px] text-[#69736F] pt-1">
                        Transfer ₹{(statusData?.package?.price || 35400).toLocaleString()} via IMPS / NEFT, then enter the transaction UTR below.
                      </p>
                    </div>
                  )}

                  {/* Cash Settlement Card */}
                  {paymentMethod === 'CASH_DEPOSIT' && (
                    <div className="p-4 rounded-2xl bg-[#FAF4DC] border border-[#E2C766] text-xs space-y-1.5 text-[#8C6C16]">
                      <span className="font-bold flex items-center gap-1.5">
                        <AlertCircle className="w-4 h-4 text-[#C9A227]" />
                        Cash Settlement with Sponsor / Franchise Hub
                      </span>
                      <p className="text-[11px] leading-relaxed">
                        Hand over cash directly to your authorized sponsor (<strong>{recipient?.full_name}</strong> - {recipient?.user_code}) or visit the nearest authorized franchise hub. Enter the issued receipt or voucher code below.
                      </p>
                    </div>
                  )}

                  <div>
                    <label className="block text-xs font-bold text-[#18211F] mb-1">
                      Transaction Reference / UTR Number <span className="text-[#C88A16]">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. UTR-20260829-123456 or Txn ID"
                      value={paymentRef}
                      onChange={(e) => setPaymentRef(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#E5E0D3] text-xs font-mono text-[#18211F] focus:outline-none focus:border-[#063B32]"
                    />
                    <p className="text-[10px] text-[#69736F] mt-1">
                      Enter the exact transaction reference/UTR provided by your banking or UPI app.
                    </p>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setActiveStep(isPinIssued ? 'PIN' : 'OVERVIEW')}
                    className="flex-1 px-4 py-3 rounded-2xl border border-[#E5E0D3] hover:bg-[#EFECE2] text-[#18211F] text-xs font-semibold transition-colors cursor-pointer"
                  >
                    Back
                  </button>
                  <button
                    type="submit"
                    disabled={submittingPayment || !paymentRef.trim()}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/30 text-xs font-heading font-bold shadow-wealth-card transition-all disabled:opacity-50 cursor-pointer"
                  >
                    {submittingPayment ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-[#C9A227]" />
                        <span>Submitting...</span>
                      </>
                    ) : (
                      <>
                        <CreditCard className="w-4 h-4 text-[#C9A227]" />
                        <span>{isPaymentSubmitted ? 'Update Payment Ref' : 'Submit Payment Request'}</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Quick link to enter PIN if user already has it */}
                <div className="text-center pt-1">
                  <button
                    type="button"
                    onClick={() => setActiveStep('PIN')}
                    className="text-xs text-[#063B32] font-bold hover:underline cursor-pointer inline-flex items-center gap-1"
                  >
                    <KeyRound className="w-3.5 h-3.5 text-[#C9A227]" />
                    <span>Already received your Security PIN? Enter it here &rarr;</span>
                  </button>
                </div>
              </form>
            )}

            {/* STEP 3: ENTER SECURITY PIN & ACTIVATE */}
            {activeStep === 'PIN' && (
              <form onSubmit={handleActivateWithPin} className="space-y-4">
                {/* Ready Banner */}
                <div className="p-4 rounded-2xl bg-[#FAF4DC] border border-[#E2C766] text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#8C6C16] flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-[#C9A227]" />
                      Package Ready for PIN Activation
                    </span>
                    <span className="bg-[#E0F3EE] text-[#063B32] px-2.5 py-0.5 rounded-full font-bold text-[10px] font-mono">
                      {isPinIssued ? 'PIN ISSUED' : 'VERIFIED'}
                    </span>
                  </div>
                  <p className="text-[#69736F] text-[11px] leading-relaxed">
                    Your payment has been verified. Enter the 8-character single-use Security PIN provided by your Admin or Sponsor to immediately activate your ₹{(statusData?.package?.price || 35400).toLocaleString()} package and generate 30,000 personal BV.
                  </p>
                </div>

                {/* PIN Input */}
                <div className="space-y-2">
                  <label className="block text-xs font-bold text-[#18211F]">
                    Enter 8-Character Security PIN <span className="text-[#C88A16]">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      required
                      maxLength={16}
                      autoFocus
                      placeholder="e.g. 7K9M2X4W"
                      value={securityPin}
                      onChange={(e) => setSecurityPin(e.target.value.toUpperCase())}
                      className="w-full px-4 py-3.5 rounded-2xl bg-white border-2 border-[#C9A227]/60 text-lg font-mono font-black text-center tracking-[0.25em] text-[#063B32] placeholder:text-[#69736F]/40 placeholder:tracking-normal focus:outline-none focus:border-[#063B32] shadow-xs"
                    />
                    <KeyRound className="w-5 h-5 text-[#C9A227] absolute right-4 top-1/2 -translate-y-1/2" />
                  </div>
                  <div className="flex items-center gap-1.5 text-[10px] text-[#69736F]">
                    <ShieldCheck className="w-3.5 h-3.5 text-[#0E9F6E]" />
                    <span>Single-use security token with 5-attempt rate protection.</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setActiveStep('PAYMENT')}
                    className="flex-1 px-4 py-3 rounded-2xl border border-[#E5E0D3] hover:bg-[#EFECE2] text-[#18211F] text-xs font-semibold transition-colors cursor-pointer"
                  >
                    Back
                  </button>
                  <button
                    type="submit"
                    disabled={activatingPin || !securityPin.trim()}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/40 text-xs font-heading font-black shadow-wealth-card transition-all transform hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 cursor-pointer"
                  >
                    {activatingPin ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-[#C9A227]" />
                        <span>Verifying PIN...</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-4 h-4 text-[#C9A227]" />
                        <span>ACTIVATE PACKAGE NOW</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}
          </div>
        ) : (
          /* SUCCESS STATE */
          <div className="text-center py-4">
            <div className="w-16 h-16 rounded-2xl bg-[#FAF4DC] border border-[#E2C766] text-[#8C6C16] flex items-center justify-center mx-auto mb-4 animate-bounce">
              <CheckCircle2 className="w-10 h-10 text-[#063B32]" />
            </div>

            <h3 className="text-2xl font-heading font-extrabold text-[#18211F] mb-1">
              Package Activated Successfully!
            </h3>
            <p className="text-[#063B32] font-bold text-sm mb-4">
              ₹{(successEvent.purchase?.amount || statusData?.package?.price || 35400).toLocaleString()} Sub Franchise Package (+30,000 BV) is now Active
            </p>

            <div className="p-4 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] mb-6 text-left space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-[#69736F] font-medium">Purchase Code:</span>
                <span className="font-mono text-[#18211F] font-bold">{successEvent.purchase?.purchase_code}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#69736F] font-medium">Personal BV Added:</span>
                <span className="text-[#063B32] font-bold font-mono">+30,000 BV</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#69736F] font-medium">Account Status:</span>
                <span className="text-[#063B32] font-semibold flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-[#0E9F6E]" />
                  Active Wealth Distributor
                </span>
              </div>
              {successEvent.events && successEvent.events.length > 0 && (
                <div className="pt-2 border-t border-[#E5E0D3]">
                  <div className="text-[#18211F] mb-1 font-semibold">Commissions Processed:</div>
                  {successEvent.events.map((ev: any, idx: number) => (
                    <div key={idx} className="text-[#69736F] flex justify-between">
                      <span>• {ev.type === 'DIRECT_REFERRAL' ? 'Direct Sponsor Bonus' : 'Pair Bonus'} to {ev.beneficiary}</span>
                      <span className="text-[#0E9F6E] font-mono font-bold">+₹{ev.amount?.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={handleClose}
              className="w-full py-3.5 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/30 text-xs font-bold font-heading transition-colors cursor-pointer"
            >
              Continue to Wealth Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

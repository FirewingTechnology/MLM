import React, { useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import {
  QrCode,
  Copy,
  Check,
  ExternalLink,
  Smartphone,
  ShieldCheck,
  Sparkles,
  Info,
  Image as ImageIcon
} from 'lucide-react';
import { useToast } from '../../context/ToastContext';

interface UpiQrPaymentCardProps {
  amount?: number;
  upiId?: string;
  payeeName?: string;
  transactionNote?: string;
  customQrImageUrl?: string;
  packageTitle?: string;
}

export const UpiQrPaymentCard: React.FC<UpiQrPaymentCardProps> = ({
  amount = 35400,
  upiId = 'mystatusads@icici',
  payeeName = 'MyStatus Platform',
  transactionNote = 'Sub Franchise Package Activation',
  customQrImageUrl = '/payment-qr.png',
  packageTitle = 'Premium Sub Franchise (₹35,400)'
}) => {
  const { showToast } = useToast();
  const [copiedUpi, setCopiedUpi] = useState(false);
  const [copiedAmount, setCopiedAmount] = useState(false);
  const [imgError, setImgError] = useState(false);

  // Standard NPCI UPI URI
  const upiUri = `upi://pay?pa=${encodeURIComponent(upiId)}&pn=${encodeURIComponent(
    payeeName
  )}&cu=INR`;

  const handleCopyUpi = () => {
    navigator.clipboard.writeText(upiId);
    setCopiedUpi(true);
    showToast('UPI ID copied to clipboard!', 'success');
    setTimeout(() => setCopiedUpi(false), 2500);
  };

  const handleCopyAmount = () => {
    navigator.clipboard.writeText(amount.toString());
    setCopiedAmount(true);
    showToast('Amount copied to clipboard!', 'success');
    setTimeout(() => setCopiedAmount(false), 2500);
  };

  return (
    <div className="rounded-2xl bg-[#FFFEF9] border-2 border-[#E2C766] p-4 sm:p-5 shadow-wealth-card space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#E5E0D3] pb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-[#FAF4DC] border border-[#E2C766] text-[#8C6C16] flex items-center justify-center">
            <QrCode className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-heading font-extrabold text-[#18211F] uppercase tracking-wider flex items-center gap-1.5">
              <span>Scan & Pay via UPI</span>
              <span className="text-[10px] font-mono font-bold bg-[#E0F3EE] text-[#063B32] border border-[#8DCFBF] px-2 py-0.5 rounded-full">
                STATIC QR
              </span>
            </h4>
            <p className="text-[11px] text-[#69736F]">
              Scan with PhonePe, Google Pay, Paytm or any UPI App
            </p>
          </div>
        </div>
      </div>

      {/* QR Code Container */}
      <div className="flex flex-col sm:flex-row items-center gap-4 bg-[#F7F4EC]/60 p-4 rounded-2xl border border-[#E5E0D3]">
        {/* The Static QR Box */}
        <div className="relative p-3 bg-white rounded-2xl border border-[#E2C766] shadow-xs flex flex-col items-center justify-center shrink-0">
          <div className="w-40 h-40 flex items-center justify-center overflow-hidden rounded-xl bg-white">
            {!imgError ? (
              <img
                src={customQrImageUrl}
                alt="Static Payment QR Code"
                onError={() => setImgError(true)}
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="flex flex-col items-center justify-center p-3 text-[#69736F] text-center">
                <QrCode className="w-12 h-12 text-[#C9A227] mb-1" />
                <span className="text-[11px] font-bold">Static QR Code</span>
                <span className="text-[9px] font-mono text-[#8C6C16]">{customQrImageUrl}</span>
              </div>
            )}
          </div>

          {/* Scannable Badge */}
          <div className="mt-2 text-[9px] font-mono font-bold uppercase tracking-wider text-[#8C6C16] bg-[#FAF4DC] px-2 py-0.5 rounded-md border border-[#E2C766]/60 flex items-center gap-1">
            <Sparkles className="w-2.5 h-2.5 text-[#C9A227]" />
            <span>Official Payment Standee</span>
          </div>
        </div>

        {/* Payment Details & Actions */}
        <div className="flex-1 space-y-3 w-full text-xs">
          {/* Amount Box */}
          <div className="flex items-center justify-between p-2.5 bg-white rounded-xl border border-[#E5E0D3]">
            <div>
              <span className="text-[10px] uppercase font-bold text-[#69736F] block">Payable Amount</span>
              <span className="text-xl font-heading font-black text-[#063B32] font-mono">
                ₹{amount.toLocaleString()}
              </span>
            </div>
            <button
              type="button"
              onClick={handleCopyAmount}
              className="flex items-center gap-1 text-[11px] font-bold text-[#063B32] hover:text-[#042C26] bg-[#E0F3EE] px-2.5 py-1.5 rounded-lg border border-[#8DCFBF] cursor-pointer transition-colors"
            >
              {copiedAmount ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedAmount ? 'Copied' : 'Copy'}</span>
            </button>
          </div>

          {/* UPI ID Box */}
          <div className="p-2.5 bg-white rounded-xl border border-[#E5E0D3] space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-bold text-[#69736F]">Official UPI ID</span>
              <button
                type="button"
                onClick={handleCopyUpi}
                className="flex items-center gap-1 text-[11px] font-bold text-[#8C6C16] hover:text-[#6D530F] bg-[#FAF4DC] px-2 py-0.5 rounded-md border border-[#E2C766] cursor-pointer transition-colors"
              >
                {copiedUpi ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                <span>{copiedUpi ? 'Copied' : 'Copy UPI'}</span>
              </button>
            </div>
            <div className="font-mono font-bold text-[#18211F] text-xs break-all select-all">
              {upiId}
            </div>
            <div className="text-[10px] text-[#69736F]">
              Payee: <strong className="text-[#18211F]">{payeeName}</strong>
            </div>
          </div>

          {/* Direct Mobile Deep Link (for users paying directly from mobile device) */}
          <a
            href={upiUri}
            className="flex items-center justify-center gap-1.5 w-full py-2 px-3 rounded-xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] font-bold text-[11px] shadow-xs cursor-pointer transition-colors"
          >
            <Smartphone className="w-3.5 h-3.5 text-[#C9A227]" />
            <span>Open in UPI App (PhonePe / GPay)</span>
            <ExternalLink className="w-3 h-3 opacity-70" />
          </a>
        </div>
      </div>

      {/* UPI App Logos & Guidance */}
      <div className="space-y-2 pt-1">
        <div className="flex flex-wrap items-center justify-between text-[11px] text-[#69736F] px-1">
          <span className="font-medium">Supported Apps:</span>
          <span className="font-semibold text-[#18211F]">Google Pay • PhonePe • Paytm • BHIM • Cred • Any Bank UPI</span>
        </div>

        <div className="p-3 rounded-xl bg-[#FAF4DC]/60 border border-[#E2C766]/60 text-[#8C6C16] text-[11px] flex items-start gap-2">
          <Info className="w-3.5 h-3.5 text-[#C9A227] shrink-0 mt-0.5" />
          <div>
            <strong>After paying:</strong> Please copy the <strong>12-digit UTR / Reference Number</strong> from your payment receipt and paste it in the field below to verify your request.
          </div>
        </div>
      </div>
    </div>
  );
};

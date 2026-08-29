import React, { useState, useEffect } from 'react';
import {
  X,
  KeyRound,
  Send,
  DownloadCloud,
  ArrowRightLeft,
  Clock,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  Users,
  Copy,
  Check,
  History,
  Inbox,
  Sparkles
} from 'lucide-react';
import api from '../../services/api';
import {
  PinWalletData,
  EligibleDownlineUser,
  SecurityPinOrder,
  SecurityPinUplineRequest,
  SecurityPinTransfer,
  SecurityPinLedgerEntry
} from '../../types';

interface PinWalletModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTab?: 'overview' | 'buy' | 'give' | 'request' | 'incoming' | 'history';
  onSuccess?: () => void;
}

export const PinWalletModal: React.FC<PinWalletModalProps> = ({
  isOpen,
  onClose,
  initialTab = 'overview',
  onSuccess
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'buy' | 'give' | 'request' | 'incoming' | 'history'>(initialTab);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Data states
  const [inventory, setInventory] = useState<PinWalletData | null>(null);
  const [downlines, setDownlines] = useState<EligibleDownlineUser[]>([]);
  const [orders, setOrders] = useState<SecurityPinOrder[]>([]);
  const [uplineRequests, setUplineRequests] = useState<{ incoming: SecurityPinUplineRequest[]; outgoing: SecurityPinUplineRequest[] }>({
    incoming: [],
    outgoing: []
  });
  const [historyData, setHistoryData] = useState<{ transfers: SecurityPinTransfer[]; ledger: SecurityPinLedgerEntry[] }>({
    transfers: [],
    ledger: []
  });

  // Buy form states
  const [buyQuantity, setBuyQuantity] = useState<number>(1);
  const [customQuantity, setCustomQuantity] = useState<string>('');
  const [paymentMethod, setPaymentMethod] = useState<string>('UPI_TRANSFER');
  const [paymentReference, setPaymentReference] = useState<string>('');
  const [submittingBuy, setSubmittingBuy] = useState(false);

  // Give form states
  const [selectedRecipient, setSelectedRecipient] = useState<string>('');
  const [giveQuantity, setGiveQuantity] = useState<number>(1);
  const [giveReason, setGiveReason] = useState<string>('Downline Package Activation');
  const [submittingGive, setSubmittingGive] = useState(false);
  const [giveConfirmOpen, setGiveConfirmOpen] = useState(false);

  // Request form states
  const [requestQuantity, setRequestQuantity] = useState<number>(1);
  const [requestNotes, setRequestNotes] = useState<string>('');
  const [submittingRequest, setSubmittingRequest] = useState(false);

  // Activation states
  const [activating, setActivating] = useState(false);
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const pricePerPin = 35000;

  useEffect(() => {
    if (isOpen) {
      setActiveTab(initialTab);
      loadAllData();
    }
  }, [isOpen, initialTab]);

  const loadAllData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [invRes, downlinesRes, ordersRes, reqsRes, histRes] = await Promise.allSettled([
        api.get('/security-pins/inventory'),
        api.get('/security-pins/downline-eligible'),
        api.get('/security-pins/orders'),
        api.get('/security-pins/upline-requests'),
        api.get('/security-pins/history')
      ]);

      if (invRes.status === 'fulfilled' && invRes.value.data?.data) {
        setInventory(invRes.value.data.data);
      }
      if (downlinesRes.status === 'fulfilled' && downlinesRes.value.data?.data) {
        setDownlines(downlinesRes.value.data.data);
      }
      if (ordersRes.status === 'fulfilled' && ordersRes.value.data?.data) {
        setOrders(ordersRes.value.data.data);
      }
      if (reqsRes.status === 'fulfilled' && reqsRes.value.data?.data) {
        setUplineRequests(reqsRes.value.data.data);
      }
      if (histRes.status === 'fulfilled' && histRes.value.data?.data) {
        setHistoryData(histRes.value.data.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load Security PIN wallet.');
    } finally {
      setLoading(false);
    }
  };

  const handleBuySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!paymentReference.trim()) {
      setError('Please enter your transaction reference / UTR.');
      return;
    }
    const finalQty = customQuantity ? parseInt(customQuantity) || 1 : buyQuantity;
    setSubmittingBuy(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const res = await api.post('/security-pins/orders', {
        package_id: 1,
        quantity: finalQty,
        payment_method: paymentMethod,
        payment_reference: paymentReference.trim()
      });
      setSuccessMsg(res.data?.message || `Successfully placed order for ${finalQty} PIN(s)!`);
      setPaymentReference('');
      setCustomQuantity('');
      loadAllData();
      setTimeout(() => setActiveTab('overview'), 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Failed to submit PIN order.');
    } finally {
      setSubmittingBuy(false);
    }
  };

  const handleGiveSubmit = async () => {
    if (!selectedRecipient) {
      setError('Please select a recipient from your downline.');
      return;
    }
    setSubmittingGive(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const res = await api.post('/security-pins/transfer', {
        to_user_identifier: selectedRecipient,
        quantity: giveQuantity,
        reason: giveReason
      });
      setSuccessMsg(res.data?.message || 'PIN(s) transferred successfully!');
      setGiveConfirmOpen(false);
      setSelectedRecipient('');
      setGiveQuantity(1);
      loadAllData();
      if (onSuccess) onSuccess();
      setTimeout(() => setActiveTab('overview'), 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Failed to transfer PIN.');
    } finally {
      setSubmittingGive(false);
    }
  };

  const handleUseOwnPin = async (pinId?: number) => {
    setActivating(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const res = await api.post('/security-pins/use', {
        pin_id: pinId
      });
      setSuccessMsg(res.data?.message || 'Package activated successfully! 30,000 BV credited.');
      loadAllData();
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Failed to activate package.');
    } finally {
      setActivating(false);
    }
  };

  const handleRequestUplineSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingRequest(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const res = await api.post('/security-pins/request-from-upline', {
        quantity: requestQuantity,
        notes: requestNotes
      });
      setSuccessMsg(res.data?.message || 'PIN Request sent to sponsor!');
      setRequestNotes('');
      loadAllData();
      setTimeout(() => setActiveTab('overview'), 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Failed to send PIN request.');
    } finally {
      setSubmittingRequest(false);
    }
  };

  const handleApproveRequest = async (requestId: number) => {
    setLoading(true);
    setError(null);
    try {
      await api.post(`/security-pins/upline-requests/${requestId}/approve`);
      setSuccessMsg('Request approved and PIN transferred!');
      loadAllData();
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Failed to approve request.');
    } finally {
      setLoading(false);
    }
  };

  const handleRejectRequest = async (requestId: number) => {
    setLoading(true);
    setError(null);
    try {
      await api.post(`/security-pins/upline-requests/${requestId}/reject`, { notes: 'Declined by upline' });
      setSuccessMsg('Request rejected.');
      loadAllData();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Failed to reject request.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string, id: number) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (!isOpen) return null;

  const availableCount = inventory?.wallet?.available || 0;
  const isUserActive = inventory?.user?.is_active ?? false;
  const effectiveBuyQty = customQuantity ? parseInt(customQuantity) || 1 : buyQuantity;
  const totalBuyPrice = effectiveBuyQty * pricePerPin;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-4xl max-h-[92vh] flex flex-col bg-[#FFFEF9] rounded-3xl border border-[#E5E0D3] shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#E5E0D3] bg-[#F7F4EC]/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#063B32] text-[#FFFEF9] flex items-center justify-center shadow-md">
              <KeyRound className="w-5 h-5 text-[#C9A227]" />
            </div>
            <div>
              <h2 className="text-lg font-heading font-extrabold text-[#18211F] flex items-center gap-2">
                Security PIN Wallet
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#FAF4DC] text-[#8C6C16] border border-[#E2C766] font-mono">
                  Prepaid Inventory
                </span>
              </h2>
              <p className="text-xs text-[#69736F]">
                Manage prepaid activation credits, distribute to downlines, and fulfill member requests.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-[#69736F] hover:text-[#18211F] hover:bg-[#E5E0D3]/60 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Wallet Balance Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 p-4 bg-[#063B32] text-[#FFFEF9]">
          <div className="p-2.5 rounded-2xl bg-white/10 border border-white/10 text-center">
            <div className="text-[10px] text-white/70 font-bold uppercase tracking-wider">Available</div>
            <div className="text-xl font-heading font-black text-[#C9A227] font-mono">{availableCount}</div>
          </div>
          <div className="p-2.5 rounded-2xl bg-white/10 border border-white/10 text-center">
            <div className="text-[10px] text-white/70 font-bold uppercase tracking-wider">Used</div>
            <div className="text-xl font-heading font-black text-white font-mono">{inventory?.wallet?.used || 0}</div>
          </div>
          <div className="p-2.5 rounded-2xl bg-white/10 border border-white/10 text-center">
            <div className="text-[10px] text-white/70 font-bold uppercase tracking-wider">Transferred</div>
            <div className="text-xl font-heading font-black text-emerald-300 font-mono">{inventory?.wallet?.transferred || 0}</div>
          </div>
          <div className="p-2.5 rounded-2xl bg-white/10 border border-white/10 text-center">
            <div className="text-[10px] text-white/70 font-bold uppercase tracking-wider">Received</div>
            <div className="text-xl font-heading font-black text-blue-300 font-mono">{inventory?.wallet?.received || 0}</div>
          </div>
          <div className="p-2.5 rounded-2xl bg-white/10 border border-white/10 text-center col-span-2 sm:col-span-1">
            <div className="text-[10px] text-white/70 font-bold uppercase tracking-wider">Downline Reqs</div>
            <div className="text-xl font-heading font-black text-amber-300 font-mono">
              {inventory?.wallet?.pending_downline_requests || 0}
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1 px-6 pt-3 border-b border-[#E5E0D3] bg-[#FFFEF9] overflow-x-auto">
          {[
            { id: 'overview', label: 'PIN Inventory', icon: KeyRound },
            { id: 'buy', label: 'Get PINs (Admin)', icon: DownloadCloud },
            { id: 'give', label: 'Give PIN to Downline', icon: Send },
            { id: 'request', label: 'Request from Upline', icon: ArrowRightLeft },
            {
              id: 'incoming',
              label: `Downline Requests (${inventory?.wallet?.pending_downline_requests || 0})`,
              icon: Inbox
            },
            { id: 'history', label: 'Ledger & Transfers', icon: History },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id as any);
                  setError(null);
                  setSuccessMsg(null);
                }}
                className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-bold whitespace-nowrap border-b-2 transition-all cursor-pointer ${
                  isActive
                    ? 'border-[#063B32] text-[#063B32] bg-[#F7F4EC]/80 rounded-t-xl'
                    : 'border-transparent text-[#69736F] hover:text-[#18211F]'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Modal Body */}
        <div className="flex-1 p-6 overflow-y-auto space-y-4">
          {/* Notifications */}
          {error && (
            <div className="p-3.5 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2.5">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-3.5 rounded-2xl bg-[#E0F3EE] border border-[#8DCFBF] text-[#063B32] text-xs flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span className="font-bold">{successMsg}</span>
            </div>
          )}

          {/* TAB 1: OVERVIEW & AVAILABLE PINS */}
          {activeTab === 'overview' && (
            <div className="space-y-5">
              {/* Account Activation Callout if Inactive */}
              {!isUserActive && (
                <div className="p-4 rounded-3xl bg-gradient-to-r from-[#FAF4DC] to-[#F7F4EC] border border-[#E2C766] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-[#C9A227] text-white flex items-center justify-center font-bold">
                      <Sparkles className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="font-extrabold text-[#18211F] text-sm">Account Inactive (Pending Activation)</div>
                      <div className="text-xs text-[#69736F]">
                        {availableCount > 0
                          ? 'You have available PINs in your wallet! Click below to activate now.'
                          : 'Get a PIN from Admin or your Sponsor to activate your account and start earning BV.'}
                      </div>
                    </div>
                  </div>
                  {availableCount > 0 ? (
                    <button
                      onClick={() => handleUseOwnPin()}
                      disabled={activating}
                      className="px-4 py-2 rounded-2xl bg-[#063B32] hover:bg-[#063B32]/90 text-[#FFFEF9] text-xs font-extrabold shadow-sm transition-all cursor-pointer"
                    >
                      {activating ? 'Activating...' : '⚡ ACTIVATE WITH MY PIN'}
                    </button>
                  ) : (
                    <button
                      onClick={() => setActiveTab('buy')}
                      className="px-4 py-2 rounded-2xl bg-[#063B32] hover:bg-[#063B32]/90 text-[#FFFEF9] text-xs font-extrabold shadow-sm transition-all cursor-pointer"
                    >
                      GET PINS NOW
                    </button>
                  )}
                </div>
              )}

              {/* Quick Action Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <button
                  onClick={() => setActiveTab('buy')}
                  className="p-4 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] hover:border-[#063B32] hover:shadow-md transition-all text-left group cursor-pointer"
                >
                  <div className="w-8 h-8 rounded-xl bg-[#E0F3EE] text-[#063B32] flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                    <DownloadCloud className="w-4 h-4" />
                  </div>
                  <div className="font-bold text-xs text-[#18211F]">Get PINs from Admin</div>
                  <div className="text-[10px] text-[#69736F]">Purchase bulk activation inventory</div>
                </button>

                <button
                  onClick={() => setActiveTab('give')}
                  className="p-4 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] hover:border-[#063B32] hover:shadow-md transition-all text-left group cursor-pointer"
                >
                  <div className="w-8 h-8 rounded-xl bg-[#FAF4DC] text-[#8C6C16] flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                    <Send className="w-4 h-4" />
                  </div>
                  <div className="font-bold text-xs text-[#18211F]">Give PIN to Downline</div>
                  <div className="text-[10px] text-[#69736F]">Transfer credit to network members</div>
                </button>

                <button
                  onClick={() => setActiveTab('request')}
                  className="p-4 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] hover:border-[#063B32] hover:shadow-md transition-all text-left group cursor-pointer"
                >
                  <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-800 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                    <ArrowRightLeft className="w-4 h-4" />
                  </div>
                  <div className="font-bold text-xs text-[#18211F]">Request from Sponsor</div>
                  <div className="text-[10px] text-[#69736F]">Ask upline leader for a PIN</div>
                </button>
              </div>

              {/* Available PINs Table */}
              <div className="rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] p-4 space-y-3">
                <div className="flex items-center justify-between border-b border-[#E5E0D3] pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-[#18211F]">Available Security PINs in Wallet</h3>
                    <p className="text-[10px] text-[#69736F]">
                      Ready for self-activation or transfer to downline members.
                    </p>
                  </div>
                  <span className="text-xs font-mono font-bold bg-[#E0F3EE] text-[#063B32] px-2.5 py-1 rounded-xl">
                    {availableCount} Available
                  </span>
                </div>

                {inventory?.available_pins && inventory.available_pins.length > 0 ? (
                  <div className="divide-y divide-[#E5E0D3]/60">
                    {inventory.available_pins.map((pin) => (
                      <div key={pin.id} className="py-2.5 flex items-center justify-between gap-3 hover:bg-[#F7F4EC]/50 px-2 rounded-xl">
                        <div className="flex items-center gap-2.5">
                          <KeyRound className="w-4 h-4 text-[#C9A227]" />
                          <div>
                            <div className="font-mono font-bold text-xs text-[#18211F]">{pin.masked_code || pin.pin_code}</div>
                            <div className="text-[10px] text-[#69736F]">
                              ₹{pin.amount?.toLocaleString()} • {pin.bv?.toLocaleString()} BV • Expires {pin.expires_at ? new Date(pin.expires_at).toLocaleDateString() : 'in 30 days'}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          {!isUserActive && (
                            <button
                              onClick={() => handleUseOwnPin(pin.id)}
                              disabled={activating}
                              className="px-2.5 py-1 rounded-xl bg-[#063B32] text-[#FFFEF9] text-[10px] font-bold hover:bg-[#063B32]/90 cursor-pointer"
                            >
                              Use This PIN
                            </button>
                          )}
                          <button
                            onClick={() => {
                              setActiveTab('give');
                            }}
                            className="px-2.5 py-1 rounded-xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#063B32] text-[10px] font-bold hover:bg-[#E5E0D3] cursor-pointer"
                          >
                            Transfer
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-8 text-center text-xs text-[#69736F] space-y-2">
                    <KeyRound className="w-8 h-8 text-[#C9A227]/40 mx-auto" />
                    <div>No available Security PINs currently in your wallet.</div>
                    <button
                      onClick={() => setActiveTab('buy')}
                      className="px-3 py-1.5 rounded-xl bg-[#063B32] text-[#FFFEF9] text-xs font-bold"
                    >
                      Purchase PINs from Admin
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: BUY PINS FROM ADMIN */}
          {activeTab === 'buy' && (
            <form onSubmit={handleBuySubmit} className="space-y-4">
              <div className="p-4 rounded-3xl bg-[#F7F4EC]/70 border border-[#E5E0D3] space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase text-[#69736F]">Selected Package</span>
                  <span className="text-xs font-bold text-[#063B32]">₹35,000 / 30,000 BV per PIN</span>
                </div>

                {/* Quantity Selectors */}
                <div>
                  <label className="block text-xs font-bold text-[#18211F] mb-1.5">Select Quantity:</label>
                  <div className="grid grid-cols-4 gap-2 mb-2">
                    {[1, 5, 10, 20].map((qty) => (
                      <button
                        key={qty}
                        type="button"
                        onClick={() => {
                          setBuyQuantity(qty);
                          setCustomQuantity('');
                        }}
                        className={`py-2 rounded-2xl text-xs font-mono font-bold transition-all cursor-pointer ${
                          buyQuantity === qty && !customQuantity
                            ? 'bg-[#063B32] text-[#FFFEF9] shadow-sm'
                            : 'bg-[#FFFEF9] text-[#18211F] border border-[#E5E0D3]'
                        }`}
                      >
                        {qty} {qty === 1 ? 'PIN' : 'PINs'}
                      </button>
                    ))}
                  </div>

                  <input
                    type="number"
                    min="1"
                    max="500"
                    placeholder="Or enter custom quantity (e.g. 50)"
                    value={customQuantity}
                    onChange={(e) => setCustomQuantity(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-2xl bg-[#FFFEF9] border border-[#E5E0D3] text-xs font-mono focus:border-[#063B32] focus:outline-none"
                  />
                </div>

                {/* Amount Summary */}
                <div className="p-3.5 rounded-2xl bg-[#FFFEF9] border border-[#E5E0D3] flex items-center justify-between">
                  <div>
                    <div className="text-[10px] text-[#69736F] font-bold uppercase">Total Payable</div>
                    <div className="text-xs text-[#18211F]">
                      {effectiveBuyQty} × ₹{pricePerPin.toLocaleString()}
                    </div>
                  </div>
                  <div className="text-lg font-heading font-black text-[#063B32] font-mono">
                    ₹{totalBuyPrice.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Payment Details Form */}
              <div className="p-4 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] space-y-3">
                <h4 className="text-xs font-bold text-[#18211F] uppercase tracking-wider">Payment Reference</h4>

                <div>
                  <label className="block text-xs font-bold text-[#18211F] mb-1">Payment Method</label>
                  <select
                    value={paymentMethod}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-2xl bg-[#F7F4EC]/50 border border-[#E5E0D3] text-xs font-bold focus:border-[#063B32] focus:outline-none"
                  >
                    <option value="UPI_TRANSFER">UPI Transfer / GPay / PhonePe</option>
                    <option value="BANK_NEFT_IMPS">Bank NEFT / IMPS Transfer</option>
                    <option value="CASH_DEPOSIT">Cash Deposit at Franchise Hub</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#18211F] mb-1">
                    Transaction Reference / UTR Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. UPI-9988223344 or Bank UTR Ref"
                    value={paymentReference}
                    onChange={(e) => setPaymentReference(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-2xl bg-[#F7F4EC]/50 border border-[#E5E0D3] text-xs font-mono font-bold focus:border-[#063B32] focus:outline-none"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={submittingBuy}
                className="w-full py-3 rounded-2xl bg-[#063B32] hover:bg-[#063B32]/90 text-[#FFFEF9] text-xs font-bold shadow-md transition-all cursor-pointer disabled:opacity-50"
              >
                {submittingBuy ? 'Submitting Order...' : `REQUEST ${effectiveBuyQty} SECURITY PIN(S) (₹${totalBuyPrice.toLocaleString()})`}
              </button>
            </form>
          )}

          {/* TAB 3: GIVE PIN TO DOWNLINE */}
          {activeTab === 'give' && (
            <div className="space-y-4">
              <div className="p-4 rounded-3xl bg-[#FAF4DC]/60 border border-[#E2C766] flex items-center gap-3">
                <ShieldCheck className="w-5 h-5 text-[#8C6C16] flex-shrink-0" />
                <div className="text-xs text-[#8C6C16]">
                  <strong>Downline Eligibility Rule:</strong> You can only give PINs to members in your own registered downline binary or sponsor tree.
                </div>
              </div>

              <div className="p-4 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] space-y-3">
                <div>
                  <label className="block text-xs font-bold text-[#18211F] mb-1">
                    Select Downline Recipient: <span className="text-red-500">*</span>
                  </label>
                  {downlines.length > 0 ? (
                    <select
                      value={selectedRecipient}
                      onChange={(e) => setSelectedRecipient(e.target.value)}
                      className="w-full px-3.5 py-2 rounded-2xl bg-[#F7F4EC]/50 border border-[#E5E0D3] text-xs font-bold focus:border-[#063B32] focus:outline-none"
                    >
                      <option value="">-- Choose Member from Downline ({downlines.length} available) --</option>
                      {downlines.map((d) => (
                        <option key={d.id} value={d.user_code}>
                          {d.full_name} ({d.user_code}) {d.is_active ? '• Active' : '• Inactive'}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      placeholder="Enter Member User Code or Email"
                      value={selectedRecipient}
                      onChange={(e) => setSelectedRecipient(e.target.value)}
                      className="w-full px-3.5 py-2 rounded-2xl bg-[#F7F4EC]/50 border border-[#E5E0D3] text-xs font-bold focus:border-[#063B32] focus:outline-none"
                    />
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-[#18211F] mb-1">Quantity</label>
                    <input
                      type="number"
                      min="1"
                      max={availableCount || 1}
                      value={giveQuantity}
                      onChange={(e) => setGiveQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                      className="w-full px-3.5 py-2 rounded-2xl bg-[#F7F4EC]/50 border border-[#E5E0D3] text-xs font-mono font-bold focus:border-[#063B32] focus:outline-none"
                    />
                    <span className="text-[10px] text-[#69736F] mt-0.5 block">
                      Max available: {availableCount}
                    </span>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-[#18211F] mb-1">Transfer Reason</label>
                    <input
                      type="text"
                      value={giveReason}
                      onChange={(e) => setGiveReason(e.target.value)}
                      className="w-full px-3.5 py-2 rounded-2xl bg-[#F7F4EC]/50 border border-[#E5E0D3] text-xs font-bold focus:border-[#063B32] focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              {/* Transfer Button & Confirmation */}
              {!giveConfirmOpen ? (
                <button
                  type="button"
                  disabled={availableCount < 1 || !selectedRecipient}
                  onClick={() => setGiveConfirmOpen(true)}
                  className="w-full py-3 rounded-2xl bg-[#063B32] hover:bg-[#063B32]/90 text-[#FFFEF9] text-xs font-bold shadow-md transition-all cursor-pointer disabled:opacity-50"
                >
                  TRANSFER {giveQuantity} PIN(S) TO DOWNLINE
                </button>
              ) : (
                <div className="p-4 rounded-3xl bg-red-50 border border-red-200 space-y-3">
                  <div className="text-xs text-red-800 font-bold">
                    ⚠️ Confirmation: You are transferring {giveQuantity} Security PIN(s) to {selectedRecipient}. This action cannot be reversed after transfer.
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={handleGiveSubmit}
                      disabled={submittingGive}
                      className="flex-1 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold cursor-pointer"
                    >
                      {submittingGive ? 'Transferring...' : 'CONFIRM & GIVE PIN'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setGiveConfirmOpen(false)}
                      className="px-4 py-2 rounded-xl bg-white border border-gray-300 text-gray-700 text-xs font-bold cursor-pointer"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: REQUEST FROM UPLINE */}
          {activeTab === 'request' && (
            <form onSubmit={handleRequestUplineSubmit} className="space-y-4">
              <div className="p-4 rounded-3xl bg-[#F7F4EC]/70 border border-[#E5E0D3] space-y-3">
                <h4 className="text-xs font-bold text-[#18211F] uppercase tracking-wider">Request PIN from Sponsor/Upline</h4>
                <p className="text-xs text-[#69736F]">
                  Send a formal PIN activation request to your sponsor. Once approved, the PIN will appear in your Security PIN Wallet.
                </p>

                <div>
                  <label className="block text-xs font-bold text-[#18211F] mb-1">Quantity</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={requestQuantity}
                    onChange={(e) => setRequestQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                    className="w-full px-3.5 py-2 rounded-2xl bg-[#FFFEF9] border border-[#E5E0D3] text-xs font-mono font-bold focus:border-[#063B32] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#18211F] mb-1">Note to Sponsor (Optional)</label>
                  <textarea
                    rows={2}
                    placeholder="e.g. Transferred ₹35,000 via GPay directly to your account"
                    value={requestNotes}
                    onChange={(e) => setRequestNotes(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-2xl bg-[#FFFEF9] border border-[#E5E0D3] text-xs focus:border-[#063B32] focus:outline-none"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={submittingRequest}
                className="w-full py-3 rounded-2xl bg-[#063B32] hover:bg-[#063B32]/90 text-[#FFFEF9] text-xs font-bold shadow-md transition-all cursor-pointer disabled:opacity-50"
              >
                {submittingRequest ? 'Sending Request...' : 'SEND REQUEST TO SPONSOR'}
              </button>
            </form>
          )}

          {/* TAB 5: INCOMING DOWNLINE REQUESTS */}
          {activeTab === 'incoming' && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-[#18211F] uppercase tracking-wider">
                Requests from Downlines ({uplineRequests.incoming.length})
              </h4>

              {uplineRequests.incoming.length > 0 ? (
                <div className="divide-y divide-[#E5E0D3]/60">
                  {uplineRequests.incoming.map((req) => (
                    <div key={req.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#FFFEF9] p-3 rounded-2xl border border-[#E5E0D3]/60">
                      <div>
                        <div className="font-bold text-xs text-[#18211F]">
                          {req.requester_user_name} ({req.requester_user_code})
                        </div>
                        <div className="text-[10px] text-[#69736F]">
                          Requested: {req.quantity} PIN(s) • {new Date(req.created_at).toLocaleString()}
                        </div>
                        {req.notes && <div className="text-xs text-[#063B32] font-mono mt-1">"{req.notes}"</div>}
                      </div>

                      <div className="flex items-center gap-2">
                        {req.status === 'PENDING' ? (
                          <>
                            <button
                              onClick={() => handleApproveRequest(req.id)}
                              disabled={loading || availableCount < req.quantity}
                              className="px-3 py-1.5 rounded-xl bg-[#063B32] text-[#FFFEF9] text-xs font-bold hover:bg-[#063B32]/90 disabled:opacity-50 cursor-pointer"
                            >
                              Approve & Give PIN
                            </button>
                            <button
                              onClick={() => handleRejectRequest(req.id)}
                              disabled={loading}
                              className="px-3 py-1.5 rounded-xl bg-red-100 text-red-800 text-xs font-bold hover:bg-red-200 cursor-pointer"
                            >
                              Reject
                            </button>
                          </>
                        ) : (
                          <span className={`px-2.5 py-1 rounded-xl text-xs font-bold ${
                            req.status === 'APPROVED' ? 'bg-[#E0F3EE] text-[#063B32]' : 'bg-red-50 text-red-700'
                          }`}>
                            {req.status}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center text-xs text-[#69736F]">No pending downline requests.</div>
              )}
            </div>
          )}

          {/* TAB 6: HISTORY & AUDIT LEDGER */}
          {activeTab === 'history' && (
            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-bold text-[#18211F] uppercase tracking-wider mb-2">Transfer Records</h4>
                {historyData.transfers.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse font-mono">
                      <thead>
                        <tr className="border-b border-[#E5E0D3] text-[#69736F] text-[10px]">
                          <th className="py-2 px-2">PIN ID</th>
                          <th className="py-2 px-2">From</th>
                          <th className="py-2 px-2">To</th>
                          <th className="py-2 px-2">Reason</th>
                          <th className="py-2 px-2">Date</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E5E0D3]/60">
                        {historyData.transfers.map((t) => (
                          <tr key={t.id} className="hover:bg-[#F7F4EC]/50">
                            <td className="py-2 px-2 font-bold text-[#063B32]">{t.pin_code}</td>
                            <td className="py-2 px-2 font-sans">{t.from_user_name}</td>
                            <td className="py-2 px-2 font-sans">{t.to_user_name}</td>
                            <td className="py-2 px-2 font-sans text-[#69736F]">{t.transfer_reason}</td>
                            <td className="py-2 px-2 text-[#69736F]">{new Date(t.transferred_at).toLocaleDateString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-xs text-[#69736F] py-2">No transfer records found.</div>
                )}
              </div>

              <div>
                <h4 className="text-xs font-bold text-[#18211F] uppercase tracking-wider mb-2">Audit Ledger</h4>
                {historyData.ledger.length > 0 ? (
                  <div className="divide-y divide-[#E5E0D3]/60 max-h-48 overflow-y-auto font-mono text-xs">
                    {historyData.ledger.map((l) => (
                      <div key={l.id} className="py-2 flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            l.action.includes('PURCHASE') || l.action.includes('ISSUED') ? 'bg-emerald-100 text-emerald-800' :
                            l.action.includes('TRANSFERRED') ? 'bg-amber-100 text-amber-800' :
                            l.action.includes('USED') ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {l.action}
                          </span>
                          <span className="text-[#18211F]">{l.notes || l.reference_id}</span>
                        </div>
                        <span className="text-[10px] text-[#69736F]">{new Date(l.timestamp).toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-[#69736F] py-2">No ledger entries.</div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

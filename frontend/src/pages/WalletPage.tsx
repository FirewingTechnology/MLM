import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { Wallet, WalletTransaction, Withdrawal } from '../types';
import { WithdrawalModal } from '../components/modals/WithdrawalModal';
import { 
  Wallet as WalletIcon, 
  TrendingUp, 
  ArrowUpRight, 
  Filter, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  ChevronLeft, 
  ChevronRight,
  ShieldCheck,
  Sparkles
} from 'lucide-react';

export const WalletPage: React.FC = () => {
  const [isWithdrawalModalOpen, setIsWithdrawalModalOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [page, setPage] = useState<number>(1);

  // Wallet overview
  const { data: walletData } = useQuery<Wallet>({
    queryKey: ['wallet'],
    queryFn: async () => {
      const res = await api.get('/wallet');
      return res.data.data;
    },
  });

  // Transactions ledger
  const { data: txnsData, isLoading: txnsLoading } = useQuery<{
    items: WalletTransaction[];
    total: number;
    pages: number;
    page: number;
  }>({
    queryKey: ['transactions', page, selectedCategory],
    queryFn: async () => {
      const url = `/wallet/transactions?page=${page}&per_page=15${selectedCategory ? `&category=${selectedCategory}` : ''}`;
      const res = await api.get(url);
      return res.data.data;
    },
  });

  // Withdrawals list
  const { data: withdrawalsData } = useQuery<{ items: Withdrawal[] }>({
    queryKey: ['withdrawals'],
    queryFn: async () => {
      const res = await api.get('/withdrawals?per_page=5');
      return res.data.data;
    },
  });

  const categories = [
    { label: 'All Transactions', value: '' },
    { label: '🟢 Direct Sponsor', value: 'DIRECT_COMMISSION' },
    { label: '🟣 Pair Bonus (₹15k)', value: 'PAIR_BONUS' },
    { label: '🟠 Matching Upline', value: 'MATCHING_COMMISSION' },
    { label: '🔵 Carry Commission', value: 'CARRY_COMMISSION' },
    { label: '💸 Withdrawals', value: 'WITHDRAWAL' },
    { label: '⚙️ Admin Adjustments', value: 'ADMIN_ADJUSTMENT' },
  ];

  return (
    <div className="space-y-5 sm:space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-[#C9A227] mb-1">
            <WalletIcon className="w-4 h-4 text-[#063B32]" />
            <span>Wealth Financial System</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-[#18211F] tracking-tight">Virtual Wallet & Ledger</h1>
          <p className="text-xs sm:text-sm text-[#69736F] font-medium">
            Real-time balance, transparent double-entry transactions, and withdrawal requests.
          </p>
        </div>

        <button
          onClick={() => setIsWithdrawalModalOpen(true)}
          className="flex items-center justify-center gap-2 px-5 py-3 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/40 font-heading font-bold text-xs shadow-wealth-card transition-all transform hover:scale-[1.02] cursor-pointer"
        >
          <ArrowUpRight className="w-4 h-4 text-[#C9A227]" />
          <span>Request Virtual Payout</span>
        </button>
      </div>

      {/* Balance Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Available Balance in Deep Emerald */}
        <div className="rounded-3xl wealth-hero p-6 relative overflow-hidden text-[#FFFEF9]">
          <div className="flex items-center justify-between text-[#F7F4EC]/75 mb-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#C9A227]">Available Balance</span>
            <div className="w-9 h-9 rounded-xl bg-[#042C26] text-[#E2C766] flex items-center justify-center border border-[#C9A227]/30">
              <WalletIcon className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl sm:text-4xl font-heading font-black text-[#E2C766] font-mono">
            ₹{walletData?.balance?.toLocaleString() || 0}
          </div>
          <div className="text-xs text-[#E0F3EE] mt-2 flex items-center gap-1 font-semibold">
            <ShieldCheck className="w-4 h-4 text-[#8DCFBF]" />
            <span>Eligible for virtual demo payout</span>
          </div>
        </div>

        <div className="rounded-3xl bg-[#FFFEF9] p-6 border border-[#E5E0D3] shadow-wealth-card relative overflow-hidden">
          <div className="flex items-center justify-between text-[#69736F] mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#18211F]">Total Earned</span>
            <div className="w-9 h-9 rounded-xl bg-[#E0F3EE] text-[#063B32] flex items-center justify-center border border-[#8DCFBF]">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl sm:text-4xl font-heading font-black text-[#063B32] font-mono">
            ₹{walletData?.total_earned?.toLocaleString() || 0}
          </div>
          <div className="text-xs text-[#69736F] mt-2">Cumulative commission earnings</div>
        </div>

        <div className="rounded-3xl bg-[#FFFEF9] p-6 border border-[#E5E0D3] shadow-wealth-card relative overflow-hidden">
          <div className="flex items-center justify-between text-[#69736F] mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#18211F]">Total Withdrawn</span>
            <div className="w-9 h-9 rounded-xl bg-[#FAF4DC] text-[#8C6C16] flex items-center justify-center border border-[#E2C766]/50">
              <ArrowUpRight className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl sm:text-4xl font-heading font-black text-[#8C6C16] font-mono">
            ₹{walletData?.total_withdrawn?.toLocaleString() || 0}
          </div>
          <div className="text-xs text-[#69736F] mt-2">Approved virtual withdrawals</div>
        </div>
      </div>

      {/* Recent Withdrawals Queue */}
      {withdrawalsData?.items && withdrawalsData.items.length > 0 && (
        <div className="rounded-3xl bg-[#FFFEF9] p-6 border border-[#E5E0D3] shadow-wealth-card">
          <div className="flex items-center justify-between mb-4">
            <div className="text-xs font-bold uppercase tracking-wider text-[#18211F] flex items-center gap-2">
              <Clock className="w-4 h-4 text-[#C9A227]" />
              <span>Withdrawal Requests</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {withdrawalsData.items.map((w) => (
              <div
                key={w.id}
                className="p-4 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-bold text-[#18211F] font-mono">{w.withdrawal_code}</div>
                  <div className="text-[#69736F] text-[10px] mt-0.5">{new Date(w.created_at).toLocaleDateString()} • {w.payout_method}</div>
                </div>
                <div className="text-right">
                  <div className="font-heading font-black text-[#18211F] font-mono">₹{w.amount.toLocaleString()}</div>
                  <span
                    className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full mt-1 border ${
                      w.status === 'APPROVED'
                        ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
                        : w.status === 'PENDING'
                        ? 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766]'
                        : 'bg-[#FDE8E8] text-[#C94B4B] border-[#F8B4B4]'
                    }`}
                  >
                    {w.status === 'APPROVED' && <CheckCircle2 className="w-3 h-3 text-[#063B32]" />}
                    {w.status === 'PENDING' && <Clock className="w-3 h-3 text-[#8C6C16]" />}
                    {w.status === 'REJECTED' && <XCircle className="w-3 h-3 text-[#C94B4B]" />}
                    <span>{w.status}</span>
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Ledger Filter Tabs & Table */}
      <div className="rounded-3xl bg-[#FFFEF9] p-6 border border-[#E5E0D3] shadow-wealth-card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E5E0D3] pb-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-[#063B32]" />
            <span className="text-sm font-heading font-extrabold text-[#18211F]">Ledger Transactions</span>
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto">
            {categories.map((cat) => (
              <button
                key={cat.value}
                onClick={() => {
                  setSelectedCategory(cat.value);
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                  selectedCategory === cat.value
                    ? 'bg-[#063B32] text-[#FFFEF9] font-bold shadow-xs'
                    : 'text-[#69736F] hover:text-[#18211F] hover:bg-[#F7F4EC]'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Ledger Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#E5E0D3] text-[#69736F] font-bold uppercase tracking-wider text-[10px] bg-[#F7F4EC]/60">
                <th className="py-3 px-4">Transaction ID</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Description</th>
                <th className="py-3 px-4 text-right">Amount</th>
                <th className="py-3 px-4 text-right">Balance After</th>
                <th className="py-3 px-4 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E0D3]/60 font-mono">
              {txnsLoading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-[#69736F]">
                    Loading ledger data...
                  </td>
                </tr>
              ) : txnsData?.items && txnsData.items.length > 0 ? (
                txnsData.items.map((txn) => (
                  <tr key={txn.id} className="hover:bg-[#F7F4EC]/40 transition-colors">
                    <td className="py-3 px-4 text-[#18211F] font-bold">
                      {txn.transaction_code}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`text-[10px] px-2.5 py-0.5 rounded-md font-sans font-bold border ${
                        txn.category === 'PAIR_BONUS'
                          ? 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766]'
                          : txn.category === 'DIRECT_COMMISSION' || txn.category === 'DIRECT_REFERRAL'
                          ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
                          : txn.category === 'MATCHING_COMMISSION' || txn.category === 'BINARY_MATCHING'
                          ? 'bg-[#FFEDD5] text-[#C2410C] border-[#FDBA74]'
                          : txn.category === 'CARRY_COMMISSION'
                          ? 'bg-[#DBEAFE] text-[#1D4ED8] border-[#93C5FD]'
                          : txn.category === 'WITHDRAWAL'
                          ? 'bg-[#FDE8E8] text-[#C94B4B] border-[#F8B4B4]'
                          : 'bg-[#F7F4EC] text-[#69736F] border-[#E5E0D3]'
                      }`}>
                        {txn.category === 'PAIR_BONUS'
                          ? '🟣 Pair Bonus (₹15k)'
                          : txn.category === 'DIRECT_COMMISSION' || txn.category === 'DIRECT_REFERRAL'
                          ? '🟢 Direct Sponsor'
                          : txn.category === 'MATCHING_COMMISSION' || txn.category === 'BINARY_MATCHING'
                          ? '🟠 Matching Upline'
                          : txn.category === 'CARRY_COMMISSION'
                          ? '🔵 Carry Commission'
                          : txn.category}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-sans text-[#18211F] font-medium">
                      {txn.description}
                    </td>
                    <td className="py-3 px-4 text-right font-bold">
                      <span className={txn.type === 'CREDIT' ? 'text-[#0E9F6E]' : 'text-[#C94B4B]'}>
                        {txn.type === 'CREDIT' ? '+' : '-'}₹{txn.amount.toLocaleString()}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right text-[#18211F] font-bold">
                      ₹{txn.balance_after.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right text-[#69736F] text-[11px]">
                      {new Date(txn.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-[#69736F] font-sans">
                    No transactions found in this category.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {txnsData && txnsData.pages > 1 && (
          <div className="flex items-center justify-between pt-4 border-t border-[#E5E0D3] text-xs">
            <span className="text-[#69736F]">
              Page {txnsData.page} of {txnsData.pages} ({txnsData.total} records)
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                className="p-2 rounded-xl bg-[#F7F4EC] hover:bg-[#EFECE2] disabled:opacity-40 text-[#18211F] cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                disabled={page >= txnsData.pages}
                onClick={() => setPage((p) => p + 1)}
                className="p-2 rounded-xl bg-[#F7F4EC] hover:bg-[#EFECE2] disabled:opacity-40 text-[#18211F] cursor-pointer"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      <WithdrawalModal
        isOpen={isWithdrawalModalOpen}
        onClose={() => setIsWithdrawalModalOpen(false)}
        availableBalance={walletData?.balance || 0}
      />
    </div>
  );
};


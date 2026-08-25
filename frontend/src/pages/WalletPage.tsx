import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { Wallet, WalletTransaction, Withdrawal } from '../types';
import { WithdrawalModal } from '../components/modals/WithdrawalModal';
import { 
  Wallet as WalletIcon, 
  TrendingUp, 
  ArrowUpRight, 
  ArrowDownLeft, 
  Coins, 
  Filter, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  ChevronLeft, 
  ChevronRight,
  ShieldCheck 
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
    { label: 'Direct Referral Bonus', value: 'DIRECT_REFERRAL' },
    { label: 'Binary Matching Bonus', value: 'BINARY_MATCHING' },
    { label: 'Withdrawals', value: 'WITHDRAWAL' },
    { label: 'Admin Adjustments', value: 'ADMIN_ADJUSTMENT' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-brand-400 mb-1">
            <WalletIcon className="w-4 h-4" />
            <span>Financial System</span>
          </div>
          <h1 className="text-2xl font-black text-white">Virtual Wallet & Ledger</h1>
          <p className="text-xs text-slate-400">
            Real-time balance, transparent double-entry transactions, and withdrawal requests.
          </p>
        </div>

        <button
          onClick={() => setIsWithdrawalModalOpen(true)}
          className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-400 hover:to-emerald-500 text-navy-950 font-bold text-xs shadow-glow-emerald transition-all transform hover:scale-[1.02]"
        >
          <ArrowUpRight className="w-4 h-4" />
          <span>Request Virtual Withdrawal</span>
        </button>
      </div>

      {/* Balance Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-3xl glass-panel p-6 border border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Available Balance</span>
            <div className="w-9 h-9 rounded-xl bg-brand-500/10 text-brand-400 flex items-center justify-center">
              <WalletIcon className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-black text-white font-mono">
            ₹{walletData?.balance?.toLocaleString() || 0}
          </div>
          <div className="text-xs text-emerald-400 mt-2 flex items-center gap-1 font-medium">
            <ShieldCheck className="w-4 h-4" />
            <span>Eligible for virtual demo payout</span>
          </div>
        </div>

        <div className="rounded-3xl glass-panel p-6 border border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Earned</span>
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-black text-emerald-400 font-mono">
            ₹{walletData?.total_earned?.toLocaleString() || 0}
          </div>
          <div className="text-xs text-slate-400 mt-2">Cumulative commission earnings</div>
        </div>

        <div className="rounded-3xl glass-panel p-6 border border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Withdrawn</span>
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <ArrowUpRight className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-black text-amber-400 font-mono">
            ₹{walletData?.total_withdrawn?.toLocaleString() || 0}
          </div>
          <div className="text-xs text-slate-400 mt-2">Approved virtual withdrawals</div>
        </div>
      </div>

      {/* Recent Withdrawals Queue */}
      {withdrawalsData?.items && withdrawalsData.items.length > 0 && (
        <div className="rounded-3xl glass-panel p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <Clock className="w-4 h-4 text-amber-400" />
              <span>Withdrawal Requests</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {withdrawalsData.items.map((w) => (
              <div
                key={w.id}
                className="p-3.5 rounded-2xl bg-navy-900/80 border border-slate-800 flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-bold text-white font-mono">{w.withdrawal_code}</div>
                  <div className="text-slate-400 text-[10px] mt-0.5">{new Date(w.created_at).toLocaleDateString()} • {w.payout_method}</div>
                </div>
                <div className="text-right">
                  <div className="font-black text-white font-mono">₹{w.amount.toLocaleString()}</div>
                  <span
                    className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full mt-1 border ${
                      w.status === 'APPROVED'
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : w.status === 'PENDING'
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                    }`}
                  >
                    {w.status === 'APPROVED' && <CheckCircle2 className="w-3 h-3" />}
                    {w.status === 'PENDING' && <Clock className="w-3 h-3" />}
                    {w.status === 'REJECTED' && <XCircle className="w-3 h-3" />}
                    <span>{w.status}</span>
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Ledger Filter Tabs & Table */}
      <div className="rounded-3xl glass-panel p-6 border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-brand-400" />
            <span className="text-sm font-bold text-white">Ledger Transactions</span>
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto">
            {categories.map((cat) => (
              <button
                key={cat.value}
                onClick={() => {
                  setSelectedCategory(cat.value);
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                  selectedCategory === cat.value
                    ? 'bg-brand-500 text-navy-950 font-bold shadow-glow-emerald'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
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
              <tr className="border-b border-slate-800/80 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Transaction ID</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Description</th>
                <th className="py-3 px-4 text-right">Amount</th>
                <th className="py-3 px-4 text-right">Balance After</th>
                <th className="py-3 px-4 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {txnsLoading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    Loading ledger data...
                  </td>
                </tr>
              ) : txnsData?.items && txnsData.items.length > 0 ? (
                txnsData.items.map((txn) => (
                  <tr key={txn.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 text-slate-300 font-bold">
                      {txn.transaction_code}
                    </td>
                    <td className="py-3 px-4">
                      <span className="bg-slate-800 text-slate-300 text-[10px] px-2 py-0.5 rounded font-sans font-semibold">
                        {txn.category}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-sans text-slate-200">
                      {txn.description}
                    </td>
                    <td className="py-3 px-4 text-right font-bold">
                      <span className={txn.type === 'CREDIT' ? 'text-emerald-400' : 'text-rose-400'}>
                        {txn.type === 'CREDIT' ? '+' : '-'}₹{txn.amount.toLocaleString()}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right text-slate-300">
                      ₹{txn.balance_after.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-400 text-[11px]">
                      {new Date(txn.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500 font-sans">
                    No transactions found in this category.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {txnsData && txnsData.pages > 1 && (
          <div className="flex items-center justify-between pt-4 border-t border-slate-800 text-xs">
            <span className="text-slate-400">
              Page {txnsData.page} of {txnsData.pages} ({txnsData.total} records)
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                disabled={page >= txnsData.pages}
                onClick={() => setPage((p) => p + 1)}
                className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300"
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

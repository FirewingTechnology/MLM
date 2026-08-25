import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { useToast } from '../context/ToastContext';
import { useAuth } from '../context/AuthContext';
import { 
  Users, 
  Copy, 
  Check, 
  GitFork, 
  ChevronLeft, 
  ChevronRight, 
  CheckCircle2, 
  Clock 
} from 'lucide-react';

export const ReferralsPage: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [page, setPage] = useState<number>(1);
  const [copied, setCopied] = useState(false);

  const referralLink = user?.referral_code
    ? `${window.location.origin}/register?ref=${user.referral_code}`
    : '';

  const handleCopy = () => {
    navigator.clipboard.writeText(referralLink);
    setCopied(true);
    showToast('Referral link copied!', 'success');
    setTimeout(() => setCopied(false), 2500);
  };

  const { data, isLoading } = useQuery({
    queryKey: ['myReferrals', page],
    queryFn: async () => {
      const res = await api.get(`/referral/my-referrals?page=${page}&per_page=15`);
      return res.data.data;
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-brand-400 mb-1">
            <Users className="w-4 h-4" />
            <span>Direct Team</span>
          </div>
          <h1 className="text-2xl font-black text-white">Direct Sponsored Members</h1>
          <p className="text-xs text-slate-400">
            View all members registered directly via your referral link ({user?.referral_code}).
          </p>
        </div>

        <button
          onClick={handleCopy}
          className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-400 text-navy-950 font-bold text-xs shadow-glow-emerald transition-all"
        >
          {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
          <span>{copied ? 'Copied Link!' : 'Copy My Referral Link'}</span>
        </button>
      </div>

      {/* Referrals Table Card */}
      <div className="rounded-3xl glass-panel p-6 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="text-sm font-bold text-white flex items-center gap-2">
            <span>Direct Team Members</span>
            <span className="bg-brand-500/20 text-brand-300 text-xs px-2.5 py-0.5 rounded-full font-mono font-bold">
              {data?.total_direct || 0} Total
            </span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800/80 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Member</th>
                <th className="py-3 px-4">User Code</th>
                <th className="py-3 px-4">Placement Parent</th>
                <th className="py-3 px-4">Position</th>
                <th className="py-3 px-4 text-right">Personal BV</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-right">Joined Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400 font-sans">
                    Loading direct team members...
                  </td>
                </tr>
              ) : data?.items && data.items.length > 0 ? (
                data.items.map((m: any) => (
                  <tr key={m.id} className="hover:bg-slate-800/30 transition-colors font-sans">
                    <td className="py-3 px-4">
                      <div className="font-bold text-white">{m.full_name}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{m.email}</div>
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-slate-300">
                      {m.user_code}
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-medium">
                      {m.binary_parent_name || 'Root'}
                    </td>
                    <td className="py-3 px-4">
                      <span className="bg-slate-800 text-slate-300 font-mono text-[10px] px-2 py-0.5 rounded font-bold">
                        {m.binary_position || 'ROOT'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-emerald-400 font-bold">
                      {m.personal_bv ? `${m.personal_bv.toLocaleString()} BV` : '0 BV'}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                          m.is_active
                            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                            : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        }`}
                      >
                        {m.is_active ? <CheckCircle2 className="w-3 h-3" /> : <Clock className="w-3 h-3" />}
                        <span>{m.is_active ? 'Active' : 'Inactive'}</span>
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right text-slate-400 text-[11px]">
                      {new Date(m.joined_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500 font-sans">
                    You have not sponsored any members yet. Share your referral link to build your direct team.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-between pt-4 border-t border-slate-800 text-xs">
            <span className="text-slate-400">
              Page {data.page} of {data.pages} ({data.total} records)
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
                disabled={page >= data.pages}
                onClick={() => setPage((p) => p + 1)}
                className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

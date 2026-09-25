import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { useToast } from '../context/ToastContext';
import { useAuth } from '../context/AuthContext';
import {
  Users,
  Copy,
  Check,
  ExternalLink,
  Lock,
  Share2,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  Clock,
  Sparkles
} from 'lucide-react';
import { ReferralLinksData } from '../types';

export const ReferralsPage: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [page, setPage] = useState<number>(1);
  const [copiedLeft, setCopiedLeft] = useState(false);
  const [copiedRight, setCopiedRight] = useState(false);

  // Fetch permanent locked referral links
  const { data: linksData } = useQuery<ReferralLinksData>({
    queryKey: ['referralLinks'],
    queryFn: async () => {
      const res = await api.get('/referral/links');
      return res.data.data;
    },
  });

  const leftUrl = linksData?.left?.token
    ? `${window.location.origin}/register?ref=${linksData.left.token}`
    : user?.referral_code
      ? `${window.location.origin}/register?ref=${user.referral_code}&leg=left`
      : '';

  const rightUrl = linksData?.right?.token
    ? `${window.location.origin}/register?ref=${linksData.right.token}`
    : user?.referral_code
      ? `${window.location.origin}/register?ref=${user.referral_code}&leg=right`
      : '';

  const handleCopyLeft = () => {
    if (!leftUrl) return;
    navigator.clipboard.writeText(leftUrl);
    setCopiedLeft(true);
    showToast('LEFT Referral Link copied!', 'success');
    setTimeout(() => setCopiedLeft(false), 2500);
  };

  const handleCopyRight = () => {
    if (!rightUrl) return;
    navigator.clipboard.writeText(rightUrl);
    setCopiedRight(true);
    showToast('RIGHT Referral Link copied!', 'success');
    setTimeout(() => setCopiedRight(false), 2500);
  };

  const handleShare = async (title: string, url: string) => {
    if (navigator.share) {
      try {
        await navigator.share({
          title,
          text: `Join my partner network via this invitation link:`,
          url,
        });
      } catch {
        // User cancelled or unsupported
      }
    } else {
      navigator.clipboard.writeText(url);
      showToast('Referral link copied to clipboard!', 'success');
    }
  };

  const { data, isLoading } = useQuery({
    queryKey: ['myReferrals', page],
    queryFn: async () => {
      const res = await api.get(`/referral/my-referrals?page=${page}&per_page=15`);
      return res.data.data;
    },
  });

  return (
    <div className="space-y-5 sm:space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-[#C9A227] mb-1">
            <Users className="w-4 h-4 text-[#063B32]" />
            <span>Direct Team Portfolio</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-[#18211F] tracking-tight">Direct Sponsored Members</h1>
          <p className="text-xs sm:text-sm text-[#69736F] font-medium">
            Generate locked LEFT & RIGHT placement links to recruit new direct distributors.
          </p>
        </div>
      </div>

      {/* MY REFERRAL LINKS SECTION */}
      <div className="rounded-3xl bg-[#FFFEF9] p-6 border border-[#E5E0D3] shadow-wealth-card space-y-4">
        <div className="flex items-center justify-between border-b border-[#E5E0D3] pb-3">
          <div className="flex items-center gap-2 text-sm font-heading font-extrabold text-[#18211F]">
            <Lock className="w-4 h-4 text-[#063B32]" />
            <span>MY REFERRAL LINKS (LOCKED Matching PLACEMENT)</span>
          </div>
          <span className="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-[#FAF4DC] text-[#8C6C16] border border-[#E2C766]/60">
            Sponsor: {user?.referral_code}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
          {/* LEFT LEG CARD */}
          <div className="p-5 rounded-2xl bg-[#F7F4EC] border border-[#8DCFBF] flex flex-col justify-between space-y-3">
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[#063B32]">
                  <span className="w-2 h-2 rounded-full bg-[#063B32]" />
                  <span>LEFT LEG REFERRAL</span>
                </div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-[#E0F3EE] text-[#063B32] border border-[#8DCFBF]">
                  LEFT LOCKED
                </span>
              </div>
              <p className="text-xs text-[#69736F] mb-3">
                Places new members on your extreme-left leg automatically.
              </p>
              <div className="p-2.5 rounded-xl bg-[#FFFEF9] border border-[#E5E0D3] font-mono text-[11px] text-[#18211F] truncate select-all">
                {leftUrl}
              </div>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <button
                onClick={handleCopyLeft}
                className="flex-1 flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] text-xs font-bold transition-all shadow-xs cursor-pointer"
              >
                {copiedLeft ? <Check className="w-3.5 h-3.5 text-[#C9A227]" /> : <Copy className="w-3.5 h-3.5 text-[#C9A227]" />}
                <span>{copiedLeft ? 'Copied LEFT Link!' : 'Copy LEFT Link'}</span>
              </button>
              <button
                onClick={() => handleShare('Left Leg Referral', leftUrl)}
                className="p-2.5 rounded-xl border border-[#E5E0D3] bg-[#FFFEF9] hover:bg-[#EFECE2] text-[#18211F] transition-colors cursor-pointer"
                title="Share Link"
              >
                <Share2 className="w-3.5 h-3.5" />
              </button>
              <a
                href={leftUrl}
                target="_blank"
                rel="noreferrer"
                className="p-2.5 rounded-xl border border-[#E5E0D3] bg-[#FFFEF9] hover:bg-[#EFECE2] text-[#18211F] transition-colors cursor-pointer"
                title="Open Preview"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>

          {/* RIGHT LEG CARD */}
          <div className="p-5 rounded-2xl bg-[#F7F4EC] border border-[#E2C766] flex flex-col justify-between space-y-3">
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[#8C6C16]">
                  <span className="w-2 h-2 rounded-full bg-[#C9A227]" />
                  <span>RIGHT LEG REFERRAL</span>
                </div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-[#FAF4DC] text-[#8C6C16] border border-[#E2C766]">
                  RIGHT LOCKED
                </span>
              </div>
              <p className="text-xs text-[#69736F] mb-3">
                Places new members on your extreme-right leg automatically.
              </p>
              <div className="p-2.5 rounded-xl bg-[#FFFEF9] border border-[#E5E0D3] font-mono text-[11px] text-[#18211F] truncate select-all">
                {rightUrl}
              </div>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <button
                onClick={handleCopyRight}
                className="flex-1 flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] text-xs font-bold transition-all shadow-xs cursor-pointer"
              >
                {copiedRight ? <Check className="w-3.5 h-3.5 text-[#C9A227]" /> : <Copy className="w-3.5 h-3.5 text-[#C9A227]" />}
                <span>{copiedRight ? 'Copied RIGHT Link!' : 'Copy RIGHT Link'}</span>
              </button>
              <button
                onClick={() => handleShare('Right Leg Referral', rightUrl)}
                className="p-2.5 rounded-xl border border-[#E5E0D3] bg-[#FFFEF9] hover:bg-[#EFECE2] text-[#18211F] transition-colors cursor-pointer"
                title="Share Link"
              >
                <Share2 className="w-3.5 h-3.5" />
              </button>
              <a
                href={rightUrl}
                target="_blank"
                rel="noreferrer"
                className="p-2.5 rounded-xl border border-[#E5E0D3] bg-[#FFFEF9] hover:bg-[#EFECE2] text-[#18211F] transition-colors cursor-pointer"
                title="Open Preview"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Referrals Table Card */}
      <div className="rounded-3xl bg-[#FFFEF9] p-6 border border-[#E5E0D3] shadow-wealth-card space-y-4">
        <div className="flex items-center justify-between border-b border-[#E5E0D3] pb-4">
          <div className="text-sm font-heading font-extrabold text-[#18211F] flex items-center gap-2">
            <span>Direct Team Members</span>
            <span className="bg-[#FAF4DC] text-[#8C6C16] border border-[#E2C766]/60 text-xs px-2.5 py-0.5 rounded-full font-mono font-bold">
              {data?.total_direct || 0} Total
            </span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#E5E0D3] text-[#69736F] font-bold uppercase tracking-wider text-[10px] bg-[#F7F4EC]/60">
                <th className="py-3 px-4">Member</th>
                <th className="py-3 px-4">User Code</th>
                <th className="py-3 px-4">Placement Parent</th>
                <th className="py-3 px-4">Position</th>
                <th className="py-3 px-4 text-right">Personal BV</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-right">Joined Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E0D3]/60 font-mono">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-[#69736F] font-sans">
                    Loading direct team members...
                  </td>
                </tr>
              ) : data?.items && data.items.length > 0 ? (
                data.items.map((m: any) => (
                  <tr key={m.id} className="hover:bg-[#F7F4EC]/40 transition-colors font-sans">
                    <td className="py-3 px-4">
                      <div className="font-bold text-[#18211F]">{m.full_name}</div>
                      <div className="text-[11px] text-[#69736F] font-mono">{m.email}</div>
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-[#063B32]">
                      {m.user_code}
                    </td>
                    <td className="py-3 px-4 text-[#18211F] font-medium">
                      {m.binary_parent_name || 'Root'}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`font-mono text-[10px] px-2 py-0.5 rounded-md font-bold border ${m.binary_position === 'LEFT'
                          ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
                          : m.binary_position === 'RIGHT'
                            ? 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766]/60'
                            : 'bg-[#F7F4EC] text-[#69736F] border-[#E5E0D3]'
                        }`}>
                        {m.binary_position || 'ROOT'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-[#063B32] font-bold">
                      {m.personal_bv ? `${m.personal_bv.toLocaleString()} BV` : '0 BV'}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${m.is_active
                            ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
                            : 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766]'
                          }`}
                      >
                        {m.is_active ? <CheckCircle2 className="w-3 h-3 text-[#063B32]" /> : <Clock className="w-3 h-3 text-[#8C6C16]" />}
                        <span>{m.is_active ? 'Active' : 'Inactive'}</span>
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right text-[#69736F] text-[11px] font-mono">
                      <div className="font-bold text-[#18211F]">
                        {new Date(m.joined_at).toLocaleDateString()}
                      </div>
                      <div className="text-[10px] text-[#69736F]">
                        {new Date(m.joined_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-[#69736F] font-sans">
                    You have not sponsored any members yet. Share your referral link to build your direct team.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-between pt-4 border-t border-[#E5E0D3] text-xs">
            <span className="text-[#69736F]">
              Page {data.page} of {data.pages} ({data.total} records)
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
                disabled={page >= data.pages}
                onClick={() => setPage((p) => p + 1)}
                className="p-2 rounded-xl bg-[#F7F4EC] hover:bg-[#EFECE2] disabled:opacity-40 text-[#18211F] cursor-pointer"
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


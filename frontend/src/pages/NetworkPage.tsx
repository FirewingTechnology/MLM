import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { MatchingTreeCanvas } from '../components/tree/BinaryTreeCanvas';
import { MatchingTreeNode, SlotSettlement, NetworkViewMode } from '../types';
import {
  GitFork,
  Search,
  Users,
  Coins,
  HelpCircle,
  Sparkles,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Home,
  UserCheck,
  Zap,
  History,
  RotateCcw,
  CheckCircle2,
  Clock,
  Layers,
  ArrowUpRight
} from 'lucide-react';

export const NetworkPage: React.FC = () => {
  const [rootId, setRootId] = useState<number | null>(null);
  const [depth, setDepth] = useState<number>(3);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<NetworkViewMode>('network');

  const { data: treeData, isLoading } = useQuery<MatchingTreeNode>({
    queryKey: ['network', rootId, depth, viewMode],
    queryFn: async () => {
      const url = rootId
        ? `/network/${rootId}?depth=${depth}&view=${viewMode}`
        : `/network?depth=${depth}&view=${viewMode}`;
      const res = await api.get(url);
      return res.data.data;
    },
  });

  const { data: members = [] } = useQuery<any[]>({
    queryKey: ['networkMembers'],
    queryFn: async () => {
      const res = await api.get('/network/members');
      return res.data.data || [];
    },
  });

  const { data: settlementsData, isLoading: isLoadingSettlements } = useQuery<{ items: SlotSettlement[]; total: number }>({
    queryKey: ['mySettlements'],
    queryFn: async () => {
      const res = await api.get('/network/settlements?per_page=50');
      return res.data.data || { items: [], total: 0 };
    },
    enabled: viewMode === 'history',
  });

  const { data: searchResults } = useQuery({
    queryKey: ['networkSearch', searchQuery],
    queryFn: async () => {
      if (!searchQuery || searchQuery.length < 2) return [];
      const res = await api.get(`/network/search?q=${searchQuery}`);
      return res.data.data;
    },
    enabled: searchQuery.length >= 2,
  });

  // Calculate current active user index in members list
  const currentActiveId = rootId ?? (treeData?.id || (members[0]?.id));
  const currentIndex = members.findIndex((m: any) => m.id === currentActiveId);
  const prevUser = currentIndex > 0 ? members[currentIndex - 1] : null;
  const nextUser = currentIndex >= 0 && currentIndex < members.length - 1 ? members[currentIndex + 1] : null;

  const handlePrevUser = () => {
    if (prevUser) {
      setRootId(prevUser.id);
    }
  };

  const handleNextUser = () => {
    if (nextUser) {
      setRootId(nextUser.id);
    }
  };

  return (
    <div className="space-y-5 sm:space-y-6">
      {/* Page Header with Mode Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
        <div>
          <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-[#C9A227] mb-1">
            <GitFork className="w-3.5 h-3.5" />
            <span>Matching Network Engine</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-[#18211F] tracking-tight">Franchise Partner</h1>
          <p className="text-xs sm:text-sm text-[#69736F] font-medium">
            Matching Network Structure • Active 12-Hour Slot Matching • Carry Forward Volume
          </p>
        </div>

        {/* View Mode Toggle Buttons */}
        <div className="flex items-center gap-1.5 p-1.5 bg-[#F7F4EC] rounded-2xl border border-[#E5E0D3] self-start md:self-auto shadow-2xs">
          <button
            onClick={() => setViewMode('network')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${viewMode === 'network'
                ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs'
                : 'text-[#69736F] hover:text-[#18211F] hover:bg-[#EFECE2]'
              }`}
          >
            <GitFork className="w-3.5 h-3.5" />
            <span>Franchise Tree</span>
          </button>

          <button
            onClick={() => setViewMode('active_slot')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${viewMode === 'active_slot'
                ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs'
                : 'text-[#69736F] hover:text-[#18211F] hover:bg-[#EFECE2]'
              }`}
          >
            <Zap className="w-3.5 h-3.5 text-[#C9A227]" />
            <span>Active Slot View</span>
          </button>

          <button
            onClick={() => setViewMode('history')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${viewMode === 'history'
                ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs'
                : 'text-[#69736F] hover:text-[#18211F] hover:bg-[#EFECE2]'
              }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Slot History</span>
          </button>
        </div>
      </div>

      {/* Member Search Bar (Visible in tree modes) */}
      {viewMode !== 'history' && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3.5 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
          {/* Search member bar */}
          <div className="relative w-full sm:w-80">
            <div className="relative">
              <Search className="w-4 h-4 text-[#69736F] absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search member name or code..."
                className="w-full pl-9 pr-4 py-2 rounded-xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] text-xs focus:outline-none focus:border-[#C9A227] font-mono shadow-2xs"
              />
            </div>

            {/* Autocomplete dropdown */}
            {searchResults && searchResults.length > 0 && (
              <div className="absolute left-0 right-0 mt-2 rounded-2xl bg-[#FFFEF9] p-2 shadow-wealth-elevated z-40 border border-[#E5E0D3]">
                <div className="text-[10px] uppercase font-bold text-[#69736F] px-2 py-1 mb-1">
                  Network Search Results
                </div>
                {searchResults.map((member: any) => (
                  <button
                    key={member.id}
                    onClick={() => {
                      setRootId(member.id);
                      setSearchQuery('');
                    }}
                    className="w-full p-2.5 rounded-xl hover:bg-[#F7F4EC] text-left flex items-center justify-between transition-colors text-xs cursor-pointer"
                  >
                    <div>
                      <div className="font-bold text-[#18211F]">{member.full_name}</div>
                      <div className="text-[10px] text-[#69736F] font-mono">{member.user_code}</div>
                    </div>
                    <span className="text-[10px] bg-[#FAF4DC] text-[#8C6C16] px-2.5 py-1 rounded-lg font-mono font-bold border border-[#E2C766]/50">
                      View Subtree →
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Quick View Mode Hint */}
          <div className="text-xs font-mono text-[#69736F] flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#063B32] animate-pulse" />
            <span className="font-sans font-medium">
              Mode: <strong className="text-[#18211F]">{viewMode === 'active_slot' ? 'Active 12h Slot Volume' : 'Permanent Matching Network'}</strong>
            </span>
          </div>
        </div>
      )}

      {/* Statistics Strip for Tree Views */}
      {viewMode !== 'history' && treeData && (
        <div className="p-4 sm:p-5 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 divide-y lg:divide-y-0 lg:divide-x divide-[#EFECE2]">
            {/* Network Volume Header */}
            <div className="pr-4 shrink-0">
              <span className="text-[10px] font-bold uppercase tracking-widest text-[#C9A227] block">
                {viewMode === 'active_slot' ? 'Active Slot Member' : 'Permanent Network'}
              </span>
              <div className="text-base font-heading font-extrabold text-[#18211F] mt-0.5">{treeData.full_name}</div>
              <div className="text-[11px] text-[#063B32] font-mono font-bold">{treeData.user_code}</div>
            </div>

            {/* Left Volume */}
            <div className="pt-3 lg:pt-0 lg:px-6 flex-1">
              <div className="text-[10px] font-bold uppercase tracking-wider text-[#69736F]">
                {viewMode === 'active_slot' ? 'Left Effective BV' : 'Left Lifetime BV'}
              </div>
              <div className="text-base sm:text-lg font-mono font-black text-[#063B32] mt-0.5">
                ₹{(viewMode === 'active_slot' ? (treeData.effective_left_bv ?? treeData.left_bv ?? 0) : (treeData.accumulated_left_bv ?? treeData.left_bv ?? 0)).toLocaleString()}{' '}
                <span className="text-xs font-medium text-[#69736F]">BV</span>
              </div>
              <div className="text-[11px] text-[#69736F] font-mono flex items-center gap-1">
                <RotateCcw className="w-3 h-3 text-[#8C6C16]" />
                <span>Carry: ₹{(treeData.ending_carry_left ?? treeData.carry_left_bv ?? 0).toLocaleString()}</span>
              </div>
            </div>

            {/* Right Volume */}
            <div className="pt-3 lg:pt-0 lg:px-6 flex-1">
              <div className="text-[10px] font-bold uppercase tracking-wider text-[#69736F]">
                {viewMode === 'active_slot' ? 'Right Effective BV' : 'Right Lifetime BV'}
              </div>
              <div className="text-base sm:text-lg font-mono font-black text-[#063B32] mt-0.5">
                ₹{(viewMode === 'active_slot' ? (treeData.effective_right_bv ?? treeData.right_bv ?? 0) : (treeData.accumulated_right_bv ?? treeData.right_bv ?? 0)).toLocaleString()}{' '}
                <span className="text-xs font-medium text-[#69736F]">BV</span>
              </div>
              <div className="text-[11px] text-[#69736F] font-mono flex items-center gap-1">
                <RotateCcw className="w-3 h-3 text-[#8C6C16]" />
                <span>Carry: ₹{(treeData.ending_carry_right ?? treeData.carry_right_bv ?? 0).toLocaleString()}</span>
              </div>
            </div>

            {/* Matched Volume / Pair Status */}
            <div className="pt-3 lg:pt-0 lg:pl-6 shrink-0 bg-[#FAF4DC]/40 -m-4 p-4 lg:m-0 lg:p-0 lg:bg-transparent rounded-2xl">
              <div className="text-[10px] font-bold uppercase tracking-wider text-[#8C6C16]">
                {viewMode === 'active_slot' ? 'Current Slot Status' : 'Matched Volume'}
              </div>
              <div className="text-base sm:text-lg font-mono font-black text-[#C9A227] mt-0.5 flex items-center gap-1.5">
                {viewMode === 'active_slot' ? (
                  treeData.pair_completed ? (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[#E0F3EE] text-[#063B32] text-[10px] font-bold border border-[#8DCFBF]">
                      <CheckCircle2 className="w-3 h-3 text-[#063B32]" />
                      Paid ₹15,000 Pair
                    </span>
                  ) : (
                    <span className="text-xs bg-[#FAF4DC] text-[#8C6C16] px-2 py-1 rounded-lg border border-[#E2C766] font-sans font-bold">
                      In Progress (Max 1/slot)
                    </span>
                  )
                ) : (
                  <>
                    <span>₹{treeData.matched_bv?.toLocaleString() || 0}</span>
                    {treeData.matched_bv >= 30000 && (
                      <span className="text-[10px] bg-[#C9A227] text-white px-1.5 py-0.5 rounded font-sans font-bold">
                        Pair ✓
                      </span>
                    )}
                  </>
                )}
              </div>
              <div className="text-[11px] text-[#8C6C16] font-medium">
                {viewMode === 'active_slot' ? '1 Pair Max per 12-Hour Slot' : '10% Pair Bonus Basis'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main View: Tree Canvas or Settlement History */}
      {viewMode === 'history' ? (
        /* Slot Settlement History Table */
        <div className="p-5 sm:p-6 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-heading font-extrabold text-[#18211F]">Slot Settlement Audit Trail</h2>
              <p className="text-xs text-[#69736F]">
                Immutable records of volume matching, pair bonus payouts, and leg-specific carry forwards across all 12-hour slots.
              </p>
            </div>
            <span className="text-xs font-mono bg-[#F7F4EC] px-3 py-1.5 rounded-xl border border-[#E5E0D3] font-bold text-[#063B32]">
              {settlementsData?.total || 0} Settlements
            </span>
          </div>

          {isLoadingSettlements ? (
            <div className="py-12 flex flex-col items-center justify-center gap-3">
              <div className="w-8 h-8 rounded-full border-2 border-[#063B32] border-t-[#C9A227] animate-spin" />
              <div className="text-xs text-[#69736F]">Loading settlement records...</div>
            </div>
          ) : settlementsData?.items && settlementsData.items.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#E5E0D3] bg-[#F7F4EC]/60 text-[#69736F] font-mono text-[10px] uppercase">
                    <th className="py-3 px-4 rounded-l-xl">Slot ID</th>
                    <th className="py-3 px-3">Opening Left</th>
                    <th className="py-3 px-3">Opening Right</th>
                    <th className="py-3 px-3">Matched Left</th>
                    <th className="py-3 px-3">Matched Right</th>
                    <th className="py-3 px-3 text-[#C9A227]">Pair Bonus</th>
                    <th className="py-3 px-3 text-[#063B32]">Left Carry</th>
                    <th className="py-3 px-3 text-[#063B32]">Right Carry</th>
                    <th className="py-3 px-3">Carry Comm.</th>
                    <th className="py-3 px-4 rounded-r-xl">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#EFECE2] font-mono">
                  {settlementsData.items.map((s) => (
                    <tr key={s.id} className="hover:bg-[#F7F4EC]/50 transition-colors">
                      <td className="py-3.5 px-4 font-bold text-[#18211F]">{s.slot_id}</td>
                      <td className="py-3.5 px-3">₹{s.left_before?.toLocaleString()}</td>
                      <td className="py-3.5 px-3">₹{s.right_before?.toLocaleString()}</td>
                      <td className="py-3.5 px-3 text-[#8C6C16] font-bold">₹{s.left_matched?.toLocaleString()}</td>
                      <td className="py-3.5 px-3 text-[#8C6C16] font-bold">₹{s.right_matched?.toLocaleString()}</td>
                      <td className="py-3.5 px-3 font-bold text-[#C9A227]">
                        {s.pair_bonus > 0 ? `₹${s.pair_bonus?.toLocaleString()}` : '—'}
                      </td>
                      <td className="py-3.5 px-3 font-bold text-[#063B32]">₹{s.left_carry?.toLocaleString()}</td>
                      <td className="py-3.5 px-3 font-bold text-[#063B32]">₹{s.right_carry?.toLocaleString()}</td>
                      <td className="py-3.5 px-3">
                        {s.carry_commission > 0 ? (
                          <span className="text-[#063B32] font-bold">₹{s.carry_commission?.toLocaleString()}</span>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="py-3.5 px-4 font-sans">
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#E0F3EE] text-[#063B32] border border-[#8DCFBF]">
                          {s.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-12 text-center rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3]">
              <History className="w-8 h-8 text-[#C9A227] mx-auto mb-2 opacity-80" />
              <div className="text-sm font-bold text-[#18211F]">No Slot Settlements Yet</div>
              <p className="text-xs text-[#69736F] mt-1 max-w-sm mx-auto">
                Settlement records are automatically finalized as 12-hour slots roll over.
              </p>
            </div>
          )}
        </div>
      ) : (
        /* Permanent Network & Active Slot Tree Canvas */
        <>
          {/* Member Navigation Bar (Left & Right Arrows) */}
          {members.length > 0 && (
            <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-card">
              <div className="flex items-center gap-2">
                <button
                  onClick={handlePrevUser}
                  disabled={!prevUser}
                  title={prevUser ? `Previous: ${prevUser.full_name} (${prevUser.user_code})` : 'No previous member'}
                  className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl font-bold text-xs transition-all ${prevUser
                      ? 'bg-[#F7F4EC] hover:bg-[#063B32] hover:text-[#FFFEF9] text-[#18211F] shadow-2xs cursor-pointer border border-[#E5E0D3]'
                      : 'bg-[#FDFBF7] text-[#C9C4B7] border border-[#E5E0D3] cursor-not-allowed opacity-60'
                    }`}
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span>Previous User</span>
                  {prevUser && (
                    <span className="hidden md:inline text-[11px] font-mono font-medium opacity-80">
                      ({prevUser.full_name})
                    </span>
                  )}
                </button>

                {rootId !== null && (
                  <button
                    onClick={() => setRootId(null)}
                    className="flex items-center gap-1 px-3.5 py-2 rounded-xl bg-[#FAF4DC] border border-[#E2C766] hover:bg-[#F4E7B4] text-[#8C6C16] text-xs font-bold transition-colors cursor-pointer"
                    title="Return to your top root node"
                  >
                    <Home className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">My Root</span>
                  </button>
                )}
              </div>

              {/* Center Info: Member Position Counter */}
              <div className="flex items-center gap-2 text-xs font-mono">
                <span className="text-[#69736F] font-sans text-[11px] hidden sm:inline">Viewing Member:</span>
                <span className="font-bold text-[#18211F] bg-[#F7F4EC] px-3 py-1 rounded-lg border border-[#E5E0D3]">
                  {currentIndex >= 0 ? `${currentIndex + 1} / ${members.length}` : '1 / 1'}
                </span>
                <span className="text-[#063B32] font-bold hidden lg:inline truncate max-w-[200px]">
                  {treeData?.full_name} ({treeData?.user_code})
                </span>
              </div>

              <button
                onClick={handleNextUser}
                disabled={!nextUser}
                title={nextUser ? `Next: ${nextUser.full_name} (${nextUser.user_code})` : 'No next member'}
                className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl font-bold text-xs transition-all ${nextUser
                    ? 'bg-[#F7F4EC] hover:bg-[#063B32] hover:text-[#FFFEF9] text-[#18211F] shadow-2xs cursor-pointer border border-[#E5E0D3]'
                    : 'bg-[#FDFBF7] text-[#C9C4B7] border border-[#E5E0D3] cursor-not-allowed opacity-60'
                  }`}
              >
                {nextUser && (
                  <span className="hidden md:inline text-[11px] font-mono font-medium opacity-80">
                    ({nextUser.full_name})
                  </span>
                )}
                <span>Next User</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Tree Canvas */}
          <MatchingTreeCanvas
            rootNode={treeData || null}
            onSelectRootId={(id: number | null) => setRootId(id)}
            depth={depth}
            onDepthChange={(d: number) => setDepth(d)}
            isLoading={isLoading}
            onPrevUser={handlePrevUser}
            onNextUser={handleNextUser}
            prevUser={prevUser}
            nextUser={nextUser}
            currentIndex={currentIndex}
            totalMembers={members.length}
            viewMode={viewMode}
          />
        </>
      )}
    </div>
  );
};

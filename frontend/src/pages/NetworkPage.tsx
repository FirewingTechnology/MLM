import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { BinaryTreeCanvas } from '../components/tree/BinaryTreeCanvas';
import { BinaryTreeNode } from '../types';
import { 
  GitFork, 
  Search, 
  Users, 
  Coins, 
  HelpCircle, 
  Sparkles,
  ArrowRight
} from 'lucide-react';

export const NetworkPage: React.FC = () => {
  const [rootId, setRootId] = useState<number | null>(null);
  const [depth, setDepth] = useState<number>(3);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const { data: treeData, isLoading } = useQuery<BinaryTreeNode>({
    queryKey: ['network', rootId, depth],
    queryFn: async () => {
      const url = rootId ? `/network/${rootId}?depth=${depth}` : `/network?depth=${depth}`;
      const res = await api.get(url);
      return res.data.data;
    },
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

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-brand-400 mb-1">
            <GitFork className="w-4 h-4" />
            <span>Interactive Visualizer</span>
          </div>
          <h1 className="text-2xl font-black text-white">Binary Network Tree</h1>
          <p className="text-xs text-slate-400">
            Explore your dual-leg organization, volume flow, and active distributor placements.
          </p>
        </div>

        {/* Search member bar */}
        <div className="relative w-full sm:w-80">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search member name or code..."
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-navy-900 border border-slate-700/80 text-white text-xs focus:outline-none focus:border-brand-500 font-mono"
            />
          </div>

          {/* Autocomplete dropdown */}
          {searchResults && searchResults.length > 0 && (
            <div className="absolute left-0 right-0 mt-2 rounded-2xl glass-dropdown p-2 shadow-2xl z-40 border border-slate-700">
              <div className="text-[10px] uppercase font-bold text-slate-400 px-2 py-1 mb-1">
                Network Search Results
              </div>
              {searchResults.map((member: any) => (
                <button
                  key={member.id}
                  onClick={() => {
                    setRootId(member.id);
                    setSearchQuery('');
                  }}
                  className="w-full p-2 rounded-xl hover:bg-slate-800 text-left flex items-center justify-between transition-colors text-xs"
                >
                  <div>
                    <div className="font-bold text-white">{member.full_name}</div>
                    <div className="text-[10px] text-slate-400 font-mono">{member.user_code}</div>
                  </div>
                  <span className="text-[10px] bg-brand-500/20 text-brand-300 px-2 py-0.5 rounded font-mono font-bold">
                    View Subtree →
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Network Stats Bar */}
      {treeData && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3 rounded-2xl glass-panel border border-slate-800 text-xs">
            <span className="text-slate-400 text-[10px] uppercase font-bold">Root Node</span>
            <div className="text-sm font-bold text-white truncate mt-0.5">{treeData.full_name}</div>
            <div className="text-[10px] text-brand-400 font-mono">{treeData.user_code}</div>
          </div>

          <div className="p-3 rounded-2xl glass-panel border border-slate-800 text-xs font-mono">
            <span className="text-slate-400 text-[10px] font-sans uppercase font-bold">Left Volume</span>
            <div className="text-sm font-bold text-emerald-400 mt-0.5">₹{treeData.left_bv?.toLocaleString()} BV</div>
            <div className="text-[10px] text-slate-400 font-sans">Carry: ₹{treeData.carry_left_bv?.toLocaleString()}</div>
          </div>

          <div className="p-3 rounded-2xl glass-panel border border-slate-800 text-xs font-mono">
            <span className="text-slate-400 text-[10px] font-sans uppercase font-bold">Right Volume</span>
            <div className="text-sm font-bold text-emerald-400 mt-0.5">₹{treeData.right_bv?.toLocaleString()} BV</div>
            <div className="text-[10px] text-slate-400 font-sans">Carry: ₹{treeData.carry_right_bv?.toLocaleString()}</div>
          </div>

          <div className="p-3 rounded-2xl glass-panel border border-slate-800 text-xs font-mono">
            <span className="text-slate-400 text-[10px] font-sans uppercase font-bold">Matched Volume</span>
            <div className="text-sm font-bold text-purple-400 mt-0.5">₹{treeData.matched_bv?.toLocaleString()} BV</div>
            <div className="text-[10px] text-slate-400 font-sans">10% Commission Basis</div>
          </div>
        </div>
      )}

      {/* Main Canvas */}
      <BinaryTreeCanvas
        rootNode={treeData || null}
        onSelectRootId={(id) => setRootId(id)}
        depth={depth}
        onDepthChange={(d) => setDepth(d)}
        isLoading={isLoading}
      />
    </div>
  );
};

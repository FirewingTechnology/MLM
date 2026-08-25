import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  GitFork,
  Wallet,
  Coins,
  Users,
  PackageCheck,
  ShieldAlert,
  HelpCircle,
  TrendingUp,
} from 'lucide-react';

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user } = useAuth();

  const navLinks = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/network', label: 'Binary Network Tree', icon: GitFork },
    { to: '/packages', label: 'Virtual Packages', icon: PackageCheck },
    { to: '/wallet', label: 'Virtual Wallet & Ledger', icon: Wallet },
    { to: '/commissions', label: 'Commissions & Audit', icon: Coins },
    { to: '/referrals', label: 'Direct Referrals', icon: Users },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
        />
      )}

      <aside
        className={`fixed lg:static top-0 bottom-0 left-0 z-40 w-64 bg-navy-900 border-r border-slate-800/80 flex flex-col justify-between transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="p-4 space-y-6">
          <div className="px-2 pt-2">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3 px-2">
              Main Menu
            </div>
            <nav className="space-y-1">
              {navLinks.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                        isActive
                          ? 'bg-brand-500/10 text-brand-400 border border-brand-500/20 shadow-glow-emerald'
                          : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/50'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>

          {/* Admin section if user is admin */}
          {user?.role === 'ADMIN' && (
            <div className="px-2 pt-4 border-t border-slate-800/80">
              <div className="text-[11px] font-bold uppercase tracking-wider text-amber-400 mb-3 px-2 flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>Admin Suite</span>
              </div>
              <nav className="space-y-1">
                <NavLink
                  to="/admin/dashboard"
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                      isActive
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-glow-amber'
                        : 'text-slate-400 hover:text-amber-300 hover:bg-slate-800/50'
                    }`
                  }
                >
                  <TrendingUp className="w-4 h-4 shrink-0" />
                  <span>Admin Overview</span>
                </NavLink>
                <NavLink
                  to="/admin/users"
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                      isActive
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-glow-amber'
                        : 'text-slate-400 hover:text-amber-300 hover:bg-slate-800/50'
                    }`
                  }
                >
                  <Users className="w-4 h-4 shrink-0" />
                  <span>User Management</span>
                </NavLink>
                <NavLink
                  to="/admin/withdrawals"
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                      isActive
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-glow-amber'
                        : 'text-slate-400 hover:text-amber-300 hover:bg-slate-800/50'
                    }`
                  }
                >
                  <Wallet className="w-4 h-4 shrink-0" />
                  <span>Withdrawal Requests</span>
                </NavLink>
              </nav>
            </div>
          )}
        </div>

        {/* Bottom Referral / Demo Info Card */}
        <div className="p-4 border-t border-slate-800/80">
          <div className="p-3.5 rounded-xl bg-gradient-to-b from-slate-800/60 to-slate-900 border border-slate-700/60 text-xs">
            <div className="flex items-center gap-2 text-brand-400 font-bold mb-1">
              <HelpCircle className="w-4 h-4" />
              <span>Demo Rule Summary</span>
            </div>
            <div className="space-y-1 text-[11px] text-slate-300">
              <p>• Package: <span className="text-white font-semibold">₹35,000</span> (30k BV)</p>
              <p>• Direct Sponsor: <span className="text-brand-400 font-semibold">10% (₹3,000)</span></p>
              <p>• Binary Match: <span className="text-brand-400 font-semibold">10% (Carry-over)</span></p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

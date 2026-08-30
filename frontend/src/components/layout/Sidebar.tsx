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
  Sparkles,
} from 'lucide-react';

import { MyStatusLogo } from '../common/MyStatusLogo';

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user } = useAuth();

  const navLinks = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/network', label: 'Network Tree', icon: GitFork },
    { to: '/packages', label: 'Packages', icon: PackageCheck },
    { to: '/wallet', label: 'Income Wallet & Ledger', icon: Wallet },
    { to: '/commissions', label: 'Income Report', icon: Coins },
    { to: '/referrals', label: 'Direct Referrals', icon: Users },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/60 backdrop-blur-xs z-40 lg:hidden"
        />
      )}

      <aside
        className={`fixed lg:static top-0 bottom-0 left-0 z-40 w-64 bg-[#063B32] border-r border-[#042C26] flex flex-col justify-between transition-transform duration-300 ease-in-out shadow-2xl ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="p-4 space-y-5">
          {/* Brand Logo & Emblem in Sidebar */}
          <div className="px-2 pt-2 pb-2 border-b border-[#0B5145]/60 flex items-center justify-between">
            <MyStatusLogo size="sm" theme="dark" />
            <span className="px-2 py-0.5 rounded-md border border-[#0288D1]/50 text-[#29B6F6] text-[10px] font-mono font-bold">
              PRO
            </span>
          </div>

          <div className="px-1">
            <div className="text-[10px] font-bold uppercase tracking-wider text-[#F7F4EC]/50 mb-2.5 px-3">
              Wealth Navigation
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
                      `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                        isActive
                          ? 'bg-[#0A4D42] text-[#FFFEF9] font-bold border-l-2 border-[#C9A227] shadow-sm'
                          : 'text-[#F7F4EC]/75 hover:text-[#FFFEF9] hover:bg-[#08453A]'
                      }`
                    }
                  >
                    {({ isActive }) => (
                      <>
                        <Icon className={`w-4 h-4 shrink-0 transition-colors ${isActive ? 'text-[#C9A227]' : 'text-[#F7F4EC]/60'}`} />
                        <span>{item.label}</span>
                      </>
                    )}
                  </NavLink>
                );
              })}
            </nav>
          </div>

          {/* Admin section if user is admin */}
          {user?.role === 'ADMIN' && (
            <div className="px-1 pt-4 border-t border-[#0B5145]/60">
              <div className="text-[10px] font-bold uppercase tracking-wider text-[#C9A227] mb-2.5 px-3 flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-[#C9A227]" />
                <span>Superuser Suite</span>
              </div>
              <nav className="space-y-1">
                <NavLink
                  to="/admin/dashboard"
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                      isActive
                        ? 'bg-[#0A4D42] text-[#FFFEF9] font-bold border-l-2 border-[#C9A227]'
                        : 'text-[#F7F4EC]/75 hover:text-[#FFFEF9] hover:bg-[#08453A]'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <TrendingUp className={`w-4 h-4 shrink-0 ${isActive ? 'text-[#C9A227]' : 'text-[#F7F4EC]/60'}`} />
                      <span>Admin Overview</span>
                    </>
                  )}
                </NavLink>
                <NavLink
                  to="/admin/users"
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                      isActive
                        ? 'bg-[#0A4D42] text-[#FFFEF9] font-bold border-l-2 border-[#C9A227]'
                        : 'text-[#F7F4EC]/75 hover:text-[#FFFEF9] hover:bg-[#08453A]'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <Users className={`w-4 h-4 shrink-0 ${isActive ? 'text-[#C9A227]' : 'text-[#F7F4EC]/60'}`} />
                      <span>User Management</span>
                    </>
                  )}
                </NavLink>
                <NavLink
                  to="/admin/withdrawals"
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                      isActive
                        ? 'bg-[#0A4D42] text-[#FFFEF9] font-bold border-l-2 border-[#C9A227]'
                        : 'text-[#F7F4EC]/75 hover:text-[#FFFEF9] hover:bg-[#08453A]'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <Wallet className={`w-4 h-4 shrink-0 ${isActive ? 'text-[#C9A227]' : 'text-[#F7F4EC]/60'}`} />
                      <span>Payout Requests</span>
                    </>
                  )}
                </NavLink>
              </nav>
            </div>
          )}
        </div>

        {/* Bottom Rule Summary Card */}
        <div className="p-4 border-t border-[#0B5145]/60">
          <div className="p-3.5 rounded-2xl bg-[#042C26] border border-[#C9A227]/25 text-xs text-[#F7F4EC]">
            <div className="flex items-center gap-2 text-[#C9A227] font-bold mb-1.5">
              <HelpCircle className="w-4 h-4" />
              <span>Platform Rule Summary</span>
            </div>
            <div className="space-y-1 text-[11px] text-[#F7F4EC]/80 font-medium">
              <p>• Qualifying Package: <span className="text-[#FFFEF9] font-bold">₹35,000</span> (30k BV)</p>
              <p>• Direct Sponsor: <span className="text-[#C9A227] font-bold">10% (₹3,000)</span></p>
              <p>• Binary Pair Bonus: <span className="text-[#E2C766] font-bold">₹10,000 / pair</span></p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};


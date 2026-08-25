import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  LogOut, 
  User as UserIcon, 
  ShoppingBag, 
  Shield, 
  ChevronDown, 
  Sparkles,
  Menu,
  X
} from 'lucide-react';

interface NavbarProps {
  onOpenPurchaseModal?: () => void;
  onToggleSidebar?: () => void;
  isSidebarOpen?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenPurchaseModal, onToggleSidebar, isSidebarOpen }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 border-b border-slate-800/80 bg-navy-900/90 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          aria-label="Toggle Navigation"
        >
          {isSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        <Link to="/dashboard" className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-emerald-400 flex items-center justify-center shadow-glow-emerald">
            <Sparkles className="w-5 h-5 text-navy-950 font-bold" />
          </div>
          <div>
            <div className="font-extrabold text-base tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent flex items-center gap-1.5">
              <span>BINARY<span className="text-brand-400">MLM</span></span>
              <span className="text-[10px] font-bold tracking-wider px-1.5 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">PRO</span>
            </div>
          </div>
        </Link>
      </div>

      <div className="flex items-center gap-3">
        {/* Virtual Buy Package CTA */}
        {onOpenPurchaseModal && (
          <button
            onClick={onOpenPurchaseModal}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-400 hover:to-emerald-500 text-navy-950 font-bold text-xs sm:text-sm shadow-glow-emerald transition-all transform hover:scale-[1.02] active:scale-[0.98]"
          >
            <ShoppingBag className="w-4 h-4" />
            <span>Buy Virtual Package</span>
          </button>
        )}

        {/* User Account / Dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2.5 p-1.5 pl-2 rounded-xl border border-slate-800 hover:border-slate-700 bg-navy-800/60 hover:bg-navy-800 transition-all text-left"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-brand-500 flex items-center justify-center font-bold text-xs text-white uppercase shadow-sm">
              {user?.full_name?.substring(0, 2) || 'US'}
            </div>
            <div className="hidden md:block pr-1 text-xs">
              <div className="font-bold text-slate-200 truncate max-w-[120px]">{user?.full_name}</div>
              <div className="text-slate-400 text-[10px] font-mono">{user?.user_code}</div>
            </div>
            <ChevronDown className="w-4 h-4 text-slate-400" />
          </button>

          {dropdownOpen && (
            <div
              className="absolute right-0 mt-2 w-56 rounded-xl glass-dropdown shadow-2xl p-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150"
              onClick={() => setDropdownOpen(false)}
            >
              <div className="px-3 py-2 border-b border-slate-800 text-xs mb-1">
                <div className="font-bold text-slate-100">{user?.full_name}</div>
                <div className="text-slate-400 text-[11px] font-mono">{user?.email}</div>
                <div className="mt-1 flex items-center gap-1.5">
                  <span className={`inline-block w-2 h-2 rounded-full ${user?.is_active ? 'bg-brand-400' : 'bg-amber-400'}`} />
                  <span className="text-[10px] text-slate-300 uppercase tracking-wider">{user?.is_active ? 'Active Distributor' : 'Inactive Account'}</span>
                </div>
              </div>

              {user?.role === 'ADMIN' && (
                <Link
                  to="/admin/dashboard"
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold text-amber-400 hover:bg-amber-500/10 transition-colors"
                >
                  <Shield className="w-4 h-4" />
                  <span>Admin Control Center</span>
                </Link>
              )}

              <Link
                to="/dashboard"
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <UserIcon className="w-4 h-4 text-slate-400" />
                <span>My Dashboard</span>
              </Link>

              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-rose-400 hover:bg-rose-500/10 transition-colors mt-1"
              >
                <LogOut className="w-4 h-4" />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

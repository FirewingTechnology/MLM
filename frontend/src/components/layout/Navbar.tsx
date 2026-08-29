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
  X,
  Clock
} from 'lucide-react';

import { MyStatusLogo } from '../common/MyStatusLogo';
import { useTime } from '../../context/TimeContext';

interface NavbarProps {
  onOpenPurchaseModal?: () => void;
  onToggleSidebar?: () => void;
  isSidebarOpen?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenPurchaseModal, onToggleSidebar, isSidebarOpen }) => {
  const { user, logout } = useAuth();
  const { slotInfo, currentDisplayTime, isDemoMode } = useTime();
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 border-b border-[#E5E0D3] bg-[#F7F4EC]/95 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30 shadow-wealth-card">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 rounded-xl text-[#69736F] hover:text-[#18211F] hover:bg-[#EFECE2] transition-colors cursor-pointer"
          aria-label="Toggle Navigation"
        >
          {isSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        <Link to="/dashboard" className="flex items-center gap-2.5">
          <MyStatusLogo size="sm" />
          <span className="hidden sm:inline-block text-[10px] font-bold tracking-wider px-1.5 py-0.5 rounded bg-[#FAF4DC] text-[#8C6C16] border border-[#E2C766]/50 font-mono">
            PRO
          </span>
        </Link>
      </div>

      <div className="flex items-center gap-3">
        {/* Live Slot Status Indicator */}
        {slotInfo && (
          <div className={`hidden sm:flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono border ${
            isDemoMode
              ? 'bg-[#FAF4DC] border-[#E2C766] text-[#8C6C16]'
              : 'bg-[#E0F3EE] border-[#8DCFBF] text-[#063B32]'
          }`}>
            <span className={`w-2 h-2 rounded-full ${isDemoMode ? 'bg-[#C88A16] animate-pulse' : 'bg-[#0E9F6E] animate-ping'}`} />
            <span className="font-bold">{isDemoMode ? 'DEMO TIME' : 'LIVE IST'}</span>
            <span className="opacity-40">•</span>
            <span className="font-medium text-[11px]">{currentDisplayTime}</span>
          </div>
        )}

        {/* Buy Sub Franchise Package CTA */}
        {onOpenPurchaseModal && (
          <button
            onClick={onOpenPurchaseModal}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/35 font-bold text-xs sm:text-sm shadow-wealth-card transition-all transform hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
          >
            <ShoppingBag className="w-4 h-4 text-[#C9A227]" />
            <span>Buy Sub Franchise</span>
          </button>
        )}

        {/* User Account / Dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2.5 p-1.5 pl-2 rounded-xl border border-[#E5E0D3] hover:border-[#D3CCA9] bg-[#FFFEF9] hover:bg-[#FAF8F2] transition-all text-left cursor-pointer shadow-2xs"
          >
            <div className="w-8 h-8 rounded-lg bg-[#063B32] border border-[#C9A227]/40 flex items-center justify-center font-bold text-xs text-[#E2C766] uppercase shadow-xs">
              {user?.full_name?.substring(0, 2) || 'US'}
            </div>
            <div className="hidden md:block pr-1 text-xs">
              <div className="font-bold text-[#18211F] truncate max-w-[120px]">{user?.full_name}</div>
              <div className="text-[#69736F] text-[10px] font-mono">{user?.user_code}</div>
            </div>
            <ChevronDown className="w-4 h-4 text-[#69736F]" />
          </button>

          {dropdownOpen && (
            <div
              className="absolute right-0 mt-2 w-56 rounded-2xl bg-[#FFFEF9] shadow-wealth-elevated p-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150 border border-[#E5E0D3]"
              onClick={() => setDropdownOpen(false)}
            >
              <div className="px-3 py-2 border-b border-[#EFECE2] text-xs mb-1">
                <div className="font-bold text-[#18211F]">{user?.full_name}</div>
                <div className="text-[#69736F] text-[11px] font-mono">{user?.email}</div>
                <div className="mt-1.5 flex items-center gap-1.5">
                  <span className={`inline-block w-2 h-2 rounded-full ${user?.is_active ? 'bg-[#0E9F6E]' : 'bg-[#C88A16]'}`} />
                  <span className="text-[10px] text-[#69736F] font-semibold uppercase tracking-wider">{user?.is_active ? 'Active Distributor' : 'Inactive Account'}</span>
                </div>
              </div>

              {user?.role === 'ADMIN' && (
                <Link
                  to="/admin/dashboard"
                  className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold text-[#8C6C16] hover:bg-[#FAF4DC] transition-colors"
                >
                  <Shield className="w-4 h-4 text-[#C9A227]" />
                  <span>Admin Control Center</span>
                </Link>
              )}

              <Link
                to="/dashboard"
                className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs text-[#18211F] hover:bg-[#EFECE2] transition-colors font-medium"
              >
                <UserIcon className="w-4 h-4 text-[#69736F]" />
                <span>My Dashboard</span>
              </Link>

              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs text-[#C94B4B] hover:bg-[#FDF2F2] transition-colors mt-1 font-semibold cursor-pointer"
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


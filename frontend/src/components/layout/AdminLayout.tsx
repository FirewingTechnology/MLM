import React, { useState } from 'react';
import { Outlet, Navigate, Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { DemoBanner } from './DemoBanner';
import { DemoResetModal } from '../modals/DemoResetModal';
import {
  ShieldAlert,
  LayoutDashboard,
  Users,
  Wallet,
  RotateCcw,
  LogOut,
  ArrowLeft,
  Sparkles,
} from 'lucide-react';

export const AdminLayout: React.FC = () => {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const navigate = useNavigate();
  const [resetModalOpen, setResetModalOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#F7F4EC] flex items-center justify-center">
        <div className="w-10 h-10 rounded-full border-2 border-[#C9A227] border-t-[#063B32] animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated || user?.role !== 'ADMIN') {
    return <Navigate to="/dashboard" replace />;
  }

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-[#F7F4EC] text-[#18211F] flex flex-col">
      <DemoBanner />

      {/* Admin Navbar */}
      <header className="h-16 border-b border-[#E5E0D3] bg-[#FFFEF9]/95 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30 shadow-wealth-card">
        <div className="flex items-center gap-4">
          <Link to="/admin/dashboard" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-[#063B32] border border-[#C9A227]/50 flex items-center justify-center shadow-wealth-gold">
              <ShieldAlert className="w-5 h-5 text-[#C9A227]" />
            </div>
            <div>
              <div className="font-heading font-extrabold text-sm tracking-tight text-[#18211F] flex items-center gap-2">
                <span>ADMIN CONTROL</span>
                <span className="text-[10px] bg-[#FAF4DC] text-[#8C6C16] font-bold px-2 py-0.5 rounded border border-[#E2C766]/60 font-mono">
                  SUPERUSER
                </span>
              </div>
            </div>
          </Link>
        </div>

        <div className="flex items-center gap-3">
          {/* Quick Demo Reset button */}
          <button
            onClick={() => setResetModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#FDF2F2] hover:bg-[#FDE8E8] text-[#C94B4B] border border-[#F8B4B4] text-xs font-bold transition-all cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Demo DB</span>
          </button>

          <Link
            to="/dashboard"
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#EFECE2] hover:bg-[#E5E0D3] text-[#18211F] text-xs font-semibold transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5 text-[#063B32]" />
            <span>User View</span>
          </Link>

          <button
            onClick={handleLogout}
            className="p-2 rounded-xl text-[#69736F] hover:text-[#C94B4B] hover:bg-[#FDF2F2] transition-colors cursor-pointer"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Admin Nav Sub-bar */}
      <div className="border-b border-[#E5E0D3] bg-[#FFFEF9] px-4 sm:px-6 py-2 flex items-center gap-2 overflow-x-auto">
        <NavLink
          to="/admin/dashboard"
          end
          className={({ isActive }) =>
            `px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap ${
              isActive
                ? 'bg-[#063B32] text-[#FFFEF9] shadow-sm'
                : 'text-[#69736F] hover:text-[#18211F] hover:bg-[#EFECE2]'
            }`
          }
        >
          {({ isActive }) => (
            <>
              <LayoutDashboard className={`w-3.5 h-3.5 ${isActive ? 'text-[#C9A227]' : 'text-[#69736F]'}`} />
              <span>System KPIs</span>
            </>
          )}
        </NavLink>

        <NavLink
          to="/admin/users"
          className={({ isActive }) =>
            `px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap ${
              isActive
                ? 'bg-[#063B32] text-[#FFFEF9] shadow-sm'
                : 'text-[#69736F] hover:text-[#18211F] hover:bg-[#EFECE2]'
            }`
          }
        >
          {({ isActive }) => (
            <>
              <Users className={`w-3.5 h-3.5 ${isActive ? 'text-[#C9A227]' : 'text-[#69736F]'}`} />
              <span>All Distributors</span>
            </>
          )}
        </NavLink>

        <NavLink
          to="/admin/withdrawals"
          className={({ isActive }) =>
            `px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap ${
              isActive
                ? 'bg-[#063B32] text-[#FFFEF9] shadow-sm'
                : 'text-[#69736F] hover:text-[#18211F] hover:bg-[#EFECE2]'
            }`
          }
        >
          {({ isActive }) => (
            <>
              <Wallet className={`w-3.5 h-3.5 ${isActive ? 'text-[#C9A227]' : 'text-[#69736F]'}`} />
              <span>Withdrawal Approvals</span>
            </>
          )}
        </NavLink>
      </div>

      {/* Main Content */}
      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
        <Outlet />
      </main>

      <DemoResetModal
        isOpen={resetModalOpen}
        onClose={() => setResetModalOpen(false)}
      />
    </div>
  );
};


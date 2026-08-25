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
      <div className="min-h-screen bg-navy-950 flex items-center justify-center">
        <div className="w-10 h-10 rounded-full border-2 border-amber-400 border-t-transparent animate-spin" />
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
    <div className="min-h-screen bg-navy-950 text-slate-100 flex flex-col">
      <DemoBanner />

      {/* Admin Navbar */}
      <header className="h-16 border-b border-amber-500/30 bg-navy-900/90 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-4">
          <Link to="/admin/dashboard" className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-amber-500 to-amber-600 flex items-center justify-center shadow-glow-amber">
              <ShieldAlert className="w-5 h-5 text-navy-950 font-bold" />
            </div>
            <div>
              <div className="font-black text-sm tracking-tight text-white flex items-center gap-2">
                <span>ADMIN PORTAL</span>
                <span className="text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded border border-amber-500/30">
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
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-bold transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Demo DB</span>
          </button>

          <Link
            to="/dashboard"
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>User View</span>
          </Link>

          <button
            onClick={handleLogout}
            className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Admin Nav Sub-bar */}
      <div className="border-b border-slate-800 bg-navy-900/60 px-4 sm:px-6 py-2 flex items-center gap-2 overflow-x-auto">
        <NavLink
          to="/admin/dashboard"
          end
          className={({ isActive }) =>
            `px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap ${
              isActive
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                : 'text-slate-400 hover:text-white'
            }`
          }
        >
          <LayoutDashboard className="w-3.5 h-3.5" />
          <span>System KPIs</span>
        </NavLink>

        <NavLink
          to="/admin/users"
          className={({ isActive }) =>
            `px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap ${
              isActive
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                : 'text-slate-400 hover:text-white'
            }`
          }
        >
          <Users className="w-3.5 h-3.5" />
          <span>All Distributors</span>
        </NavLink>

        <NavLink
          to="/admin/withdrawals"
          className={({ isActive }) =>
            `px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap ${
              isActive
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                : 'text-slate-400 hover:text-white'
            }`
          }
        >
          <Wallet className="w-3.5 h-3.5" />
          <span>Withdrawal Approvals</span>
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

import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  Home, 
  GitFork, 
  Wallet, 
  MoreHorizontal, 
  Users, 
  ListOrdered, 
  Shield, 
  LogOut, 
  X,
  ShoppingBag
} from 'lucide-react';

interface BottomNavProps {
  onOpenPurchaseModal?: () => void;
}

export const BottomNav: React.FC<BottomNavProps> = ({ onOpenPurchaseModal }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isMoreOpen, setIsMoreOpen] = useState(false);

  const handleLogout = () => {
    setIsMoreOpen(false);
    logout();
    navigate('/login');
  };

  return (
    <>
      {/* Fixed Bottom Navigation Bar on Mobile */}
      <div className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-navy-900/95 backdrop-blur-lg border-t border-slate-800 px-3 py-2 flex items-center justify-around">
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            `flex flex-col items-center gap-1 py-1 px-3 rounded-xl transition-all ${
              isActive ? 'text-brand-400 font-bold' : 'text-slate-400 hover:text-white'
            }`
          }
        >
          <Home className="w-5 h-5" />
          <span className="text-[10px] tracking-tight">Home</span>
        </NavLink>

        <NavLink
          to="/network"
          className={({ isActive }) =>
            `flex flex-col items-center gap-1 py-1 px-3 rounded-xl transition-all ${
              isActive ? 'text-brand-400 font-bold' : 'text-slate-400 hover:text-white'
            }`
          }
        >
          <GitFork className="w-5 h-5" />
          <span className="text-[10px] tracking-tight">Network</span>
        </NavLink>

        <NavLink
          to="/wallet"
          className={({ isActive }) =>
            `flex flex-col items-center gap-1 py-1 px-3 rounded-xl transition-all ${
              isActive ? 'text-brand-400 font-bold' : 'text-slate-400 hover:text-white'
            }`
          }
        >
          <Wallet className="w-5 h-5" />
          <span className="text-[10px] tracking-tight">Wallet</span>
        </NavLink>

        <button
          onClick={() => setIsMoreOpen(true)}
          className="flex flex-col items-center gap-1 py-1 px-3 rounded-xl text-slate-400 hover:text-white transition-all"
        >
          <MoreHorizontal className="w-5 h-5" />
          <span className="text-[10px] tracking-tight">More</span>
        </button>
      </div>

      {/* "More" Bottom Sheet on Mobile */}
      {isMoreOpen && (
        <div 
          className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-end animate-in fade-in duration-200"
          onClick={() => setIsMoreOpen(false)}
        >
          <div 
            className="w-full bg-navy-900 border-t border-slate-700 rounded-t-3xl p-5 space-y-4 shadow-2xl animate-in slide-in-from-bottom duration-250 pb-8"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <div className="text-sm font-bold text-white">{user?.full_name}</div>
                <div className="text-[11px] font-mono text-brand-400">{user?.referral_code}</div>
              </div>
              <button 
                onClick={() => setIsMoreOpen(false)}
                className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2.5 text-xs">
              <button
                onClick={() => {
                  setIsMoreOpen(false);
                  if (onOpenPurchaseModal) onOpenPurchaseModal();
                }}
                className="flex items-center gap-2.5 p-3 rounded-xl bg-brand-500/10 border border-brand-500/30 text-brand-300 font-bold hover:bg-brand-500/20 text-left"
              >
                <ShoppingBag className="w-4 h-4 text-brand-400" />
                <span>Buy Package</span>
              </button>

              <NavLink
                to="/referrals"
                onClick={() => setIsMoreOpen(false)}
                className="flex items-center gap-2.5 p-3 rounded-xl bg-slate-800/80 border border-slate-700/60 text-slate-200 font-semibold hover:bg-slate-800"
              >
                <Users className="w-4 h-4 text-blue-400" />
                <span>Direct Team</span>
              </NavLink>

              <NavLink
                to="/commissions"
                onClick={() => setIsMoreOpen(false)}
                className="flex items-center gap-2.5 p-3 rounded-xl bg-slate-800/80 border border-slate-700/60 text-slate-200 font-semibold hover:bg-slate-800"
              >
                <ListOrdered className="w-4 h-4 text-emerald-400" />
                <span>Commissions</span>
              </NavLink>

              {user?.role === 'ADMIN' && (
                <NavLink
                  to="/admin/dashboard"
                  onClick={() => setIsMoreOpen(false)}
                  className="flex items-center gap-2.5 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 font-bold hover:bg-amber-500/20"
                >
                  <Shield className="w-4 h-4 text-amber-400" />
                  <span>Admin Panel</span>
                </NavLink>
              )}
            </div>

            <div className="pt-2 border-t border-slate-800">
              <button
                onClick={handleLogout}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 hover:bg-rose-500/20 text-xs font-bold transition-all"
              >
                <LogOut className="w-4 h-4" />
                <span>Sign Out of Account</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

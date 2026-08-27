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
      <div className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-[#063B32] border-t border-[#042C26] px-3 py-2 flex items-center justify-around shadow-2xl">
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            `flex flex-col items-center gap-1 py-1 px-3 rounded-xl transition-all ${
              isActive ? 'text-[#C9A227] font-bold' : 'text-[#F7F4EC]/65 hover:text-[#FFFEF9]'
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
              isActive ? 'text-[#C9A227] font-bold' : 'text-[#F7F4EC]/65 hover:text-[#FFFEF9]'
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
              isActive ? 'text-[#C9A227] font-bold' : 'text-[#F7F4EC]/65 hover:text-[#FFFEF9]'
            }`
          }
        >
          <Wallet className="w-5 h-5" />
          <span className="text-[10px] tracking-tight">Wallet</span>
        </NavLink>

        <button
          onClick={() => setIsMoreOpen(true)}
          className="flex flex-col items-center gap-1 py-1 px-3 rounded-xl text-[#F7F4EC]/65 hover:text-[#FFFEF9] transition-all cursor-pointer"
        >
          <MoreHorizontal className="w-5 h-5" />
          <span className="text-[10px] tracking-tight">More</span>
        </button>
      </div>

      {/* "More" Bottom Sheet on Mobile */}
      {isMoreOpen && (
        <div 
          className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-end animate-in fade-in duration-200"
          onClick={() => setIsMoreOpen(false)}
        >
          <div 
            className="w-full bg-[#FFFEF9] border-t border-[#E5E0D3] rounded-t-3xl p-5 space-y-4 shadow-wealth-elevated animate-in slide-in-from-bottom duration-250 pb-8"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#EFECE2]">
              <div>
                <div className="text-sm font-bold text-[#18211F]">{user?.full_name}</div>
                <div className="text-[11px] font-mono text-[#063B32] font-bold">{user?.referral_code}</div>
              </div>
              <button 
                onClick={() => setIsMoreOpen(false)}
                className="p-1.5 rounded-xl bg-[#EFECE2] text-[#69736F] hover:text-[#18211F] cursor-pointer"
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
                className="flex items-center gap-2.5 p-3 rounded-2xl bg-[#063B32] text-[#FFFEF9] font-bold hover:bg-[#042C26] text-left cursor-pointer border border-[#C9A227]/30"
              >
                <ShoppingBag className="w-4 h-4 text-[#C9A227]" />
                <span>Buy Package</span>
              </button>

              <NavLink
                to="/referrals"
                onClick={() => setIsMoreOpen(false)}
                className="flex items-center gap-2.5 p-3 rounded-2xl bg-[#FDFBF7] border border-[#E5E0D3] text-[#18211F] font-semibold hover:bg-[#FAF8F2]"
              >
                <Users className="w-4 h-4 text-[#063B32]" />
                <span>Direct Team</span>
              </NavLink>

              <NavLink
                to="/commissions"
                onClick={() => setIsMoreOpen(false)}
                className="flex items-center gap-2.5 p-3 rounded-2xl bg-[#FDFBF7] border border-[#E5E0D3] text-[#18211F] font-semibold hover:bg-[#FAF8F2]"
              >
                <ListOrdered className="w-4 h-4 text-[#C9A227]" />
                <span>Commissions</span>
              </NavLink>

              {user?.role === 'ADMIN' && (
                <NavLink
                  to="/admin/dashboard"
                  onClick={() => setIsMoreOpen(false)}
                  className="flex items-center gap-2.5 p-3 rounded-2xl bg-[#FAF4DC] border border-[#E2C766] text-[#8C6C16] font-bold hover:bg-[#F4E7B4]"
                >
                  <Shield className="w-4 h-4 text-[#C9A227]" />
                  <span>Admin Panel</span>
                </NavLink>
              )}
            </div>

            <div className="pt-2 border-t border-[#EFECE2]">
              <button
                onClick={handleLogout}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-[#FDF2F2] border border-[#F8B4B4] text-[#C94B4B] hover:bg-[#FDE8E8] text-xs font-bold transition-all cursor-pointer"
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


import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import api from '../services/api';
import { MyStatusLogo } from '../components/common/MyStatusLogo';
import { 
  Sparkles, 
  Lock, 
  User as UserIcon, 
  ArrowRight, 
  ShieldCheck, 
  AlertTriangle,
  Loader2
} from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.post('/auth/login', { identifier, password });
      if (res.data?.success) {
        login(res.data.data.token, res.data.data.user);
        showToast(`Welcome back, ${res.data.data.user.full_name}!`, 'success');
        if (res.data.data.user.role === 'ADMIN') {
          navigate('/admin/dashboard');
        } else {
          navigate('/dashboard');
        }
      } else {
        showToast(res.data?.error?.message || 'Login failed. Please check your credentials.', 'error');
      }
    } catch (err: any) {
      showToast(err.response?.data?.error?.message || 'Login failed. Check your credentials or backend connection.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F4EC] flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-6">
        <div className="flex justify-center mb-2">
          <MyStatusLogo variant="full" size="lg" />
        </div>
        <p className="text-xs text-[#69736F] font-medium mt-1">
          Sign in to access your partner dashboard
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md px-4">
        <div className="bg-[#FFFEF9] rounded-3xl p-6 sm:p-8 shadow-wealth-card border border-[#E5E0D3]">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-[#18211F] mb-1.5">
                Email / User Code / Referral Code
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#69736F]">
                  <UserIcon className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder="name@example.com or User Code"
                  required
                  className="w-full pl-10 pr-4 py-3 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] text-sm focus:outline-none focus:border-[#063B32] focus:ring-2 focus:ring-[#063B32]/10 transition-all font-mono shadow-xs"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-[#18211F] mb-1.5">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#69736F]">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full pl-10 pr-4 py-3 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] text-sm focus:outline-none focus:border-[#063B32] focus:ring-2 focus:ring-[#063B32]/10 transition-all font-mono shadow-xs"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/30 font-heading font-bold text-sm shadow-wealth-card transition-all transform hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 mt-2 cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-[#C9A227]" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <>
                  <span>Sign In to Dashboard</span>
                  <ArrowRight className="w-4 h-4 text-[#C9A227]" />
                </>
              )}
            </button>
          </form>

          {/* Registration link */}
          <div className="mt-6 pt-5 border-t border-[#E5E0D3] text-center text-xs text-[#69736F]">
            New partner?{' '}
            <Link to="/register" className="text-[#063B32] hover:text-[#042C26] font-bold">
              Register with an invitation link
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};


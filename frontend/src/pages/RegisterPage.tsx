import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import api from '../services/api';
import { 
  Sparkles, 
  User as UserIcon, 
  Mail, 
  Phone, 
  Lock, 
  Link2, 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight, 
  GitFork,
  Loader2 
} from 'lucide-react';

export const RegisterPage: React.FC = () => {
  const { login } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [mobile, setMobile] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [referralCode, setReferralCode] = useState('');
  const [binaryPosition, setBinaryPosition] = useState<'LEFT' | 'RIGHT'>('LEFT');
  const [binaryParentCode, setBinaryParentCode] = useState('');

  const [sponsorInfo, setSponsorInfo] = useState<{ valid: boolean; sponsor_name: string; referral_code: string } | null>(null);
  const [checkingReferral, setCheckingReferral] = useState(false);
  const [loading, setLoading] = useState(false);

  // Auto populate ref from URL
  useEffect(() => {
    const refParam = searchParams.get('ref');
    if (refParam) {
      setReferralCode(refParam.toUpperCase());
      verifyReferral(refParam.toUpperCase());
    } else {
      // Default to Amol's code for smooth demo testing if no ref provided
      setReferralCode('AMOL001');
      verifyReferral('AMOL001');
    }
  }, [searchParams]);

  const verifyReferral = async (code: string) => {
    if (!code || code.trim().length < 3) {
      setSponsorInfo(null);
      return;
    }
    setCheckingReferral(true);
    try {
      const res = await api.get(`/referral/${code.trim()}`);
      if (res.data?.data?.valid) {
        setSponsorInfo(res.data.data);
      } else {
        setSponsorInfo(null);
      }
    } catch {
      setSponsorInfo(null);
    } finally {
      setCheckingReferral(false);
    }
  };

  const handleReferralChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const code = e.target.value.toUpperCase();
    setReferralCode(code);
    if (code.length >= 4) {
      verifyReferral(code);
    } else {
      setSponsorInfo(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      showToast('Passwords do not match.', 'error');
      return;
    }

    if (!sponsorInfo) {
      showToast('Please provide a valid direct referral sponsor code.', 'error');
      return;
    }

    setLoading(true);
    try {
      const res = await api.post('/auth/register', {
        full_name: fullName,
        email,
        mobile,
        password,
        confirm_password: confirmPassword,
        referral_code: referralCode,
        binary_position: binaryPosition,
        binary_parent_code: binaryParentCode.trim() || undefined,
      });

      if (res.data?.success) {
        login(res.data.data.token, res.data.data.user);
        showToast('Registration successful! Welcome to the Demo Binary MLM platform.', 'success');
        navigate('/dashboard');
      }
    } catch (err: any) {
      showToast(err.response?.data?.error?.message || 'Registration failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-navy-950 flex flex-col justify-center py-10 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-xl text-center mb-5">
        <div className="flex items-center justify-center gap-2 mb-2">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-emerald-400 flex items-center justify-center shadow-glow-emerald">
            <Sparkles className="w-5 h-5 text-navy-950 font-bold" />
          </div>
          <span className="font-extrabold text-2xl tracking-tight text-white">
            BINARY<span className="text-brand-400">MLM</span>
          </span>
        </div>
        <p className="text-xs text-slate-400">
          Create a new simulated distributor account in the binary tree
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-xl px-4">
        <div className="glass-panel rounded-3xl p-6 sm:p-8 shadow-2xl border border-slate-800">
          {/* Sponsor card verification */}
          <div className="mb-6 p-3.5 rounded-2xl bg-navy-900/90 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-brand-500/20 text-brand-400 flex items-center justify-center">
                <Link2 className="w-5 h-5" />
              </div>
              <div>
                <div className="text-[10px] uppercase font-bold text-slate-400">Direct Sponsor</div>
                {sponsorInfo ? (
                  <div className="flex items-center gap-1.5 text-xs font-bold text-white">
                    <CheckCircle2 className="w-3.5 h-3.5 text-brand-400" />
                    <span>{sponsorInfo.sponsor_name}</span>
                    <span className="text-brand-400 font-mono">({sponsorInfo.referral_code})</span>
                  </div>
                ) : checkingReferral ? (
                  <div className="text-xs text-slate-400 flex items-center gap-1">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    <span>Verifying sponsor code...</span>
                  </div>
                ) : (
                  <div className="text-xs text-amber-400 flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    <span>No valid sponsor code entered</span>
                  </div>
                )}
              </div>
            </div>

            <div className="text-right">
              <span className="text-[10px] text-slate-500 font-mono">Step 1 of 2</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full Name & Mobile */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Full Name
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <UserIcon className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Ramesh Kumar"
                    required
                    className="w-full pl-9 pr-3 py-2 rounded-xl bg-navy-950/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-brand-500 font-medium"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Mobile Number
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Phone className="w-4 h-4" />
                  </div>
                  <input
                    type="tel"
                    value={mobile}
                    onChange={(e) => setMobile(e.target.value)}
                    placeholder="e.g. 9876543210"
                    required
                    className="w-full pl-9 pr-3 py-2 rounded-xl bg-navy-950/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-brand-500 font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ramesh@example.com"
                  required
                  className="w-full pl-9 pr-3 py-2 rounded-xl bg-navy-950/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-brand-500 font-mono"
                />
              </div>
            </div>

            {/* Password & Confirm */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    className="w-full pl-9 pr-3 py-2 rounded-xl bg-navy-950/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-brand-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Confirm Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    className="w-full pl-9 pr-3 py-2 rounded-xl bg-navy-950/80 border border-slate-700 text-white text-xs focus:outline-none focus:border-brand-500 font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Referral Code & Placement */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Referral Code (Sponsor)
                </label>
                <input
                  type="text"
                  value={referralCode}
                  onChange={handleReferralChange}
                  placeholder="AMOL001"
                  required
                  className="w-full px-3.5 py-2 rounded-xl bg-navy-950/80 border border-slate-700 text-white text-xs font-mono uppercase focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Preferred Binary Leg
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setBinaryPosition('LEFT')}
                    className={`py-2 rounded-xl text-xs font-bold transition-all border ${
                      binaryPosition === 'LEFT'
                        ? 'bg-brand-500/20 text-brand-400 border-brand-500/40'
                        : 'bg-navy-950/60 border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    Left Leg
                  </button>
                  <button
                    type="button"
                    onClick={() => setBinaryPosition('RIGHT')}
                    className={`py-2 rounded-xl text-xs font-bold transition-all border ${
                      binaryPosition === 'RIGHT'
                        ? 'bg-brand-500/20 text-brand-400 border-brand-500/40'
                        : 'bg-navy-950/60 border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    Right Leg
                  </button>
                </div>
              </div>
            </div>

            {/* Optional Specific Binary Parent code */}
            <div>
              <label className="block text-[11px] text-slate-400 mb-1">
                Specific Placement Parent Code (Optional — leave blank for auto extreme leg placement)
              </label>
              <input
                type="text"
                value={binaryParentCode}
                onChange={(e) => setBinaryParentCode(e.target.value.toUpperCase())}
                placeholder="e.g. USR-00003 or RAHUL001 (Optional)"
                className="w-full px-3.5 py-2 rounded-xl bg-navy-950/60 border border-slate-800 text-white text-xs font-mono uppercase focus:outline-none focus:border-brand-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !sponsorInfo}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-400 hover:to-emerald-500 text-navy-950 font-bold text-sm shadow-glow-emerald transition-all transform hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 mt-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Registering Member...</span>
                </>
              ) : (
                <>
                  <span>Complete Virtual Registration</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-5 text-center text-xs text-slate-400">
            Already have an account?{' '}
            <Link to="/login" className="text-brand-400 hover:text-brand-300 font-bold">
              Sign In to Demo
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

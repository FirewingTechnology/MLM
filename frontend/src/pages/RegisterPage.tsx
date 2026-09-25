import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import api from '../services/api';
import { MyStatusLogo } from '../components/common/MyStatusLogo';
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
  const [binaryPosition, setbinaryPosition] = useState<'LEFT' | 'RIGHT'>('LEFT');
  const [binaryParentCode, setbinaryParentCode] = useState('');

  const [sponsorInfo, setSponsorInfo] = useState<{
    valid: boolean;
    sponsor_name: string;
    sponsor_code: string;
    referral_code: string;
    placement_side?: 'LEFT' | 'RIGHT' | null;
    is_locked?: boolean;
    token?: string | null;
  } | null>(null);
  const [checkingReferral, setCheckingReferral] = useState(false);
  const [loading, setLoading] = useState(false);

  // Auto populate ref and leg from URL
  useEffect(() => {
    const refParam = searchParams.get('ref');
    const legParam = searchParams.get('leg')?.toUpperCase();
    if (legParam === 'LEFT' || legParam === 'RIGHT') {
      setbinaryPosition(legParam);
    }
    if (refParam) {
      setReferralCode(refParam);
      verifyReferral(refParam);
    }
  }, [searchParams]);

  const verifyReferral = async (codeOrToken: string) => {
    if (!codeOrToken || codeOrToken.trim().length < 3) {
      setSponsorInfo(null);
      return;
    }
    setCheckingReferral(true);
    try {
      const res = await api.get(`/referral/validate/${codeOrToken.trim()}`);
      if (res.data?.data?.valid) {
        const valData = res.data.data;
        setSponsorInfo(valData);
        if (valData.is_locked && valData.placement_side) {
          setbinaryPosition(valData.placement_side);
          setbinaryParentCode('');
        }
      } else {
        setSponsorInfo(null);
      }
    } catch {
      // Fallback for direct lookup
      try {
        const res2 = await api.get(`/referral/${codeOrToken.trim()}`);
        if (res2.data?.data?.valid) {
          const valData = res2.data.data;
          setSponsorInfo(valData);
          if (valData.is_locked && valData.placement_side) {
            setbinaryPosition(valData.placement_side);
          }
        } else {
          setSponsorInfo(null);
        }
      } catch {
        setSponsorInfo(null);
      }
    } finally {
      setCheckingReferral(false);
    }
  };

  const handleReferralChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const code = e.target.value;
    setReferralCode(code);
    if (code.trim().length >= 4) {
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
      showToast('Please provide a valid direct referral sponsor link or code.', 'error');
      return;
    }

    setLoading(true);
    try {
      const payload: Record<string, any> = {
        full_name: fullName,
        email,
        mobile,
        password,
        confirm_password: confirmPassword,
        referral_code: sponsorInfo.referral_code || referralCode,
        binary_position: binaryPosition,
      };

      if (sponsorInfo.token) {
        payload.referral_token = sponsorInfo.token;
      } else if (sponsorInfo.is_locked) {
        payload.referral_token = referralCode;
      }

      if (!sponsorInfo.is_locked && binaryParentCode.trim()) {
        payload.binary_parent_code = binaryParentCode.trim();
      }

      const res = await api.post('/auth/register', payload);

      if (res.data?.success) {
        login(res.data.data.token, res.data.data.user);
        showToast('Registration successful! Welcome to the My Status platform.', 'success');
        navigate('/dashboard');
      } else {
        showToast(res.data?.error?.message || 'Registration failed. Backend API URL returned invalid data.', 'error');
      }
    } catch (err: any) {
      showToast(err.response?.data?.error?.message || 'Registration failed. Check backend connection.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F4EC] flex flex-col justify-center py-10 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="sm:mx-auto sm:w-full sm:max-w-xl text-center mb-5">
        <div className="flex justify-center mb-2">
          <MyStatusLogo variant="full" size="md" />
        </div>
        <p className="text-xs text-[#69736F] font-medium mt-1">
          Create a new partner account in the network
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-xl px-4">
        <div className="bg-[#FFFEF9] rounded-3xl p-6 sm:p-8 shadow-wealth-card border border-[#E5E0D3]">
          {/* Sponsor card verification */}
          <div className="mb-6 p-4 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#FAF4DC] border border-[#E2C766]/60 text-[#8C6C16] flex items-center justify-center">
                <Link2 className="w-5 h-5 text-[#063B32]" />
              </div>
              <div>
                <div className="text-[10px] uppercase font-bold text-[#69736F]">Direct Sponsor</div>
                {sponsorInfo ? (
                  <div className="flex items-center gap-1.5 text-xs font-bold text-[#18211F]">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#063B32]" />
                    <span>{sponsorInfo.sponsor_name}</span>
                    <span className="text-[#8C6C16] font-mono">({sponsorInfo.referral_code})</span>
                  </div>
                ) : checkingReferral ? (
                  <div className="text-xs text-[#69736F] flex items-center gap-1">
                    <Loader2 className="w-3 h-3 animate-spin text-[#063B32]" />
                    <span>Verifying sponsor code...</span>
                  </div>
                ) : (
                  <div className="text-xs text-[#C94B4B] font-medium flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5 text-[#C94B4B]" />
                    <span>No valid sponsor code entered</span>
                  </div>
                )}
              </div>
            </div>

            <div className="text-right">
              <span className="text-[10px] text-[#69736F] font-mono">Step 1 of 2</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full Name & Mobile */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-[#18211F] mb-1">
                  Full Name
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#69736F]">
                    <UserIcon className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Ramesh Kumar"
                    required
                    className="w-full pl-9 pr-3.5 py-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] text-xs focus:outline-none focus:border-[#063B32] font-medium shadow-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#18211F] mb-1">
                  Mobile Number
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#69736F]">
                    <Phone className="w-4 h-4" />
                  </div>
                  <input
                    type="tel"
                    value={mobile}
                    onChange={(e) => setMobile(e.target.value)}
                    placeholder="e.g. 9876543210"
                    required
                    className="w-full pl-9 pr-3.5 py-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] text-xs focus:outline-none focus:border-[#063B32] font-mono shadow-xs"
                  />
                </div>
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="block text-xs font-bold text-[#18211F] mb-1">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#69736F]">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ramesh@example.com"
                  required
                  className="w-full pl-9 pr-3.5 py-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] text-xs focus:outline-none focus:border-[#063B32] font-mono shadow-xs"
                />
              </div>
            </div>

            {/* Password & Confirm */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-[#18211F] mb-1">
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
                    className="w-full pl-9 pr-3.5 py-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] text-xs focus:outline-none focus:border-[#063B32] font-mono shadow-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#18211F] mb-1">
                  Confirm Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#69736F]">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    className="w-full pl-9 pr-3.5 py-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] text-xs focus:outline-none focus:border-[#063B32] font-mono shadow-xs"
                  />
                </div>
              </div>
            </div>

            {/* Referral Code & Placement */}
            {sponsorInfo?.is_locked ? (
              <div className="space-y-3 pt-1">
                <div className="p-4 rounded-2xl bg-[#FAF4DC] border border-[#E2C766] space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-[#8C6C16]">
                      <Lock className="w-4 h-4 text-[#C9A227]" />
                      <span>PLACEMENT LOCKED</span>
                    </div>
                    <span className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full border ${binaryPosition === 'LEFT'
                        ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF]'
                        : 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766]'
                      }`}>
                      {binaryPosition} LEG (LOCKED)
                    </span>
                  </div>
                  <p className="text-xs text-[#8C6C16]">
                    Your placement is locked to the <strong>{binaryPosition} leg</strong> by the referral link.
                  </p>
                  <div className="text-[11px] text-[#69736F] font-mono pt-1 border-t border-[#E2C766]/50 flex justify-between">
                    <span>Sponsor: <strong className="text-[#18211F]">{sponsorInfo.sponsor_name}</strong></span>
                    <span>Side: <strong className="text-[#063B32]">{binaryPosition}</strong></span>
                  </div>
                </div>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                  <div>
                    <label className="block text-xs font-bold text-[#18211F] mb-1">
                      Referral Code (Sponsor)
                    </label>
                    <input
                      type="text"
                      value={referralCode}
                      onChange={handleReferralChange}
                      placeholder="e.g. SPONSOR001"
                      required
                      className="w-full px-3.5 py-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] text-xs font-mono uppercase focus:outline-none focus:border-[#063B32] shadow-xs"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-[#18211F] mb-1">
                      Preferred Binary Leg
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        type="button"
                        onClick={() => setbinaryPosition('LEFT')}
                        className={`py-2.5 rounded-2xl text-xs font-bold transition-all border cursor-pointer ${binaryPosition === 'LEFT'
                            ? 'bg-[#E0F3EE] text-[#063B32] border-[#8DCFBF] shadow-xs'
                            : 'bg-[#F7F4EC] border-[#E5E0D3] text-[#69736F] hover:bg-[#EFECE2]'
                          }`}
                      >
                        Left Leg
                      </button>
                      <button
                        type="button"
                        onClick={() => setbinaryPosition('RIGHT')}
                        className={`py-2.5 rounded-2xl text-xs font-bold transition-all border cursor-pointer ${binaryPosition === 'RIGHT'
                            ? 'bg-[#FAF4DC] text-[#8C6C16] border-[#E2C766] shadow-xs'
                            : 'bg-[#F7F4EC] border-[#E5E0D3] text-[#69736F] hover:bg-[#EFECE2]'
                          }`}
                      >
                        Right Leg
                      </button>
                    </div>
                  </div>
                </div>

                {/* Optional Specific Matching Parent code */}
                <div>
                  <label className="block text-[11px] font-medium text-[#69736F] mb-1">
                    Specific Placement Parent Code (Optional — leave blank for auto extreme leg placement)
                  </label>
                  <input
                    type="text"
                    value={binaryParentCode}
                    onChange={(e) => setbinaryParentCode(e.target.value.toUpperCase())}
                    placeholder="e.g. USR-00003 or SPONSOR001 (Optional)"
                    className="w-full px-3.5 py-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] text-xs font-mono uppercase focus:outline-none focus:border-[#063B32] shadow-xs"
                  />
                </div>
              </>
            )}

            <button
              type="submit"
              disabled={loading || !sponsorInfo}
              className="w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl bg-[#063B32] hover:bg-[#042C26] text-[#FFFEF9] border border-[#C9A227]/30 font-heading font-bold text-sm shadow-wealth-card transition-all transform hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 mt-2 cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-[#C9A227]" />
                  <span>Registering Member...</span>
                </>
              ) : (
                <>
                  <span>Complete Registration</span>
                  <ArrowRight className="w-4 h-4 text-[#C9A227]" />
                </>
              )}
            </button>
          </form>

          <div className="mt-5 text-center text-xs text-[#69736F]">
            Already have an account?{' '}
            <Link to="/login" className="text-[#063B32] hover:text-[#042C26] font-bold">
              Sign In to Partner Portal
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};


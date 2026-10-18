import React, { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useToast } from '../../context/ToastContext';
import { 
  X, 
  KeyRound, 
  Loader2, 
  Copy, 
  Check, 
  Eye, 
  EyeOff, 
  ShieldCheck, 
  Sparkles, 
  User as UserIcon,
  Phone,
  Mail,
  Award,
  AlertCircle
} from 'lucide-react';
import { User } from '../../types';

interface AdminEditUserModalProps {
  user: User | null;
  onClose: () => void;
}

export const AdminEditUserModal: React.FC<AdminEditUserModalProps> = ({ user, onClose }) => {
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [mobile, setMobile] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      setEmail(user.email || '');
      setMobile(user.mobile || '');
      setNewPassword('');
      setConfirmPassword('');
      setShowPassword(false);
      setCopiedField(null);
    }
  }, [user]);

  if (!user) return null;

  const handleCopy = (text: string, fieldName: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldName);
    showToast(`Copied ${fieldName} to clipboard`, 'info');
    setTimeout(() => {
      setCopiedField((curr) => (curr === fieldName ? null : curr));
    }, 2000);
  };

  const handleGeneratePassword = () => {
    // Generate an 8-character easy-to-read secure password: e.g. Pass@7392
    const randomDigits = Math.floor(1000 + Math.random() * 9000);
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
    const randomChar = chars.charAt(Math.floor(Math.random() * chars.length));
    const generated = `Pass@${randomChar}${randomDigits}`;
    setNewPassword(generated);
    setConfirmPassword(generated);
    setShowPassword(true);
    showToast('Generated secure temporary password!', 'success');
  };

  const handleCopyAllCredentials = () => {
    const text = `Partner Network Login Credentials\nMember Code: ${user.user_code}\nEmail: ${email.trim() || user.email}\nMobile: ${mobile.trim() || user.mobile}${newPassword ? `\nNew Password: ${newPassword}` : ''}`;
    handleCopy(text, 'Full Credentials');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!fullName.trim() || fullName.trim().length < 2) {
      showToast('Full name must be at least 2 characters.', 'error');
      return;
    }

    if (!email.trim() || !email.includes('@') || !email.includes('.')) {
      showToast('Please provide a valid email address.', 'error');
      return;
    }

    if (!mobile.trim() || mobile.trim().length < 7) {
      showToast('Please provide a valid mobile number (min 7 digits).', 'error');
      return;
    }

    if (newPassword.trim()) {
      if (newPassword.trim().length < 6) {
        showToast('New password must be at least 6 characters long.', 'error');
        return;
      }
      if (newPassword !== confirmPassword) {
        showToast('New passwords do not match.', 'error');
        return;
      }
    }

    setLoading(true);
    try {
      const payload: Record<string, string> = {};
      if (fullName.trim() !== user.full_name) payload.full_name = fullName.trim();
      if (email.trim().toLowerCase() !== user.email.toLowerCase()) payload.email = email.trim().toLowerCase();
      if (mobile.trim() !== user.mobile) payload.mobile = mobile.trim();
      if (newPassword.trim()) payload.new_password = newPassword.trim();

      if (Object.keys(payload).length === 0) {
        showToast('No changes were made.', 'info');
        onClose();
        return;
      }

      const res = await api.put(`/admin/users/${user.id}/credentials`, payload);

      if (res.data?.success) {
        showToast(res.data.message || 'User credentials updated successfully.', 'success');
        queryClient.invalidateQueries({ queryKey: ['adminUsers'] });
        queryClient.invalidateQueries({ queryKey: ['adminDashboard'] });
        onClose();
      }
    } catch (err: any) {
      showToast(err.response?.data?.error?.message || 'Failed to update user credentials.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
      <div 
        className="w-full max-w-lg rounded-3xl bg-[#FFFEF9] border border-[#E5E0D3] shadow-wealth-elevated p-6 relative overflow-hidden text-[#18211F] max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-[#69736F] hover:text-[#18211F] hover:bg-[#EFECE2] transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 text-[#8C6C16] text-xs font-mono font-bold uppercase tracking-wider mb-1.5">
          <KeyRound className="w-4 h-4 text-[#C9A227]" />
          <span>Credential Management</span>
        </div>

        <h2 className="text-xl font-heading font-extrabold text-[#18211F] mb-1 tracking-tight">
          Edit User Credentials
        </h2>
        <p className="text-xs text-[#69736F] mb-4">
          Update account details, contact info, or reset password for <span className="text-[#063B32] font-bold">{user.full_name}</span>.
        </p>

        {/* User Identity Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 p-3.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-xs font-mono mb-5">
          <div>
            <div className="text-[10px] text-[#69736F] uppercase">User Code</div>
            <div className="flex items-center gap-1 font-bold text-[#063B32] mt-0.5">
              <span>{user.user_code}</span>
              <button
                type="button"
                onClick={() => handleCopy(user.user_code, 'User Code')}
                className="text-[#69736F] hover:text-[#063B32] cursor-pointer"
                title="Copy User Code"
              >
                {copiedField === 'User Code' ? <Check className="w-3 h-3 text-[#063B32]" /> : <Copy className="w-3 h-3" />}
              </button>
            </div>
          </div>

          <div>
            <div className="text-[10px] text-[#69736F] uppercase">Referral Code</div>
            <div className="flex items-center gap-1 font-bold text-[#8C6C16] mt-0.5">
              <span>{user.referral_code}</span>
              <button
                type="button"
                onClick={() => handleCopy(user.referral_code, 'Referral Code')}
                className="text-[#69736F] hover:text-[#063B32] cursor-pointer"
                title="Copy Referral Code"
              >
                {copiedField === 'Referral Code' ? <Check className="w-3 h-3 text-[#063B32]" /> : <Copy className="w-3 h-3" />}
              </button>
            </div>
          </div>

          <div>
            <div className="text-[10px] text-[#69736F] uppercase">Rank & Role</div>
            <div className="flex items-center gap-1 font-semibold text-[#18211F] mt-0.5">
              <Award className="w-3 h-3 text-[#C9A227]" />
              <span className="truncate">{user.current_rank || 'DISTRIBUTOR'}</span>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Full Name */}
          <div>
            <label className="block text-xs font-bold text-[#18211F] mb-1.5 flex items-center gap-1.5">
              <UserIcon className="w-3.5 h-3.5 text-[#063B32]" />
              <span>Full Name</span>
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              className="w-full px-3.5 py-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] text-xs font-medium focus:outline-none focus:border-[#063B32]"
              placeholder="e.g. Ramesh Kumar"
            />
          </div>

          {/* Email Address */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-bold text-[#18211F] flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5 text-[#063B32]" />
                <span>Email Address</span>
              </label>
              <button
                type="button"
                onClick={() => handleCopy(email, 'Email')}
                className="text-[10px] font-mono font-semibold text-[#69736F] hover:text-[#063B32] inline-flex items-center gap-1 cursor-pointer"
              >
                {copiedField === 'Email' ? <Check className="w-3 h-3 text-[#063B32]" /> : <Copy className="w-3 h-3" />}
                <span>Copy</span>
              </button>
            </div>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3.5 py-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] text-xs font-mono focus:outline-none focus:border-[#063B32]"
              placeholder="user@example.com"
            />
          </div>

          {/* Mobile Number */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-bold text-[#18211F] flex items-center gap-1.5">
                <Phone className="w-3.5 h-3.5 text-[#063B32]" />
                <span>Mobile Number</span>
              </label>
              <button
                type="button"
                onClick={() => handleCopy(mobile, 'Mobile')}
                className="text-[10px] font-mono font-semibold text-[#69736F] hover:text-[#063B32] inline-flex items-center gap-1 cursor-pointer"
              >
                {copiedField === 'Mobile' ? <Check className="w-3 h-3 text-[#063B32]" /> : <Copy className="w-3 h-3" />}
                <span>Copy</span>
              </button>
            </div>
            <input
              type="tel"
              value={mobile}
              onChange={(e) => setMobile(e.target.value)}
              required
              className="w-full px-3.5 py-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#18211F] text-xs font-mono focus:outline-none focus:border-[#063B32]"
              placeholder="e.g. 9876543210"
            />
          </div>

          {/* Password Reset Section */}
          <div className="p-4 rounded-2xl bg-[#FAF8F2] border border-[#E5E0D3] space-y-3 pt-3.5 mt-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-xs font-heading font-extrabold text-[#18211F]">
                <KeyRound className="w-3.5 h-3.5 text-[#C9A227]" />
                <span>Reset Login Password</span>
              </div>
              <button
                type="button"
                onClick={handleGeneratePassword}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-[#FFFEF9] border border-[#E5E0D3] text-[10px] font-heading font-bold text-[#063B32] hover:bg-[#E0F3EE] transition-all cursor-pointer shadow-xs"
              >
                <Sparkles className="w-3 h-3 text-[#C9A227]" />
                <span>Generate Password</span>
              </button>
            </div>

            <p className="text-[11px] text-[#69736F] leading-relaxed">
              Leave blank to keep existing password unchanged. Entering a password resets it immediately with secure bcrypt encryption.
            </p>

            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password (min 6 characters)"
                className="w-full px-3.5 py-2.5 pr-10 rounded-xl bg-[#FFFEF9] border border-[#E5E0D3] text-[#18211F] text-xs font-mono focus:outline-none focus:border-[#063B32]"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#69736F] hover:text-[#18211F] cursor-pointer"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            {newPassword && (
              <div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm new password"
                  className={`w-full px-3.5 py-2.5 rounded-xl bg-[#FFFEF9] border text-[#18211F] text-xs font-mono focus:outline-none ${
                    confirmPassword && confirmPassword !== newPassword
                      ? 'border-red-400 focus:border-red-500'
                      : 'border-[#E5E0D3] focus:border-[#063B32]'
                  }`}
                />
                {confirmPassword && confirmPassword !== newPassword && (
                  <p className="text-[10px] text-red-500 mt-1 flex items-center gap-1 font-sans">
                    <AlertCircle className="w-3 h-3" />
                    <span>Passwords do not match</span>
                  </p>
                )}
              </div>
            )}

            {newPassword && (
              <div className="flex justify-end pt-1">
                <button
                  type="button"
                  onClick={handleCopyAllCredentials}
                  className="inline-flex items-center gap-1.5 text-[11px] font-heading font-bold text-[#063B32] hover:text-[#04241F] cursor-pointer"
                >
                  {copiedField === 'Full Credentials' ? <Check className="w-3.5 h-3.5 text-[#063B32]" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>Copy Login Message (for WhatsApp / SMS)</span>
                </button>
              </div>
            )}
          </div>

          <div className="flex items-center justify-end gap-2.5 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2.5 rounded-2xl bg-[#F7F4EC] border border-[#E5E0D3] text-[#69736F] hover:text-[#18211F] hover:bg-[#EFECE2] text-xs font-heading font-bold transition-all cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || (!!newPassword && newPassword !== confirmPassword)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-2xl bg-[#063B32] hover:bg-[#04241F] text-[#FFFEF9] text-xs font-heading font-bold shadow-wealth-button hover:shadow-wealth-button-hover transition-all disabled:opacity-50 cursor-pointer"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin text-[#C9A227]" />}
              <span>Save Credential Changes</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export interface User {
  id: number;
  user_code: string;
  email: string;
  mobile: string;
  full_name: string;
  role: 'USER' | 'ADMIN';
  referral_code: string;
  sponsor_id: number | null;
  sponsor_name: string | null;
  sponsor_code: string | null;
  binary_parent_id: number | null;
  binary_parent_name: string | null;
  binary_parent_code: string | null;
  binary_position: 'LEFT' | 'RIGHT' | null;
  is_active: boolean;
  created_at: string;
  wallet_balance?: number;
  total_earned?: number;
  total_withdrawn?: number;
  personal_bv?: number;
  left_bv?: number;
  right_bv?: number;
  carry_left_bv?: number;
  carry_right_bv?: number;
  matched_bv?: number;
  direct_referrals_count?: number;
}

export interface Package {
  id: number;
  name: string;
  description: string;
  price: number;
  product_value: number;
  gst_amount: number;
  bv: number;
  is_active: boolean;
  created_at: string;
}

export interface Purchase {
  id: number;
  purchase_code: string;
  user_id: number;
  user_name?: string;
  user_code?: string;
  package_id: number;
  package_name?: string;
  amount: number;
  product_value: number;
  gst_amount: number;
  bv: number;
  status: string;
  created_at: string;
}

export interface Wallet {
  id: number;
  user_id: number;
  balance: number;
  total_earned: number;
  total_withdrawn: number;
  updated_at: string;
}

export interface WalletTransaction {
  id: number;
  transaction_code: string;
  wallet_id: number;
  user_id: number;
  type: 'CREDIT' | 'DEBIT' | 'ADJUSTMENT';
  category: 'DIRECT_REFERRAL' | 'BINARY_MATCHING' | 'WITHDRAWAL' | 'ADMIN_ADJUSTMENT' | 'PURCHASE';
  amount: number;
  balance_after: number;
  description: string;
  reference_id?: string;
  created_at: string;
}

export interface Commission {
  id: number;
  commission_code: string;
  beneficiary_id: number;
  beneficiary_name: string;
  source_user_id: number;
  source_user_name: string;
  source_user_code: string;
  purchase_id: number;
  purchase_code: string;
  commission_type: 'DIRECT_REFERRAL' | 'BINARY_MATCHING';
  amount: number;
  bv_amount: number;
  percentage: number;
  calculation_details: Record<string, any>;
  created_at: string;
}

export interface Withdrawal {
  id: number;
  withdrawal_code: string;
  user_id: number;
  user_name?: string;
  user_code?: string;
  amount: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  payout_method: string;
  payout_details: Record<string, any>;
  admin_notes?: string;
  approved_by?: number;
  approver_name?: string;
  processed_at?: string;
  created_at: string;
}

export interface BinaryTreeNode {
  id: number;
  user_code: string;
  full_name: string;
  email: string;
  mobile: string;
  role: string;
  is_active: boolean;
  referral_code: string;
  sponsor_id: number | null;
  sponsor_name: string | null;
  sponsor_code: string | null;
  binary_parent_id: number | null;
  binary_parent_name: string | null;
  binary_parent_code: string | null;
  binary_position: 'LEFT' | 'RIGHT' | null;
  personal_bv: number;
  left_bv: number;
  right_bv: number;
  carry_left_bv: number;
  carry_right_bv: number;
  matched_bv: number;
  direct_referrals_count: number;
  active_package_name?: string | null;
  active_package_price?: number;
  created_at: string;
  left?: BinaryTreeNode | null;
  right?: BinaryTreeNode | null;
}

export interface DashboardData {
  user: User;
  kpis: {
    wallet_balance: number;
    total_earnings: number;
    total_withdrawn: number;
    personal_bv: number;
    left_bv: number;
    right_bv: number;
    carry_left_bv: number;
    carry_right_bv: number;
    matched_bv: number;
    total_bv: number;
    direct_referrals: number;
    network_members: number;
    is_active: boolean;
    active_package_name: string | null;
    active_package_amount: number;
  };
  sponsor: {
    name: string | null;
    code: string | null;
    email: string | null;
  };
  placement: {
    parent_name: string | null;
    parent_code: string | null;
    position: string | null;
  };
  recent_transactions: WalletTransaction[];
  recent_commissions: Commission[];
}

export interface AdminDashboardData {
  kpis: {
    total_users: number;
    active_users: number;
    inactive_users: number;
    total_virtual_sales: number;
    total_bv: number;
    total_commissions: number;
    direct_commissions: number;
    matching_commissions: number;
    total_withdrawn: number;
    pending_withdrawals_count: number;
    pending_withdrawals_amount: number;
  };
  recent_logs: any[];
  recent_purchases: Purchase[];
}

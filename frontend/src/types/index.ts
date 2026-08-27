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

export interface SlotInfo {
  mode: 'REAL' | 'DEMO';
  timezone: string;
  current_time: string;
  date: string;
  time_formatted: string;
  slot_id: string;
  slot_number: number;
  slot_name: string;
  slot_start: string;
  slot_end: string;
  slot_start_formatted: string;
  slot_end_formatted: string;
  remaining_seconds: number;
  remaining_formatted: string;
  next_slot_id: string;
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
  slot_id?: string;
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
  transaction_code?: string;
  wallet_id: number;
  user_id: number;
  transaction_type?: 'CREDIT' | 'DEBIT' | 'ADMIN_ADJUSTMENT';
  type?: 'CREDIT' | 'DEBIT' | 'ADJUSTMENT';
  category: 'DIRECT_REFERRAL' | 'DIRECT_COMMISSION' | 'BINARY_MATCHING' | 'MATCHING_COMMISSION' | 'PAIR_BONUS' | 'CARRY_COMMISSION' | 'WITHDRAWAL' | 'ADMIN_ADJUSTMENT' | 'PURCHASE';
  amount: number;
  balance_before?: number;
  balance_after: number;
  description: string;
  slot_id?: string;
  reference_id?: string;
  created_at: string;
}

export interface Commission {
  id: number;
  commission_code?: string;
  beneficiary_id: number;
  beneficiary_name?: string;
  source_user_id: number;
  source_user_name: string;
  source_user_code: string;
  purchase_id: number;
  purchase_code?: string;
  commission_type: 'DIRECT_REFERRAL' | 'DIRECT_COMMISSION' | 'BINARY_MATCHING' | 'MATCHING_COMMISSION' | 'PAIR_BONUS' | 'CARRY_COMMISSION';
  slot_id?: string;
  amount: number;
  bv_amount: number;
  bv_basis?: number;
  percentage?: number;
  calculation_details?: Record<string, any>;
  created_at: string;
}

export interface VolumeLedgerEntry {
  id: number;
  source_user_id: number;
  source_user_name?: string;
  source_user_code?: string;
  ancestor_user_id: number;
  ancestor_user_name?: string;
  ancestor_user_code?: string;
  side: 'LEFT' | 'RIGHT';
  purchase_id?: number;
  source_reference?: string;
  slot_id: string;
  amount: number;
  consumed_amount: number;
  remaining_amount: number;
  status: 'ACTIVE' | 'CONSUMED';
  created_at: string;
}

export interface SlotSettlement {
  id: number;
  user_id: number;
  user_name?: string;
  user_code?: string;
  slot_id: string;
  left_before: number;
  right_before: number;
  left_matched: number;
  right_matched: number;
  pairs_paid: number;
  pair_bonus: number;
  left_carry: number;
  right_carry: number;
  carry_commission: number;
  matching_commission: number;
  status: 'SETTLED' | 'FINALIZED';
  processed_at: string;
  created_at: string;
}

export interface PairSummary {
  pair_volume_threshold: number;
  pair_bonus_amount: number;
  max_pairs_per_period?: number;
  slot_id: string;
  current_left_bv: number;
  current_right_bv: number;
  carry_forward_left: number;
  carry_forward_right: number;
  effective_left_bv: number;
  effective_right_bv: number;
  consumed_left_bv: number;
  consumed_right_bv: number;
  ending_carry_left: number;
  ending_carry_right: number;
  pair_completed: boolean;
  pair_bonus_earned: number;
  matching_commission_earned?: number;
  carry_commission_earned?: number;
  needed_left_bv: number;
  needed_right_bv: number;
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

export type NetworkViewMode = 'network' | 'active_slot' | 'history';

export interface BinaryTreeNode {
  id: number;
  user_code: string;
  full_name: string;
  email: string;
  mobile?: string;
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
  accumulated_left_bv?: number;
  accumulated_right_bv?: number;
  left_bv?: number;
  right_bv?: number;
  carry_left_bv: number;
  carry_right_bv: number;
  matched_bv: number;
  direct_referrals?: number;
  direct_referrals_count?: number;
  active_package?: string;
  active_package_name?: string | null;
  active_package_price?: number;
  created_at?: string;
  
  // Active Slot metrics
  slot_id?: string;
  view_mode?: string;
  current_left_bv?: number;
  current_right_bv?: number;
  starting_carry_left?: number;
  starting_carry_right?: number;
  effective_left_bv?: number;
  effective_right_bv?: number;
  ending_carry_left?: number;
  ending_carry_right?: number;
  pair_completed?: boolean;
  pair_bonus?: number;
  has_active_slot_volume?: boolean;

  left?: BinaryTreeNode | null;
  right?: BinaryTreeNode | null;
}

export interface DashboardData {
  user: User;
  kpis: {
    wallet_balance: number;
    total_earnings: number;
    total_withdrawn: number;
    direct_commissions?: number;
    pair_commissions?: number;
    matching_commissions?: number;
    carry_commissions?: number;
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
    slot_earnings?: number;
    slot_direct_commissions?: number;
    slot_pair_commissions?: number;
    slot_matching_commissions?: number;
    slot_carry_commissions?: number;
    slot_commissions_count?: number;
    current_slot_id?: string;
    pair_summary?: PairSummary;
  };
  pair_summary?: PairSummary;
  slot_info?: SlotInfo;
  sponsor?: {
    name: string | null;
    code: string | null;
    email: string | null;
  };
  placement?: {
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
    pair_commissions?: number;
    carry_commissions?: number;
    total_withdrawn: number;
    pending_withdrawals_count: number;
    pending_withdrawals_amount: number;
    current_slot_id?: string;
    current_slot_name?: string;
    slot_virtual_sales?: number;
    slot_bv?: number;
    slot_commissions?: number;
    slot_purchases_count?: number;
  };
  slot_info?: SlotInfo;
  recent_logs: any[];
  recent_purchases?: Purchase[];
}

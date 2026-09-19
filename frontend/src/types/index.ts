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
  current_rank?: string;
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

export interface MatchingTreeNode {
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
  activated_at?: string;
  current_rank?: string;
  earning_status?: string;

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

  left?: MatchingTreeNode | null;
  right?: MatchingTreeNode | null;
}

export interface CarryLegSummary {
  bv?: number;
  count?: number;
  carry_count?: number;
  paid_count?: number;
  unpaid_count?: number;
  paid_members?: number;
  unpaid_members?: number;
  total_members?: number;
  total?: number;
  paid?: number;
  unpaid?: number;
  carry?: number;
  total_pairs?: number;
  paid_pairs?: number;
  unpaid_pairs?: number;
}

export interface CarryPairLegSummary {
  total_pairs: number;
  paid_pairs: number;
  unpaid_pairs: number;
}

export interface CarryPairSummary {
  left: CarryPairLegSummary;
  right: CarryPairLegSummary;
}

export interface CarrySummary {
  left: CarryLegSummary;
  right: CarryLegSummary;
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
    carry?: CarrySummary;
    carry_summary?: CarrySummary;
    carry_pair_summary?: CarryPairSummary;
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
  carry?: CarrySummary;
  carry_summary?: CarrySummary;
  carry_pair_summary?: CarryPairSummary;
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
    total_packages_activated?: number;
    total_bv: number;
    total_left_bv?: number;
    total_right_bv?: number;
    total_left_carry?: number;
    total_right_carry?: number;
    total_commissions: number;
    direct_commissions: number;
    matching_commissions: number;
    pair_commissions?: number;
    carry_commissions?: number;
    total_wallet_balance?: number;
    total_withdrawn: number;
    pending_withdrawals_count: number;
    pending_withdrawals_amount: number;
    approved_withdrawals_count?: number;
    rejected_withdrawals_count?: number;
    pending_activations_count?: number;
    verified_activations_count?: number;
    total_pins_count?: number;
    available_pins_count?: number;
    used_pins_count?: number;
    expired_pins_count?: number;
    issued_pins_count?: number;
    total_activated_count?: number;
    pending_pin_orders_count?: number;
    completed_pin_orders_count?: number;
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
  recent_users?: any[];
  recent_activations?: any[];
  recent_transactions?: any[];
}

export interface ReferralLinkItem {
  token: string;
  placement_side: 'LEFT' | 'RIGHT';
  sponsor_name: string;
  sponsor_code: string;
  referral_code: string;
}

export interface ReferralLinksData {
  left: ReferralLinkItem;
  right: ReferralLinkItem;
}

export interface ReferralValidationData {
  valid: boolean;
  sponsor_name: string;
  sponsor_code: string;
  referral_code: string;
  placement_side: 'LEFT' | 'RIGHT' | null;
  is_locked: boolean;
  token?: string | null;
  is_active?: boolean;
}

export type ActivationStatus =
  | 'PAYMENT_PENDING'
  | 'PAYMENT_SUBMITTED'
  | 'UNDER_REVIEW'
  | 'PAYMENT_VERIFIED'
  | 'PIN_ISSUED'
  | 'ACTIVATED'
  | 'REJECTED'
  | 'CANCELLED';

export interface PackageActivationRequest {
  id: number;
  request_code: string;
  user_id: number;
  user_name?: string;
  user_code?: string;
  user_email?: string;
  sponsor_name?: string;
  sponsor_code?: string;
  binary_parent_name?: string;
  binary_parent_code?: string;
  binary_position?: 'LEFT' | 'RIGHT' | null;
  package_id: number;
  package_name?: string;
  package_amount: number;
  package_bv: number;
  payment_method: string;
  payment_reference?: string;
  payment_recipient_id?: number;
  payment_recipient_name?: string;
  payment_proof_url?: string;
  status: ActivationStatus;
  admin_notes?: string;
  rejection_reason?: string;
  requested_at: string;
  verified_at?: string;
  verified_by_name?: string;
  security_pin_id?: number;
  pin_status?: string;
  pin_code?: string;
  activated_at?: string;
  purchase_id?: number;
}

export interface SecurityPin {
  id: number;
  pin_code?: string;
  masked_code?: string;
  user_id: number;
  owner_user_id?: number;
  owner_user_name?: string;
  owner_user_code?: string;
  owner_name?: string;
  owner_code?: string;
  original_owner_user_id?: number;
  original_owner_name?: string;
  original_owner_code?: string;
  order_id?: number;
  package_id: number;
  package_name?: string;
  activation_request_id?: number;
  amount: number;
  bv: number;
  status: 'AVAILABLE' | 'ISSUED' | 'TRANSFERRED' | 'USED' | 'EXPIRED' | 'REVOKED';
  created_at: string;
  issued_at?: string;
  transferred_at?: string;
  used_at?: string;
  expires_at?: string;
  created_by_admin_id?: number;
  created_by_admin_name?: string;
  payment_reference?: string;
  attempt_count: number;
  max_attempts: number;
  revocation_reason?: string;
  raw_security_pin?: string;
}

export interface SecurityPinOrder {
  id: number;
  order_code: string;
  user_id: number;
  user_name?: string;
  user_code?: string;
  user_email?: string;
  buyer_name?: string;
  buyer_code?: string;
  buyer_email?: string;
  package_id: number;
  package_name?: string;
  quantity: number;
  price_per_pin: number;
  unit_price?: number;
  total_amount: number;
  bv_per_pin: number;
  payment_method: string;
  payment_reference?: string;
  payment_proof_url?: string;
  status: 'PAYMENT_PENDING' | 'PAYMENT_SUBMITTED' | 'UNDER_REVIEW' | 'PAYMENT_VERIFIED' | 'COMPLETED' | 'REJECTED' | 'CANCELLED';
  admin_notes?: string;
  rejection_reason?: string;
  created_at: string;
  verified_at?: string;
  verified_by_name?: string;
  completed_at?: string;
  generated_pins_count?: number;
}

export interface SecurityPinTransfer {
  id: number;
  pin_id: number;
  pin_code?: string;
  from_user_id: number;
  from_user_name?: string;
  from_user_code?: string;
  to_user_id: number;
  to_user_name?: string;
  to_user_code?: string;
  transfer_reason?: string;
  notes?: string;
  transferred_at: string;
  status: string;
}

export interface SecurityPinUplineRequest {
  id: number;
  request_code: string;
  requester_user_id: number;
  requester_user_name?: string;
  requester_user_code?: string;
  upline_user_id: number;
  upline_user_name?: string;
  upline_user_code?: string;
  package_id: number;
  package_name?: string;
  quantity: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED';
  notes?: string;
  rejection_reason?: string;
  transferred_pin_id?: number;
  created_at: string;
  responded_at?: string;
}

export interface SecurityPinLedgerEntry {
  id: number;
  pin_id: number;
  pin_code?: string;
  user_id: number;
  user_name?: string;
  user_code?: string;
  action: string;
  reference_id?: string;
  from_user_id?: number;
  from_user_name?: string;
  to_user_id?: number;
  to_user_name?: string;
  actor_id?: number;
  actor_name?: string;
  notes?: string;
  timestamp: string;
}

export type SecurityPinLedgerItem = SecurityPinLedgerEntry;

export interface PinWalletData {
  wallet: {
    available: number;
    used: number;
    transferred: number;
    received: number;
    expired: number;
    total_purchased: number;
    pending_downline_requests: number;
  };
  available_pins: SecurityPin[];
  user: {
    id: number;
    user_code: string;
    full_name: string;
    is_active: boolean;
  };
}

export interface EligibleDownlineUser {
  id: number;
  user_code: string;
  full_name: string;
  email: string;
  is_active: boolean;
  binary_position?: string;
  sponsor_id?: number;
}

export interface ActivationStatusResponse {
  is_active: boolean;
  package: Package;
  activation_request: PackageActivationRequest | null;
  payment_recipient: {
    id: number | null;
    full_name: string;
    user_code: string;
    role: string;
    relationship: string;
  };
  upi_details?: {
    upi_id: string;
    payee_name: string;
    amount: number;
    qr_image_url?: string;
  };
  can_activate_with_pin: boolean;
}

export interface RankConfig {
  id: number;
  rank_name: 'STAR' | 'SUPER_STAR' | 'VIP';
  display_name: string;
  level: number;
  required_directs: number;
  qualification_days: number;
  reward_type: 'CASH' | 'EV_SCOOTER';
  reward_amount: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface RankAchievement {
  id: number;
  user_id: number;
  user_name?: string;
  user_code?: string;
  rank_name: 'STAR' | 'SUPER_STAR' | 'VIP';
  status: 'IN_PROGRESS' | 'ACHIEVED' | 'EXPIRED';
  qualification_started_at: string;
  qualification_deadline: string;
  achieved_at?: string | null;
  reward_type: 'CASH' | 'EV_SCOOTER';
  reward_amount: number;
  reward_status: 'PENDING' | 'CREDITED' | 'PENDING_FULFILLMENT' | 'FULFILLED' | 'REJECTED' | 'EXPIRED';
  reward_transaction_id?: number | null;
  qualifying_direct_ids?: string | null;
  admin_notes?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface QualifyingMember {
  id: number;
  full_name: string;
  user_code: string;
  current_rank?: string;
  created_at?: string;
}

export interface RankTierProgress {
  rank_name: 'STAR' | 'SUPER_STAR' | 'VIP';
  display_name: string;
  level: number;
  required_directs: number;
  qualification_days: number;
  reward_type: 'CASH' | 'EV_SCOOTER';
  reward_amount: number;
  status: 'ACHIEVED' | 'IN_PROGRESS' | 'LOCKED' | 'EXPIRED';
  current_count: number;
  progress_percentage: number;
  qualification_started_at: string | null;
  qualification_deadline: string | null;
  achieved_at: string | null;
  remaining_seconds: number;
  is_expired: boolean;
  reward_status: 'PENDING' | 'CREDITED' | 'PENDING_FULFILLMENT' | 'FULFILLED' | 'REJECTED' | 'EXPIRED';
  qualifying_members: QualifyingMember[];
}

export interface RankOverviewResponse {
  user_id: number;
  full_name: string;
  user_code: string;
  current_rank: string;
  server_time: string;
  tiers: RankTierProgress[];
}

export interface EarningCycle {
  id: number;
  user_id: number;
  user_name?: string | null;
  user_code?: string | null;
  package_id?: number | null;
  package_name?: string | null;
  cycle_number: number;
  direct_income: number;
  pairing_income: number;
  total_eligible_income: number;
  earning_cap: number;
  remaining_capacity: number;
  progress_percentage: number;
  status: 'ACTIVE' | 'RETOPUP_REQUIRED' | 'COMPLETED';
  started_at: string | null;
  capped_at?: string | null;
  reset_at?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface EarningCapOverviewResponse {
  user_id: number;
  user_name: string | null;
  user_code: string | null;
  earning_status: 'ACTIVE' | 'RETOPUP_REQUIRED';
  current_cycle: EarningCycle;
  cycle_number: number;
  direct_income: number;
  pairing_income: number;
  total_eligible_income: number;
  earning_cap: number;
  remaining_capacity: number;
  progress_percentage: number;
  status: 'ACTIVE' | 'RETOPUP_REQUIRED' | 'COMPLETED';
  is_retopup_required: boolean;
  started_at: string | null;
  capped_at: string | null;
  lifetime_eligible_income: number;
  lifetime_blocked_amount: number;
  completed_cycles_count: number;
  retopup_message?: string | null;
}

export interface AdminEarningCapSummary {
  total_active_cycles: number;
  total_retopup_required: number;
  total_near_cap: number;
  cap_limit: number;
}

export interface AdminEarningCapListResponse {
  items: EarningCycle[];
  total: number;
  limit: number;
  offset: number;
  summary: AdminEarningCapSummary;
}

export interface DailyRewardCycle {
  id: number;
  purchase_id: number;
  purchase_code?: string | null;
  user_id: number;
  user_name?: string | null;
  user_code?: string | null;
  package_id: number;
  package_name?: string | null;
  refund_target: number;
  refunded_amount: number;
  remaining_refund: number;
  completed_pairs: number;
  base_daily_amount: number;
  pair_increment: number;
  current_daily_reward: number;
  progress_percentage: number;
  status: 'ACTIVE' | 'COMPLETED';
  last_credit_date?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface DailyRewardTransaction {
  id: number;
  cycle_id: number;
  purchase_id: number;
  user_id: number;
  business_date: string;
  amount: number;
  completed_pairs_snapshot: number;
  daily_reward_snapshot: number;
  wallet_transaction_id?: number | null;
  idempotency_key: string;
  description: string;
  created_at?: string | null;
}

export interface DailyRewardOverviewResponse {
  has_active_cycle: boolean;
  cycle: DailyRewardCycle | null;
  completed_pairs: number;
  current_daily_reward: number;
  total_refunded: number;
  next_credit_time: string;
  next_credit_time_formatted: string;
  recent_transactions: DailyRewardTransaction[];
}

export interface AdminDailyRewardSummary {
  total_cycles: number;
  active_cycles: number;
  completed_cycles: number;
  total_refunded_all_time: number;
  today_credited_amount: number;
  today_business_date: string;
}

export interface AdminDailyRewardListResponse {
  items: DailyRewardCycle[];
  total_count: number;
  limit: number;
  offset: number;
  summary: AdminDailyRewardSummary;
}



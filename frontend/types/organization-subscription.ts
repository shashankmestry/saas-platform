export type OrganizationSubscription = {
  plan: string;
  status: string;
  provider: string;
  billing_interval: string;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
};

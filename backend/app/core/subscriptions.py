"""Provider-independent subscription enums.

Commercial subscription state is stored in ``organization_subscriptions``.
Application entitlements continue to use ``OrganizationPlan`` / ``app.core.plans``.
"""

from enum import StrEnum


class SubscriptionStatus(StrEnum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"
    INCOMPLETE = "incomplete"


class BillingInterval(StrEnum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionProvider(StrEnum):
    NONE = "none"
    STRIPE = "stripe"
    PADDLE = "paddle"
    RAZORPAY = "razorpay"

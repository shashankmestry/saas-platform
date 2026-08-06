"""Code-defined SaaS plans, features, limits, and entitlements.

Plan definitions live in application code (same philosophy as RBAC).
Only organization plan *assignment* is persisted in the database.

Limit semantics:
- An integer value is a hard cap.
- ``None`` means unlimited (never use magic numbers like -1 or 999999).
"""

from dataclasses import dataclass
from enum import StrEnum


class PlanKey(StrEnum):
    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class Feature(StrEnum):
    ANALYTICS_BASIC = "analytics.basic"
    ANALYTICS_ADVANCED = "analytics.advanced"
    SUPPORT_PRIORITY = "support.priority"


class Limit(StrEnum):
    ORGANIZATION_MEMBERS = "organization.members"


@dataclass(frozen=True, slots=True)
class PlanEntitlements:
    """Resolved entitlements for a single plan.

    ``limits`` values use ``None`` to mean unlimited.
    """

    features: dict[Feature, bool]
    limits: dict[Limit, int | None]


PLAN_DEFINITIONS: dict[PlanKey, PlanEntitlements] = {
    PlanKey.FREE: PlanEntitlements(
        features={
            Feature.ANALYTICS_BASIC: True,
            Feature.ANALYTICS_ADVANCED: False,
            Feature.SUPPORT_PRIORITY: False,
        },
        limits={
            Limit.ORGANIZATION_MEMBERS: 3,
        },
    ),
    PlanKey.STANDARD: PlanEntitlements(
        features={
            Feature.ANALYTICS_BASIC: True,
            Feature.ANALYTICS_ADVANCED: False,
            Feature.SUPPORT_PRIORITY: True,
        },
        limits={
            Limit.ORGANIZATION_MEMBERS: 10,
        },
    ),
    PlanKey.PREMIUM: PlanEntitlements(
        features={
            Feature.ANALYTICS_BASIC: True,
            Feature.ANALYTICS_ADVANCED: True,
            Feature.SUPPORT_PRIORITY: True,
        },
        limits={
            Limit.ORGANIZATION_MEMBERS: 50,
        },
    ),
    PlanKey.ENTERPRISE: PlanEntitlements(
        features={
            Feature.ANALYTICS_BASIC: True,
            Feature.ANALYTICS_ADVANCED: True,
            Feature.SUPPORT_PRIORITY: True,
        },
        limits={
            # None means unlimited.
            Limit.ORGANIZATION_MEMBERS: None,
        },
    ),
}


def parse_plan_key(value: str) -> PlanKey:
    """Parse a stored plan_key string into PlanKey."""
    try:
        return PlanKey(value)
    except ValueError as exc:
        raise ValueError(f"Unknown organization plan: {value}") from exc


def entitlements_for_plan(plan: PlanKey) -> PlanEntitlements:
    definition = PLAN_DEFINITIONS.get(plan)
    if definition is None:
        raise ValueError(f"No entitlements defined for plan: {plan}")
    return definition


def plan_has_feature(plan: PlanKey, feature: Feature) -> bool:
    return bool(entitlements_for_plan(plan).features.get(feature, False))


def plan_get_limit(plan: PlanKey, limit: Limit) -> int | None:
    """Return the numeric limit, or None when unlimited."""
    entitlements = entitlements_for_plan(plan)
    if limit not in entitlements.limits:
        raise ValueError(f"Limit {limit} is not defined for plan {plan}")
    return entitlements.limits[limit]

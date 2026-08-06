class PlanError(Exception):
    """Base exception for the plans module."""


class OrganizationPlanNotFoundError(PlanError):
    """Raised when an organization has no persisted plan assignment."""


class UnknownOrganizationPlanError(PlanError):
    """Raised when a persisted plan_key is not a known PlanKey."""

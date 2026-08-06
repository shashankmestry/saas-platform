from pydantic import BaseModel, Field


class OrganizationPlanResponse(BaseModel):
    """Effective plan and entitlements for an organization.

    Limit values use ``null`` to mean unlimited.
    """

    plan: str
    features: dict[str, bool]
    limits: dict[str, int | None]
    usage: dict[str, int] = Field(
        default_factory=dict,
        description="Current usage counters for numeric limits (e.g. seat usage).",
    )

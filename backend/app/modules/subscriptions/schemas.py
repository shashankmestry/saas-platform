from datetime import datetime

from pydantic import BaseModel


class OrganizationSubscriptionResponse(BaseModel):
    """Public subscription view. Provider IDs are intentionally omitted."""

    plan: str
    status: str
    provider: str
    billing_interval: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool

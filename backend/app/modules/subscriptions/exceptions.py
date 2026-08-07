class SubscriptionError(Exception):
    """Base exception for the subscriptions module."""


class OrganizationSubscriptionNotFoundError(SubscriptionError):
    """Raised when an organization has no subscription row."""


class InvalidSubscriptionStateError(SubscriptionError):
    """Raised when a subscription transition is not valid."""

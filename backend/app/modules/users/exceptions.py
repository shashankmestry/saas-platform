class UserError(Exception):
    """Base exception for the users module."""


class UserNotFoundError(UserError):
    """Raised when a platform user cannot be found."""


class UserInactiveError(UserError):
    """Raised when a platform user exists but is inactive."""

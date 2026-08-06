class OrganizationError(Exception):
    """Base exception for the organizations module."""


class OrganizationSlugConflictError(OrganizationError):
    """Raised when a unique organization slug cannot be generated."""


class LogoValidationError(OrganizationError):
    """Raised when logo upload metadata or confirmation is invalid."""


class LogoObjectMissingError(OrganizationError):
    """Raised when a confirmed Storage object does not exist."""


class LogoStorageOperationError(OrganizationError):
    """Raised when a Storage operation required for logos fails."""

class MembershipError(Exception):
    """Base exception for the memberships module."""


class AlreadyOrganizationMemberError(MembershipError):
    """Raised when the invitee is already a member of the organization."""


class PendingInvitationExistsError(MembershipError):
    """Raised when an active pending invitation already exists."""


class InvitationNotFoundError(MembershipError):
    """Raised when an invitation cannot be found."""


class InvitationNotPendingError(MembershipError):
    """Raised when an invitation is not in a pending state."""


class InvitationExpiredError(MembershipError):
    """Raised when an invitation has expired."""


class InvitationRevokedError(MembershipError):
    """Raised when an invitation has been revoked."""


class InvitationAlreadyAcceptedError(MembershipError):
    """Raised when an invitation has already been accepted."""


class InvitationEmailMismatchError(MembershipError):
    """Raised when the authenticated user's email does not match the invitation."""


class MembershipNotFoundError(MembershipError):
    """Raised when a membership cannot be found in the organization."""


class LastOwnerInvariantError(MembershipError):
    """Raised when an operation would leave the organization without an owner."""


class InvalidMembershipOperationError(MembershipError):
    """Raised when a membership operation conflicts with current state."""

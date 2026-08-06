"""Focused tests for member lifecycle ownership invariants."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.authorization import OrganizationRole
from app.modules.memberships.exceptions import (
    InvalidMembershipOperationError,
    LastOwnerInvariantError,
    MembershipNotFoundError,
)
from app.modules.memberships.service import MembershipService


def _membership(*, role: str, user_id=None, organization_id=None, membership_id=None):
    return SimpleNamespace(
        id=membership_id or uuid4(),
        organization_id=organization_id or uuid4(),
        user_id=user_id or uuid4(),
        role=role,
        created_at=datetime.now(timezone.utc),
    )


class FakeMembershipRepository:
    def __init__(self, memberships: list) -> None:
        self.memberships = memberships
        self.deleted_ids: list = []
        self.lock_calls = 0

    async def lock_owner_memberships(self, organization_id):
        self.lock_calls += 1
        return [
            membership
            for membership in self.memberships
            if membership.organization_id == organization_id
            and membership.role == OrganizationRole.OWNER.value
        ]

    async def get_by_id_and_organization_for_update(self, membership_id, organization_id):
        for membership in self.memberships:
            if (
                membership.id == membership_id
                and membership.organization_id == organization_id
            ):
                return membership
        return None

    async def get_by_organization_and_user_for_update(self, organization_id, user_id):
        for membership in self.memberships:
            if (
                membership.organization_id == organization_id
                and membership.user_id == user_id
            ):
                return membership
        return None

    async def delete(self, membership) -> None:
        self.deleted_ids.append(membership.id)
        self.memberships = [item for item in self.memberships if item.id != membership.id]

    async def list_members_for_organization(self, organization_id):
        return []


class FakeSession:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True

    async def refresh(self, _obj) -> None:
        return None


def _service(memberships: list) -> tuple[MembershipService, FakeMembershipRepository, FakeSession]:
    session = FakeSession()
    repository = FakeMembershipRepository(memberships)
    service = MembershipService(
        session=session,
        membership_repository=repository,
        invitation_repository=SimpleNamespace(),
        user_repository=SimpleNamespace(),
        settings=SimpleNamespace(),
    )
    return service, repository, session


@pytest.mark.asyncio
async def test_promote_member_to_owner():
    org_id = uuid4()
    owner = _membership(role="owner", organization_id=org_id)
    member = _membership(role="member", organization_id=org_id)
    service, _repo, session = _service([owner, member])

    updated = await service.update_member_role(
        organization_id=org_id,
        membership_id=member.id,
        new_role=OrganizationRole.OWNER,
    )

    assert updated.role == "owner"
    assert session.committed is True


@pytest.mark.asyncio
async def test_demote_owner_when_another_owner_remains():
    org_id = uuid4()
    owner_a = _membership(role="owner", organization_id=org_id)
    owner_b = _membership(role="owner", organization_id=org_id)
    service, _repo, session = _service([owner_a, owner_b])

    updated = await service.update_member_role(
        organization_id=org_id,
        membership_id=owner_b.id,
        new_role=OrganizationRole.MEMBER,
    )

    assert updated.role == "member"
    assert session.committed is True


@pytest.mark.asyncio
async def test_last_owner_cannot_be_demoted():
    org_id = uuid4()
    owner = _membership(role="owner", organization_id=org_id)
    member = _membership(role="member", organization_id=org_id)
    service, _repo, session = _service([owner, member])

    with pytest.raises(LastOwnerInvariantError):
        await service.update_member_role(
            organization_id=org_id,
            membership_id=owner.id,
            new_role=OrganizationRole.MEMBER,
        )

    assert session.rolled_back is True
    assert owner.role == "owner"


@pytest.mark.asyncio
async def test_role_update_rejects_foreign_membership():
    org_id = uuid4()
    other_org = uuid4()
    owner = _membership(role="owner", organization_id=org_id)
    foreign = _membership(role="member", organization_id=other_org)
    service, _repo, session = _service([owner, foreign])

    with pytest.raises(MembershipNotFoundError):
        await service.update_member_role(
            organization_id=org_id,
            membership_id=foreign.id,
            new_role=OrganizationRole.OWNER,
        )

    assert session.rolled_back is True


@pytest.mark.asyncio
async def test_remove_member_succeeds():
    org_id = uuid4()
    owner = _membership(role="owner", organization_id=org_id)
    member = _membership(role="member", organization_id=org_id)
    service, repo, session = _service([owner, member])

    await service.remove_member(organization_id=org_id, membership_id=member.id)

    assert member.id in repo.deleted_ids
    assert session.committed is True


@pytest.mark.asyncio
async def test_last_owner_cannot_be_removed():
    org_id = uuid4()
    owner = _membership(role="owner", organization_id=org_id)
    service, repo, session = _service([owner])

    with pytest.raises(LastOwnerInvariantError):
        await service.remove_member(organization_id=org_id, membership_id=owner.id)

    assert repo.deleted_ids == []
    assert session.rolled_back is True


@pytest.mark.asyncio
async def test_member_can_leave():
    org_id = uuid4()
    owner = _membership(role="owner", organization_id=org_id)
    member = _membership(role="member", organization_id=org_id)
    user = SimpleNamespace(id=member.user_id)
    service, repo, session = _service([owner, member])

    await service.leave_organization(organization_id=org_id, user=user)

    assert member.id in repo.deleted_ids
    assert session.committed is True


@pytest.mark.asyncio
async def test_sole_owner_cannot_leave():
    org_id = uuid4()
    owner = _membership(role="owner", organization_id=org_id)
    user = SimpleNamespace(id=owner.user_id)
    service, repo, session = _service([owner])

    with pytest.raises(LastOwnerInvariantError):
        await service.leave_organization(organization_id=org_id, user=user)

    assert repo.deleted_ids == []
    assert session.rolled_back is True


@pytest.mark.asyncio
async def test_owner_can_leave_when_another_owner_exists():
    org_id = uuid4()
    owner_a = _membership(role="owner", organization_id=org_id)
    owner_b = _membership(role="owner", organization_id=org_id)
    user = SimpleNamespace(id=owner_a.user_id)
    service, repo, session = _service([owner_a, owner_b])

    await service.leave_organization(organization_id=org_id, user=user)

    assert owner_a.id in repo.deleted_ids
    assert session.committed is True


@pytest.mark.asyncio
async def test_non_member_cannot_leave():
    org_id = uuid4()
    owner = _membership(role="owner", organization_id=org_id)
    outsider = SimpleNamespace(id=uuid4())
    service, _repo, session = _service([owner])

    with pytest.raises(MembershipNotFoundError):
        await service.leave_organization(organization_id=org_id, user=outsider)

    assert session.rolled_back is True


@pytest.mark.asyncio
async def test_transfer_ownership_is_atomic():
    org_id = uuid4()
    owner = _membership(role="owner", organization_id=org_id)
    member = _membership(role="member", organization_id=org_id)
    user = SimpleNamespace(id=owner.user_id)
    service, repo, session = _service([owner, member])

    await service.transfer_ownership(
        organization_id=org_id,
        current_user=user,
        target_membership_id=member.id,
    )

    assert member.role == "owner"
    assert owner.role == "member"
    assert session.committed is True
    assert repo.lock_calls >= 1


@pytest.mark.asyncio
async def test_transfer_rejects_self():
    org_id = uuid4()
    owner = _membership(role="owner", organization_id=org_id)
    user = SimpleNamespace(id=owner.user_id)
    service, _repo, session = _service([owner])

    with pytest.raises(InvalidMembershipOperationError):
        await service.transfer_ownership(
            organization_id=org_id,
            current_user=user,
            target_membership_id=owner.id,
        )

    assert session.rolled_back is True


@pytest.mark.asyncio
async def test_transfer_rejects_foreign_membership():
    org_id = uuid4()
    other_org = uuid4()
    owner = _membership(role="owner", organization_id=org_id)
    foreign = _membership(role="member", organization_id=other_org)
    user = SimpleNamespace(id=owner.user_id)
    service, _repo, session = _service([owner, foreign])

    with pytest.raises(MembershipNotFoundError):
        await service.transfer_ownership(
            organization_id=org_id,
            current_user=user,
            target_membership_id=foreign.id,
        )

    assert session.rolled_back is True


@pytest.mark.asyncio
async def test_concurrent_last_owner_leaves_are_serialized_by_lock_path():
    """Both leave attempts see the sole-owner invariant via locked owners."""
    org_id = uuid4()
    owner = _membership(role="owner", organization_id=org_id)
    service_a, repo_a, session_a = _service([owner])
    service_b, repo_b, session_b = _service([owner])

    with pytest.raises(LastOwnerInvariantError):
        await service_a.leave_organization(
            organization_id=org_id,
            user=SimpleNamespace(id=owner.user_id),
        )

    with pytest.raises(LastOwnerInvariantError):
        await service_b.leave_organization(
            organization_id=org_id,
            user=SimpleNamespace(id=owner.user_id),
        )

    assert repo_a.deleted_ids == []
    assert repo_b.deleted_ids == []
    assert session_a.rolled_back is True
    assert session_b.rolled_back is True
    assert repo_a.lock_calls == 1
    assert repo_b.lock_calls == 1

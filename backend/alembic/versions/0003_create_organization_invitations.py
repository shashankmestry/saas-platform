"""Create organization_invitations table.

Revision ID: 0003_org_invitations
Revises: 0002_create_organizations
Create Date: 2026-08-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Keep revision IDs <= 32 chars (alembic_version.version_num).
revision: str = "0003_org_invitations"
down_revision: str | None = "0002_create_organizations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organization_invitations",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_organization_invitations_organization_id"),
        "organization_invitations",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_invitations_email"),
        "organization_invitations",
        ["email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_invitations_token_hash"),
        "organization_invitations",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_organization_invitations_expires_at"),
        "organization_invitations",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_invitations_created_by_user_id"),
        "organization_invitations",
        ["created_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_organization_invitations_created_by_user_id"),
        table_name="organization_invitations",
    )
    op.drop_index(
        op.f("ix_organization_invitations_expires_at"),
        table_name="organization_invitations",
    )
    op.drop_index(
        op.f("ix_organization_invitations_token_hash"),
        table_name="organization_invitations",
    )
    op.drop_index(
        op.f("ix_organization_invitations_email"),
        table_name="organization_invitations",
    )
    op.drop_index(
        op.f("ix_organization_invitations_organization_id"),
        table_name="organization_invitations",
    )
    op.drop_table("organization_invitations")

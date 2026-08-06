"""Create organization_profiles table.

Revision ID: 0004_org_profiles
Revises: 0003_org_invitations
Create Date: 2026-08-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Keep revision IDs <= 32 chars (alembic_version.version_num).
revision: str = "0004_org_profiles"
down_revision: str | None = "0003_org_invitations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organization_profiles",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("website", sa.String(length=2048), nullable=True),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("default_currency", sa.String(length=3), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id"),
    )


def downgrade() -> None:
    op.drop_table("organization_profiles")

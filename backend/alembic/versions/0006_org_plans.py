"""Create organization_plans and backfill existing organizations to free.

Revision ID: 0006_org_plans
Revises: 0005_org_logo_path
Create Date: 2026-08-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Keep revision IDs <= 32 chars (alembic_version.version_num).
revision: str = "0006_org_plans"
down_revision: str | None = "0005_org_logo_path"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organization_plans",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("plan_key", sa.String(length=50), nullable=False),
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

    # Backfill every existing organization onto the Free plan.
    op.execute(
        sa.text(
            """
            INSERT INTO organization_plans (id, organization_id, plan_key, created_at, updated_at)
            SELECT gen_random_uuid(), id, 'free', now(), now()
            FROM organizations
            WHERE NOT EXISTS (
                SELECT 1
                FROM organization_plans
                WHERE organization_plans.organization_id = organizations.id
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_table("organization_plans")

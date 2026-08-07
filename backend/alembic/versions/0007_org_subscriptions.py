"""Create organization_subscriptions and backfill existing organizations.

Revision ID: 0007_org_subscriptions
Revises: 0006_org_plans
Create Date: 2026-08-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Keep revision IDs <= 32 chars (alembic_version.version_num).
revision: str = "0007_org_subscriptions"
down_revision: str | None = "0006_org_plans"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organization_subscriptions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_customer_id", sa.String(length=255), nullable=True),
        sa.Column("provider_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("plan_key", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("billing_interval", sa.String(length=20), nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "cancel_at_period_end",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
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

    # Backfill: FREE / ACTIVE / NONE / MONTHLY for every existing organization.
    op.execute(
        sa.text(
            """
            INSERT INTO organization_subscriptions (
                id,
                organization_id,
                provider,
                provider_customer_id,
                provider_subscription_id,
                plan_key,
                status,
                billing_interval,
                current_period_start,
                current_period_end,
                cancel_at_period_end,
                canceled_at,
                created_at,
                updated_at
            )
            SELECT
                gen_random_uuid(),
                o.id,
                'none',
                NULL,
                NULL,
                COALESCE(p.plan_key, 'free'),
                'active',
                'monthly',
                now(),
                now() + interval '30 days',
                false,
                NULL,
                now(),
                now()
            FROM organizations o
            LEFT JOIN organization_plans p ON p.organization_id = o.id
            WHERE NOT EXISTS (
                SELECT 1
                FROM organization_subscriptions s
                WHERE s.organization_id = o.id
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_table("organization_subscriptions")

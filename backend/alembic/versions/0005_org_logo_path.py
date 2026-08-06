"""Add logo_path to organization_profiles.

Revision ID: 0005_org_logo_path
Revises: 0004_org_profiles
Create Date: 2026-08-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Keep revision IDs <= 32 chars (alembic_version.version_num).
revision: str = "0005_org_logo_path"
down_revision: str | None = "0004_org_profiles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "organization_profiles",
        sa.Column("logo_path", sa.String(length=1024), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("organization_profiles", "logo_path")

"""drop the ugly " (manga)" suffix from manga novel titles

Revision ID: 0006_manga_clean_title
Revises: 0005_widen_fingerprint
Create Date: 2026-11-24
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0006_manga_clean_title"
down_revision = "0005_widen_fingerprint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text("UPDATE novels SET title = REPLACE(title, ' (manga)', '') "
                "WHERE source_dir LIKE 'manhwa:%'")
    )


def downgrade() -> None:
    op.execute(
        sa.text("UPDATE novels SET title = title || ' (manga)' "
                "WHERE source_dir LIKE 'manhwa:%'")
    )

"""widen scan_log.fingerprint for prefixed manga fingerprints

Revision ID: 0005_widen_fingerprint
Revises: 0004_manga_chapters
Create Date: 2026-11-24
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0005_widen_fingerprint"
down_revision = "0004_manga_chapters"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "scan_log", "fingerprint",
        existing_type=sa.String(64), type_=sa.String(80), existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "scan_log", "fingerprint",
        existing_type=sa.String(80), type_=sa.String(64), existing_nullable=True,
    )

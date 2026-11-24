"""manga chapters + page progress

Revision ID: 0004_manga_chapters
Revises: 0003_scan_fingerprint
Create Date: 2026-11-24
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004_manga_chapters"
down_revision = "0003_scan_fingerprint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("chapters", sa.Column("kind", sa.String(10), server_default="text", nullable=False))
    op.add_column("chapters", sa.Column("page_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("reading_state", sa.Column("page_index", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("reading_state", "page_index")
    op.drop_column("chapters", "page_count")
    op.drop_column("chapters", "kind")

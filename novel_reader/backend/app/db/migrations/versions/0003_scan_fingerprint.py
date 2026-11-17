"""scan log fingerprint

Revision ID: 0003_scan_fingerprint
Revises: 0002_source_dir_and_soft_delete
Create Date: 2026-11-17
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003_scan_fingerprint"
down_revision = "0002_source_dir_and_soft_delete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scan_log", sa.Column("fingerprint", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("scan_log", "fingerprint")

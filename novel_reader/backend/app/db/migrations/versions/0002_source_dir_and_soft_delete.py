"""novel source_dir key and chapter soft-delete

Revision ID: 0002_source_dir_and_soft_delete
Revises: 0001_initial
Create Date: 2026-11-16
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_source_dir_and_soft_delete"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("novels", sa.Column("source_dir", sa.String(300), nullable=True))
    op.execute("UPDATE novels SET source_dir = title")
    op.alter_column("novels", "source_dir", nullable=False)
    op.create_index("ix_novels_source_dir", "novels", ["source_dir"], unique=True)
    # Slugs are display-only now; two folders can legitimately slugify alike.
    op.drop_index("ix_novels_slug", table_name="novels")
    op.create_index("ix_novels_slug", "novels", ["slug"])
    op.add_column(
        "chapters",
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("chapters", "active")
    op.drop_index("ix_novels_slug", table_name="novels")
    op.create_index("ix_novels_slug", "novels", ["slug"], unique=True)
    op.drop_index("ix_novels_source_dir", table_name="novels")
    op.drop_column("novels", "source_dir")

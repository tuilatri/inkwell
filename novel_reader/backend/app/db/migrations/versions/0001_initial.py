"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-16
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

TSV = TSVECTOR().with_variant(sa.Text(), "sqlite")


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.create_table(
        "novels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_novels_slug", "novels", ["slug"], unique=True)

    op.create_table(
        "variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("novel_id", sa.Integer(), sa.ForeignKey("novels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lang", sa.String(8), nullable=False),
        sa.UniqueConstraint("novel_id", "lang", name="uq_variants_novel_lang"),
    )
    op.create_index("ix_variants_novel_id", "variants", ["novel_id"])

    op.create_table(
        "chapters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("variants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("rel_path", sa.String(1000), nullable=False),
        sa.Column("file_mtime", sa.Float(), nullable=False, server_default="0"),
        sa.Column("byte_size", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("variant_id", "rel_path", name="uq_chapters_variant_rel_path"),
    )
    op.create_index("ix_chapters_variant_id", "chapters", ["variant_id"])
    op.create_index("ix_chapters_number", "chapters", ["number"])

    op.create_table(
        "chapter_search",
        sa.Column("chapter_id", sa.Integer(), sa.ForeignKey("chapters.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tsv", TSV, nullable=False),
    )
    op.create_index("ix_chapter_search_tsv", "chapter_search", ["tsv"], postgresql_using="gin")

    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_admin_users_username", "admin_users", ["username"], unique=True)

    op.create_table(
        "token_sessions",
        sa.Column("jti", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("admin_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_token_sessions_user_id", "token_sessions", ["user_id"])

    op.create_table(
        "reading_state",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("admin_users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("chapter_id", sa.Integer(), sa.ForeignKey("chapters.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("scroll_pos", sa.Float(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "scan_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("novels_upserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chapters_upserted", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "scan_warnings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scan_log_id", sa.Integer(), sa.ForeignKey("scan_log.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(80), nullable=False),
        sa.Column("detail", sa.String(1000), nullable=False),
    )
    op.create_index("ix_scan_warnings_scan_log_id", "scan_warnings", ["scan_log_id"])


def downgrade() -> None:
    op.drop_table("scan_warnings")
    op.drop_table("scan_log")
    op.drop_table("reading_state")
    op.drop_table("token_sessions")
    op.drop_table("admin_users")
    op.drop_index("ix_chapter_search_tsv", table_name="chapter_search")
    op.drop_table("chapter_search")
    op.drop_table("chapters")
    op.drop_table("variants")
    op.drop_table("novels")

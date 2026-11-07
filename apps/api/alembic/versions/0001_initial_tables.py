"""initial tables: rubrics, screenings, results

Revision ID: 0001
Revises:
Create Date: 2026-11-07
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

JSONType = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "rubrics",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_title", sa.String(120), nullable=False),
        sa.Column("language", sa.String(2), nullable=False),
        sa.Column("criteria", JSONType, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "screenings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "rubric_id",
            sa.String(36),
            sa.ForeignKey("rubrics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("blind", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_screenings_expires_at", "screenings", ["expires_at"])
    op.create_table(
        "results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "screening_id",
            sa.String(36),
            sa.ForeignKey("screenings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("candidate_ref", sa.String(60), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("must_haves_met", sa.Boolean(), nullable=False),
        sa.Column("payload", JSONType, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_results_screening_id", "results", ["screening_id"])


def downgrade() -> None:
    op.drop_index("ix_results_screening_id", table_name="results")
    op.drop_table("results")
    op.drop_index("ix_screenings_expires_at", table_name="screenings")
    op.drop_table("screenings")
    op.drop_table("rubrics")

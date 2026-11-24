"""Briefing schema: briefings

Revision ID: 005_briefing_schema
Revises: 004_agent_session_schema
Create Date: 2026-11-24 14:50:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_briefing_schema"
down_revision: Union[str, None] = "004_agent_session_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "briefings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_code", sa.String(length=32), nullable=False),
        sa.Column("target_meeting_code", sa.String(length=32), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("structured_payload", sa.JSON(), server_default="{}", nullable=False),
        sa.Column(
            "validation_status", sa.String(length=32), server_default="PASSED", nullable=False
        ),
        sa.Column("validation_errors", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("citations_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("meetings_covered", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("generation_metadata", sa.JSON(), server_default="{}", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_briefings_team_code",
        "briefings",
        ["team_code"],
        unique=False,
    )
    op.create_index(
        "ix_briefings_target_meeting_code",
        "briefings",
        ["target_meeting_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_briefings_target_meeting_code", table_name="briefings")
    op.drop_index("ix_briefings_team_code", table_name="briefings")
    op.drop_table("briefings")

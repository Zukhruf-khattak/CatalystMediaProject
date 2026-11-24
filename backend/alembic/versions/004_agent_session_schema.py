"""Agent session schema: agent_sessions

Revision ID: 004_agent_session_schema
Revises: 003_temporal_memory_schema
Create Date: 2026-11-23 20:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_agent_session_schema"
down_revision: Union[str, None] = "003_temporal_memory_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("team_code", sa.String(length=32), nullable=True),
        sa.Column("title", sa.String(length=256), nullable=True),
        sa.Column("state_snapshot", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("messages_json", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("turn_count", sa.Integer(), server_default="0", nullable=False),
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
        "ix_agent_sessions_session_id",
        "agent_sessions",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        "ix_agent_sessions_team_code",
        "agent_sessions",
        ["team_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_agent_sessions_team_code", table_name="agent_sessions")
    op.drop_index("ix_agent_sessions_session_id", table_name="agent_sessions")
    op.drop_table("agent_sessions")

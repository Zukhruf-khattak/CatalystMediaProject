"""Temporal memory schema: memories, memory_relationships, memory_extraction_runs

Revision ID: 003_temporal_memory_schema
Revises: 002_dataset_ingestion_schema
Create Date: 2026-11-23 18:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_temporal_memory_schema"
down_revision: Union[str, None] = "002_dataset_ingestion_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    vector_col = Vector(384) if is_postgres else sa.Text()

    # 1. Memories Table
    op.create_table(
        "memories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("meeting_id", sa.Uuid(), nullable=False),
        sa.Column("turn_id", sa.Uuid(), nullable=True),
        sa.Column("memory_type", sa.String(length=32), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("quote", sa.Text(), nullable=False),
        sa.Column("speaker_label", sa.String(length=32), nullable=False),
        sa.Column("speaker_role", sa.String(length=64), nullable=True),
        sa.Column("meeting_order", sa.SmallInteger(), nullable=False),
        sa.Column("sequence_letter", sa.String(length=4), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="current", nullable=False),
        sa.Column("confidence", sa.Float(), server_default="1.0", nullable=False),
        sa.Column(
            "extraction_version", sa.String(length=32), server_default="1.0.0", nullable=False
        ),
        sa.Column("embedding", vector_col, nullable=True),
        sa.Column("metadata_json", sa.JSON(), server_default="{}", nullable=False),
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
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["turn_id"], ["transcript_turns.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_memories_team_id"), "memories", ["team_id"], unique=False)
    op.create_index(op.f("ix_memories_meeting_id"), "memories", ["meeting_id"], unique=False)
    op.create_index(op.f("ix_memories_turn_id"), "memories", ["turn_id"], unique=False)
    op.create_index(op.f("ix_memories_memory_type"), "memories", ["memory_type"], unique=False)
    op.create_index(op.f("ix_memories_status"), "memories", ["status"], unique=False)
    op.create_index(
        "idx_memories_team_type_status",
        "memories",
        ["team_id", "memory_type", "status"],
        unique=False,
    )
    op.create_index(
        "idx_memories_meeting_order",
        "memories",
        ["meeting_id", "meeting_order"],
        unique=False,
    )

    if is_postgres:
        op.execute(
            "CREATE INDEX idx_memories_embedding_hnsw ON memories USING hnsw (embedding vector_cosine_ops);"
        )

    # 2. Memory Relationships Table
    op.create_table(
        "memory_relationships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_memory_id", sa.Uuid(), nullable=False),
        sa.Column("target_memory_id", sa.Uuid(), nullable=False),
        sa.Column("relationship_type", sa.String(length=32), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("is_ambiguous", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("confidence", sa.Float(), server_default="1.0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["source_memory_id"], ["memories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_memory_id"], ["memories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_memory_id",
            "target_memory_id",
            "relationship_type",
            name="uq_memory_rel_source_target_type",
        ),
    )
    op.create_index(
        op.f("ix_memory_relationships_source_memory_id"),
        "memory_relationships",
        ["source_memory_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_memory_relationships_target_memory_id"),
        "memory_relationships",
        ["target_memory_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_memory_relationships_relationship_type"),
        "memory_relationships",
        ["relationship_type"],
        unique=False,
    )

    # 3. Memory Extraction Runs Table
    op.create_table(
        "memory_extraction_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=True),
        sa.Column("meeting_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="PENDING", nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_turns_analyzed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_memories_extracted", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_memories_validated", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_memories_rejected", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_relationships_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("errors_json", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("summary_json", sa.JSON(), server_default="{}", nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_memory_extraction_runs_team_id"),
        "memory_extraction_runs",
        ["team_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_memory_extraction_runs_meeting_id"),
        "memory_extraction_runs",
        ["meeting_id"],
        unique=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    op.drop_table("memory_extraction_runs")
    op.drop_table("memory_relationships")
    if is_postgres:
        op.execute("DROP INDEX IF EXISTS idx_memories_embedding_hnsw;")
    op.drop_table("memories")

"""Dataset ingestion schema: teams, meetings, speakers, transcript turns, ingestion jobs

Revision ID: 002_dataset_ingestion_schema
Revises: 001_initial_pgvector
Create Date: 2026-11-23 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_dataset_ingestion_schema"
down_revision: Union[str, None] = "001_initial_pgvector"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. Teams Table
    op.create_table(
        "teams",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_code", sa.String(length=32), nullable=False),
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
        sa.UniqueConstraint("team_code"),
    )
    op.create_index(op.f("ix_teams_team_code"), "teams", ["team_code"], unique=True)

    # 2. Meetings Table
    op.create_table(
        "meetings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("meeting_code", sa.String(length=32), nullable=False),
        sa.Column("meeting_number", sa.SmallInteger(), nullable=True),
        sa.Column("sequence_letter", sa.String(length=4), nullable=True),
        sa.Column("total_turns", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="INGESTED"),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("parser_version", sa.String(length=32), nullable=False, server_default="1.0.0"),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_code"),
    )
    op.create_index(op.f("ix_meetings_meeting_code"), "meetings", ["meeting_code"], unique=True)
    op.create_index(op.f("ix_meetings_team_id"), "meetings", ["team_id"], unique=False)
    op.create_index(op.f("ix_meetings_source_sha256"), "meetings", ["source_sha256"], unique=False)

    # 3. Speakers Table
    op.create_table(
        "speakers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("meeting_id", sa.Uuid(), nullable=False),
        sa.Column("speaker_label", sa.String(length=32), nullable=False),
        sa.Column("speaker_letter", sa.String(length=8), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=True),
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
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id", "speaker_label", name="uq_speaker_meeting_label"),
    )
    op.create_index(op.f("ix_speakers_meeting_id"), "speakers", ["meeting_id"], unique=False)

    # 4. Transcript Turns Table
    vector_col = Vector(384) if is_postgres else sa.Text()
    tsvector_col = postgresql.TSVECTOR() if is_postgres else sa.Text()

    op.create_table(
        "transcript_turns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("meeting_id", sa.Uuid(), nullable=False),
        sa.Column("speaker_id", sa.Uuid(), nullable=False),
        sa.Column("turn_index", sa.Integer(), nullable=False),
        sa.Column("start_time_str", sa.String(length=16), nullable=False),
        sa.Column("start_time_seconds", sa.Integer(), nullable=False),
        sa.Column("end_time_seconds", sa.Integer(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("search_vector", tsvector_col, nullable=True),
        sa.Column("embedding", vector_col, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["speaker_id"], ["speakers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id", "turn_index", name="uq_turn_meeting_index"),
    )
    op.create_index(
        op.f("ix_transcript_turns_meeting_id"), "transcript_turns", ["meeting_id"], unique=False
    )
    op.create_index(
        op.f("ix_transcript_turns_speaker_id"), "transcript_turns", ["speaker_id"], unique=False
    )
    op.create_index(
        "idx_turns_meeting_index", "transcript_turns", ["meeting_id", "turn_index"], unique=False
    )

    # PostgreSQL-specific indexes and trigger
    if is_postgres:
        # GIN Index for Full-Text Search
        op.execute(
            "CREATE INDEX idx_turns_search_vector ON transcript_turns USING gin(search_vector);"
        )
        # HNSW Index for Cosine Similarity Embedding Search
        op.execute(
            "CREATE INDEX idx_turns_embedding_hnsw ON transcript_turns USING hnsw (embedding vector_cosine_ops);"
        )
        # Automatic trigger for maintaining search_vector on insert/update
        op.execute(
            """
            CREATE TRIGGER trg_turns_search_vector_update
            BEFORE INSERT OR UPDATE ON transcript_turns
            FOR EACH ROW EXECUTE FUNCTION
            tsvector_update_trigger(search_vector, 'pg_catalog.english', raw_text);
            """
        )

    # 5. Ingestion Jobs Table
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="PENDING", nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_files", sa.Integer(), server_default="0", nullable=False),
        sa.Column("completed_meetings", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_meetings", sa.Integer(), server_default="0", nullable=False),
        sa.Column("skipped_meetings", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_turns", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_words", sa.Integer(), server_default="0", nullable=False),
        sa.Column("embedded_turns", sa.Integer(), server_default="0", nullable=False),
        sa.Column("current_file", sa.String(length=255), nullable=True),
        sa.Column("errors_json", sa.JSON(), nullable=False),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute("DROP TRIGGER IF EXISTS trg_turns_search_vector_update ON transcript_turns;")
        op.execute("DROP INDEX IF EXISTS idx_turns_embedding_hnsw;")
        op.execute("DROP INDEX IF EXISTS idx_turns_search_vector;")

    op.drop_table("ingestion_jobs")
    op.drop_index("idx_turns_meeting_index", table_name="transcript_turns")
    op.drop_index(op.f("ix_transcript_turns_speaker_id"), table_name="transcript_turns")
    op.drop_index(op.f("ix_transcript_turns_meeting_id"), table_name="transcript_turns")
    op.drop_table("transcript_turns")
    op.drop_index(op.f("ix_speakers_meeting_id"), table_name="speakers")
    op.drop_table("speakers")
    op.drop_index(op.f("ix_meetings_source_sha256"), table_name="meetings")
    op.drop_index(op.f("ix_meetings_team_id"), table_name="meetings")
    op.drop_index(op.f("ix_meetings_meeting_code"), table_name="meetings")
    op.drop_table("meetings")
    op.drop_index(op.f("ix_teams_team_code"), table_name="teams")
    op.drop_table("teams")

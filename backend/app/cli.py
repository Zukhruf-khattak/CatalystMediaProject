import argparse
import sys
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.agent.service import AgentService
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.dataset import Meeting, Team
from app.schemas.agent import AgentQueryRequest
from app.schemas.memory import MemorySearchFilter
from app.schemas.retrieval import RetrievalRequest
from app.scripts.ingest_dataset import main as run_ingest
from app.services.hybrid_retrieval_service import HybridRetrievalService
from app.services.memory_extraction_service import MemoryExtractionService
from app.services.memory_retrieval_service import MemoryRetrievalService

logger = get_logger("app.cli")


def get_db_session(database_url: Optional[str] = None) -> Session:
    """Helper to acquire a database session for CLI operations."""
    url = database_url or get_settings().database_url
    engine = create_engine(url)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return session_factory()


def handle_extract_memory(args: argparse.Namespace) -> None:
    """CLI handler for temporal memory extraction."""
    db = get_db_session(args.database_url)
    service = MemoryExtractionService(db=db)

    try:
        if args.meeting_code:
            meeting = db.query(Meeting).filter(Meeting.meeting_code == args.meeting_code).first()
            if not meeting:
                print(f"Error: Meeting '{args.meeting_code}' not found in database.")
                sys.exit(1)
            print(f"Starting memory extraction for meeting: {args.meeting_code}...")
            run = service.extract_memories_for_meeting(meeting_id=meeting.id, force=args.force)
            print(f"Extraction run {run.id} finished with status '{run.status}'.")
            print(f"Summary: {run.summary_json}")
        elif args.team_code:
            team = db.query(Team).filter(Team.team_code == args.team_code).first()
            if not team:
                print(f"Error: Team '{args.team_code}' not found in database.")
                sys.exit(1)
            print(f"Starting chronological memory extraction for team: {args.team_code}...")
            runs = service.extract_memories_for_team(team_code=args.team_code, force=args.force)
            print(f"Extracted memories across {len(runs)} meetings for team {args.team_code}.")
            for r in runs:
                print(f" - {r.summary_json.get('meeting_code')}: {r.summary_json}")
        else:
            print("Error: Specify either --team-code or --meeting-code.")
            sys.exit(1)
    finally:
        db.close()


def handle_search_memory(args: argparse.Namespace) -> None:
    """CLI handler for searching temporal memories."""
    db = get_db_session(args.database_url)
    service = MemoryRetrievalService(db=db)

    try:
        filters = MemorySearchFilter(
            team_code=args.team_code,
            memory_type=args.type,
            status=args.status,
            query_text=args.query,
            limit=args.limit,
            offset=0,
        )
        items, total_count = service.search_memories(filters)
        print(f"\nFound {total_count} matching memories (showing top {len(items)}):")
        print("-" * 80)
        for idx, item in enumerate(items, 1):
            rels = [
                f"{r.relationship_type}->{str(r.target_memory_id)[:8]}"
                for r in item.outgoing_relationships
            ]
            rel_str = f" | Links: {', '.join(rels)}" if rels else ""
            print(
                f"[{idx}] {item.memory_type} | Status: {item.status} | Order: {item.meeting_order} ({item.sequence_letter})"
            )
            print(f"    Statement: {item.statement}")
            print(f"    Speaker:   {item.speaker_label}")
            print(f'    Quote:     "{item.quote}"{rel_str}')
            print("-" * 80)
    finally:
        db.close()


def handle_retrieve(args: argparse.Namespace) -> None:
    """CLI handler for executing hybrid retrieval."""
    db = get_db_session(args.database_url)
    service = HybridRetrievalService(db=db)

    try:
        req = RetrievalRequest(
            query=args.query,
            team_code=args.team_code,
            method=args.method or "hybrid",
            limit=args.limit,
        )
        pack = service.execute_retrieval(req)

        print("\n" + "=" * 80)
        print(f"QUERY: {pack.query}")
        print(
            f"EXTRACTED: Team={pack.processed_query.extracted_team} | "
            f"Topics={pack.processed_query.extracted_topics} | "
            f"Intent={pack.processed_query.temporal_intent}"
        )
        print(f"METHOD: {pack.retrieval_method} | TOTAL TURNS: {pack.total_results}")
        if pack.cross_meeting_summary:
            print(f"CROSS-MEETING EVIDENCE: {pack.cross_meeting_summary}")
        print("=" * 80)

        print("\n--- RETRIEVED TRANSCRIPT SEGMENTS ---")
        for idx, turn in enumerate(pack.transcript_segments, 1):
            role_str = f" ({turn.speaker_role})" if turn.speaker_role else ""
            print(
                f"[{idx}] {turn.meeting_code} (Turn {turn.turn_index}) | {turn.speaker_label}{role_str} at {turn.start_time_str} | Score: {turn.score}"
            )
            print(f'    "{turn.raw_text}"')
            print("-" * 80)

        if pack.temporal_memories:
            print("\n--- RELATED TEMPORAL MEMORIES ---")
            for idx, mem in enumerate(pack.temporal_memories, 1):
                rels = [
                    f"{r.relationship_type}->{str(r.target_memory_id)[:8]}"
                    for r in mem.outgoing_relationships
                ]
                rel_str = f" | Links: {', '.join(rels)}" if rels else ""
                print(
                    f"[{idx}] {mem.meeting_code} | {mem.memory_type} | Status: {mem.status}{rel_str}"
                )
                print(f"    Statement: {mem.statement}")
                print(f'    Quote:     "{mem.quote}"')
                print("-" * 80)

        if pack.unresolved_disagreements:
            print("\n--- UNRESOLVED DISAGREEMENTS ---")
            for idx, dis in enumerate(pack.unresolved_disagreements, 1):
                print(f"[{idx}] {dis.meeting_code} | Status: {dis.status}")
                print(f"    Issue: {dis.statement}")
                print(f'    Quote: "{dis.quote}"')
                print("-" * 80)
    finally:
        db.close()


def handle_ask(args: argparse.Namespace) -> None:
    """CLI handler for querying the LangGraph meeting research agent."""
    db = get_db_session(args.database_url)
    service = AgentService(db=db)

    try:
        req = AgentQueryRequest(
            question=args.query,
            team_code=args.team_code,
            session_id=args.session_id,
            max_iterations=args.max_iterations,
        )
        print(f"\nSubmitting question to Catalist Agent: '{args.query}'...")
        res = service.query(req)

        print("\n" + "=" * 80)
        print("CATALIST AGENT RESPONSE")
        print("=" * 80)
        print(f"QUESTION:    {res.question}")
        print(f"SESSION ID:  {res.session_id}")
        print(f"SUFFICIENT:  {res.is_sufficient}")
        if res.insufficient_reason:
            print(f"REASON:      {res.insufficient_reason}")
        print(f"ITERATIONS:  {res.iteration_count}")
        print(f"STEPS:       {' -> '.join(res.steps_taken)}")
        print("\n--- ANSWER ---")
        print(res.answer)
        print("\n--- CITATIONS ---")
        for idx, cite in enumerate(res.citations, 1):
            spk = f" ({cite.speaker_label})" if cite.speaker_label else ""
            print(f'[{idx}] {cite.meeting_id}{spk}: "{cite.quote}"')
        print("=" * 80 + "\n")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="catalist",
        description="Catalist Meeting Intelligence CLI",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # Ingest subcommand
    ingest_parser = subparsers.add_parser("ingest", help="Ingest transcript dataset into database")
    ingest_parser.add_argument(
        "--dataset-path",
        type=str,
        default="data/raw",
        help="Path to directory containing transcripts or raw dataset zip archive",
    )
    ingest_parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="Optional database connection URL",
    )
    ingest_parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-ingestion of already processed meetings",
    )
    ingest_parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip dense embedding generation for fast text/lexical ingestion",
    )
    ingest_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of files to process",
    )

    # Extract memory subcommand
    extract_parser = subparsers.add_parser(
        "extract-memory", help="Extract temporal memories from transcripts"
    )
    extract_parser.add_argument("--team-code", type=str, help="Team code (e.g. TS3006)")
    extract_parser.add_argument("--meeting-code", type=str, help="Meeting code (e.g. TS3006a)")
    extract_parser.add_argument(
        "--force", action="store_true", help="Force re-extraction of already processed meetings"
    )
    extract_parser.add_argument(
        "--database-url", type=str, default=None, help="Optional database URL"
    )

    # Search memory subcommand
    search_parser = subparsers.add_parser(
        "search-memory", help="Search and inspect temporal memories"
    )
    search_parser.add_argument("--team-code", type=str, help="Filter by team code")
    search_parser.add_argument(
        "--type", type=str, help="Filter by memory type (DECISION, ACTION, etc.)"
    )
    search_parser.add_argument(
        "--status", type=str, help="Filter by status (current, superseded, open, resolved)"
    )
    search_parser.add_argument("--query", type=str, help="Search text query")
    search_parser.add_argument("--limit", type=int, default=20, help="Max results to display")
    search_parser.add_argument(
        "--database-url", type=str, default=None, help="Optional database URL"
    )

    # Retrieve subcommand
    retrieve_parser = subparsers.add_parser(
        "retrieve", help="Execute hybrid retrieval across meetings and memories"
    )
    retrieve_parser.add_argument(
        "--query", type=str, required=True, help="Question or search query"
    )
    retrieve_parser.add_argument("--team-code", type=str, help="Target team code (e.g. TS3006)")
    retrieve_parser.add_argument(
        "--method",
        type=str,
        default="hybrid",
        choices=["hybrid", "keyword", "vector"],
        help="Retrieval channel",
    )
    retrieve_parser.add_argument("--limit", type=int, default=10, help="Max turns to return")
    retrieve_parser.add_argument(
        "--database-url", type=str, default=None, help="Optional database URL"
    )

    # Ask subcommand (LangGraph Agent)
    ask_parser = subparsers.add_parser("ask", help="Ask questions using LangGraph agent")
    ask_parser.add_argument("--query", type=str, required=True, help="Question to ask")
    ask_parser.add_argument("--team-code", type=str, help="Target team code (e.g. TS3006)")
    ask_parser.add_argument("--session-id", type=str, help="Resume conversation session UUID")
    ask_parser.add_argument(
        "--max-iterations", type=int, default=2, help="Max retrieval loop iterations"
    )
    ask_parser.add_argument("--database-url", type=str, default=None, help="Optional database URL")

    args = parser.parse_args()

    if args.subcommand == "ingest":
        sys.argv = [sys.argv[0]]
        if args.dataset_path:
            sys.argv.extend(["--dataset-path", args.dataset_path])
        if args.database_url:
            sys.argv.extend(["--database-url", args.database_url])
        if args.force:
            sys.argv.append("--force")
        if args.skip_embeddings:
            sys.argv.append("--skip-embeddings")
        if args.limit:
            sys.argv.extend(["--limit", str(args.limit)])
        run_ingest()
    elif args.subcommand == "extract-memory":
        handle_extract_memory(args)
    elif args.subcommand == "search-memory":
        handle_search_memory(args)
    elif args.subcommand == "retrieve":
        handle_retrieve(args)
    elif args.subcommand == "ask":
        handle_ask(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

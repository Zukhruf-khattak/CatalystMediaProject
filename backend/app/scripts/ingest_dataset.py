import argparse
import sys
from pathlib import Path

# Add backend directory to sys.path if not present
backend_dir = Path(__file__).resolve().parents[2]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.logging import get_logger, setup_logging  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.schemas.dataset import IngestionJobCreate  # noqa: E402
from app.services.ingestion_service import IngestionService  # noqa: E402

logger = get_logger("app.scripts.ingest_dataset")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Catalist Transcript Dataset Ingestion and Indexing CLI",
    )
    parser.add_argument(
        "--dataset-path",
        type=str,
        default="data/raw",
        help="Path to directory containing transcripts or raw dataset zip archive",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="Optional database connection URL (defaults to configured settings.database_url)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-ingestion of already processed meetings",
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip dense embedding generation for fast text/lexical ingestion",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of files to process (useful for smoke tests)",
    )

    args = parser.parse_args()
    setup_logging(log_level="INFO", log_format="text")

    dataset_path = Path(args.dataset_path)
    logger.info(
        f"Starting ingestion CLI with dataset path: {dataset_path} "
        f"[force={args.force}, skip_embeddings={args.skip_embeddings}, limit={args.limit}]"
    )

    db_url = args.database_url
    if db_url:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        import app.models  # noqa: F401
        from app.db.base import Base

        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        custom_engine = create_engine(db_url, connect_args=connect_args)
        Base.metadata.create_all(bind=custom_engine)
        custom_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=custom_engine)
        db = custom_session_factory()
    else:
        db = SessionLocal()
    try:
        service = IngestionService(db=db)
        options = IngestionJobCreate(
            force_reingest=args.force,
            skip_embeddings=args.skip_embeddings,
            limit_files=args.limit,
        )
        job = service.run_ingestion(options=options, custom_dataset_dir=dataset_path)

        print("\n" + "=" * 60)
        print("INGESTION JOB SUMMARY")
        print("=" * 60)
        print(f"Job ID:              {job.id}")
        print(f"Status:              {job.status}")
        print(f"Total Files Found:   {job.total_files}")
        print(f"Completed Meetings:  {job.completed_meetings}")
        print(f"Skipped Meetings:    {job.skipped_meetings}")
        print(f"Failed Meetings:     {job.failed_meetings}")
        print(f"Total Turns Parsed:  {job.total_turns}")
        print(f"Total Words Parsed:  {job.total_words}")
        print(f"Embedded Turns:      {job.embedded_turns}")
        if job.errors_json:
            print(f"Errors Logged:       {len(job.errors_json)}")
            for err in job.errors_json[:5]:
                print(f"  - {err.get('filename')}: {err.get('error')}")
        print("=" * 60 + "\n")

        if job.status == "FAILED":
            sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

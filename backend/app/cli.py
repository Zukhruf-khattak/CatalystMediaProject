import argparse
import sys

from app.scripts.ingest_dataset import main as run_ingest


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

    args = parser.parse_args()

    if args.subcommand == "ingest":
        # Pass forwarded arguments to ingest runner
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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

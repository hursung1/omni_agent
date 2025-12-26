import argparse
from pathlib import Path

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chunk and upsert documents into an Elasticsearch vector index."
    )
    parser.add_argument(
        "--index",
        type=str,
        help=f"Target Elasticsearch index",
    )
    parser.add_argument(
        "--docs",
        type=Path,
        help=f"Directory holding source documents",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process documents without writing to Elasticsearch.",
    )
    return parser.parse_args()


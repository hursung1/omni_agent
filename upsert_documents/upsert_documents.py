
"""
Utility script that chunks documents located under ``./docs`` and upserts them
into the configured Elasticsearch vector index.

Environment variables you can use:
    ELASTICSEARCH_INDEX        -> Target index name (defaults to omni-agent-docs)
    ELASTICSEARCH_URL          -> HTTP endpoint, e.g. http://localhost:9200
    ELASTICSEARCH_CLOUD_ID     -> Cloud ID if you use Elastic Cloud
    ELASTICSEARCH_API_KEY      -> API key for Elastic Cloud/Serverless
    ELASTICSEARCH_USERNAME     -> Basic auth username (fallback if no API key)
    ELASTICSEARCH_PASSWORD     -> Basic auth password (fallback if no API key)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Iterable, List

from langchain_core.documents import Document
from langchain_elasticsearch import ElasticsearchStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from models.embedding import emb

LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[1]
DOCS_DIR = BASE_DIR / "docs"
DEFAULT_INDEX_NAME = os.getenv("ELASTICSEARCH_INDEX", "omni-agent-docs")

# 1000/200 is widely recommended for character-based chunking to balance recall & cost.
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
SUPPORTED_TEXT_EXTS = {".txt", ".md", ".markdown", ".json"}


def _iter_source_files(source_dir: Path) -> Iterable[Path]:
    """Yield every supported text file under the given directory."""
    if not source_dir.exists():
        raise FileNotFoundError(
            f"Docs directory {source_dir} does not exist. "
            "Create it and put text files there before running the script."
        )
    for path in sorted(source_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_TEXT_EXTS:
            yield path


def _load_file(path: Path) -> str:
    """Return the string representation of a path's contents."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".json":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return text
        # Keep JSON human readable but deterministic so chunks stay stable.
        return json.dumps(parsed, ensure_ascii=False, indent=2)
    return text


def load_documents(source_dir: Path) -> List[Document]:
    """Load supported files and create LangChain Document objects."""
    documents: List[Document] = []
    for file_path in _iter_source_files(source_dir):
        content = _load_file(file_path).strip()
        if not content:
            LOGGER.warning("Skipping empty file: %s", file_path)
            continue
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": str(file_path.relative_to(BASE_DIR)),
                    "filename": file_path.name,
                },
            )
        )
    if not documents:
        raise ValueError(
            f"No readable documents found in {source_dir}. "
            f"Supported extensions: {', '.join(sorted(SUPPORTED_TEXT_EXTS))}"
        )
    return documents


def split_documents(documents: List[Document]) -> List[Document]:
    """Chunk documents so they work well with vector search."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.split_documents(documents)


def build_store(index_name: str) -> ElasticsearchStore:
    """Instantiate an ElasticsearchStore with the configured auth."""
    es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
    api_key = os.getenv("ELASTICSEARCH_API_KEY")
    username = os.getenv("ELASTICSEARCH_USERNAME")
    password = os.getenv("ELASTICSEARCH_PASSWORD")

    auth_kwargs: dict = {}
    if api_key:
        auth_kwargs["es_api_key"] = api_key
    elif username and password:
        auth_kwargs.update({"es_user": username, "es_password": password})

    # es_cloud_id takes precedence when provided.
    connection_kwargs = {"es_cloud_id": cloud_id} if cloud_id else {"es_url": es_url}
    return ElasticsearchStore(
        index_name=index_name,
        embedding=emb,
        **connection_kwargs,
        **auth_kwargs,
    )


def upsert(index_name: str, docs_path: Path, dry_run: bool = False) -> None:
    """Load, chunk, and upload documents."""
    LOGGER.info("Loading documents from %s", docs_path)
    raw_docs = load_documents(docs_path)
    LOGGER.info("Loaded %d source documents", len(raw_docs))

    chunks = split_documents(raw_docs)
    LOGGER.info(
        "Split into %d chunks (chunk_size=%d, chunk_overlap=%d)",
        len(chunks),
        CHUNK_SIZE,
        CHUNK_OVERLAP,
    )

    if dry_run:
        LOGGER.info("Dry-run enabled; skipping upload.")
        return

    store = build_store(index_name)
    store.add_documents(chunks)
    LOGGER.info("Finished upserting %d chunks into index '%s'", len(chunks), index_name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chunk and upsert documents into an Elasticsearch vector index."
    )
    parser.add_argument(
        "--index",
        default=DEFAULT_INDEX_NAME,
        help=f"Target Elasticsearch index (default: {DEFAULT_INDEX_NAME})",
    )
    parser.add_argument(
        "--docs",
        type=Path,
        default=DOCS_DIR,
        help=f"Directory holding source documents (default: {DOCS_DIR})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process documents without writing to Elasticsearch.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()
    upsert(index_name=args.index, docs_path=args.docs, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

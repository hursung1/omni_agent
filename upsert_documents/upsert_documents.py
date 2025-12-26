
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

from elasticsearch import Elasticsearch, AsyncElasticsearch
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from models.embedding import emb
from upsert_documents.argparser import parse_args

LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[1]
DOCS_DIR = BASE_DIR / "docs"

SUPPORTED_TEXT_EXTS = {".txt", ".md", ".markdown", ".json"}

class ESDocumentHandler:
    def __init__(self, index_name: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.index_name = index_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.es_client = self.get_es_client(is_async=False)

    # Set ES client
    def get_es_client(self, is_async: bool = False) -> Elasticsearch | AsyncElasticsearch:
        """Instantiate an ElasticsearchStore with the configured auth."""
        es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        username = os.getenv("ELASTICSEARCH_USERNAME", "elastic")
        password = os.getenv("ELASTICSEARCH_PASSWORD")

        if is_async: # Asynchronous ES client
            return AsyncElasticsearch(
                [{"host": es_url, "scheme": "https"}],
                basic_auth=(username, password),
                verify_certs=False,
                ca_certs=None
            )

        else: # Synchronous ES client
            return Elasticsearch(
                [{"host": es_url, "scheme": "https"}],
                basic_auth=(username, password),
                verify_certs=False,
                ca_certs=None
            )
        
    def load_documents(self, source_dir: Path) -> List[Document]:
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
    
    def add_documents(self, documents: List[Document]):
        for doc in documents:
            # 1. split documents

            # 2. upsert to db
            self.es_client.index(index=self.index_name, document=doc.page_content, id=doc.metadata["source"])

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

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Chunk documents so they work well with vector search."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )
        return splitter.split_documents(documents)


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


def upsert(index_name: str, docs_path: Path, dry_run: bool = False) -> None:
    ...

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()
    upsert(index_name=args.index, docs_path=args.docs, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

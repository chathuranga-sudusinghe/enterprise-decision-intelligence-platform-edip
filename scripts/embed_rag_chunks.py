from __future__ import annotations

import argparse
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd
import yaml
from openai import OpenAI
from dotenv import load_dotenv

# =========================================================
# Logging
# =========================================================
logger = logging.getLogger("embed_rag_chunks")

def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


# =========================================================
# Constants
# =========================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "rag_ingestion_config.yaml"
DEFAULT_CHUNKS_JSONL = PROJECT_ROOT / "data" / "processed" / "rag" / "document_chunks.jsonl"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "rag"

ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_BATCH_SIZE = 50
DEFAULT_MAX_RETRIES = 5
DEFAULT_RETRY_SLEEP_SECONDS = 2.0


# =========================================================
# Dataclasses
# =========================================================
@dataclass
class EmbeddingPaths:
    chunks_jsonl: Path
    embeddings_jsonl: Path
    embeddings_csv: Path
    manifest_json: Path


@dataclass
class EmbeddingConfig:
    model_name: str
    dimensions: int | None
    batch_size: int
    max_retries: int
    retry_sleep_seconds: float
    namespace: str | None


# =========================================================
# Path helpers
# =========================================================
def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def build_default_paths() -> EmbeddingPaths:
    ensure_dir(DEFAULT_OUTPUT_DIR)
    return EmbeddingPaths(
        chunks_jsonl=DEFAULT_CHUNKS_JSONL,
        embeddings_jsonl=DEFAULT_OUTPUT_DIR / "chunk_embeddings.jsonl",
        embeddings_csv=DEFAULT_OUTPUT_DIR / "chunk_embeddings.csv",
        manifest_json=DEFAULT_OUTPUT_DIR / "embedding_manifest.json",
    )


# =========================================================
# Config loading
# =========================================================
def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing YAML config file: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc


def resolve_embedding_config(config: Dict[str, Any]) -> EmbeddingConfig:
    """
    Supports a few safe config shapes so this script stays resilient.
    """
    embed_cfg: Dict[str, Any] = {}
    namespace: str | None = None

    candidates = [
        config.get("embedding", {}),
        config.get("embeddings", {}),
        config.get("ingestion", {}).get("embedding", {}) if isinstance(config.get("ingestion"), dict) else {},
        config.get("ingestion", {}).get("embeddings", {}) if isinstance(config.get("ingestion"), dict) else {},
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            embed_cfg.update({k: v for k, v in candidate.items() if v is not None})

    pinecone_cfg_candidates = [
        config.get("pinecone", {}),
        config.get("vector_db", {}),
        config.get("ingestion", {}).get("pinecone", {}) if isinstance(config.get("ingestion"), dict) else {},
    ]
    for candidate in pinecone_cfg_candidates:
        if isinstance(candidate, dict) and candidate.get("namespace") is not None:
            namespace = str(candidate["namespace"]).strip()

    model_name = str(embed_cfg.get("model_name", DEFAULT_EMBEDDING_MODEL)).strip()
    dimensions = embed_cfg.get("dimensions")
    batch_size = int(embed_cfg.get("batch_size", DEFAULT_BATCH_SIZE))
    max_retries = int(embed_cfg.get("max_retries", DEFAULT_MAX_RETRIES))
    retry_sleep_seconds = float(embed_cfg.get("retry_sleep_seconds", DEFAULT_RETRY_SLEEP_SECONDS))

    if dimensions is not None:
        dimensions = int(dimensions)
        if dimensions <= 0:
            raise ValueError("Embedding dimensions must be positive if provided.")

    if batch_size <= 0:
        raise ValueError("batch_size must be positive.")

    if max_retries <= 0:
        raise ValueError("max_retries must be positive.")

    if retry_sleep_seconds < 0:
        raise ValueError("retry_sleep_seconds cannot be negative.")

    return EmbeddingConfig(
        model_name=model_name,
        dimensions=dimensions,
        batch_size=batch_size,
        max_retries=max_retries,
        retry_sleep_seconds=retry_sleep_seconds,
        namespace=namespace,
    )


# =========================================================
# Input loading
# =========================================================
def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing chunk file: {path}. Run chunk_rag_documents.py first."
        )

    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON line in {path} at line {line_number}: {exc}"
                ) from exc

    if not rows:
        raise ValueError(f"No records found in {path}")

    return rows


def validate_chunk_records(records: List[Dict[str, Any]]) -> None:
    required_fields = [
        "chunk_id",
        "source_document_id",
        "chunk_index",
        "chunk_text",
        "document_type",
        "business_domain",
        "region_scope",
        "source_path",
    ]

    seen_ids: set[str] = set()

    for row in records:
        for field in required_fields:
            value = row.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                raise ValueError(f"Chunk record missing required field: {field}")

        chunk_id = str(row["chunk_id"])
        if chunk_id in seen_ids:
            raise ValueError(f"Duplicate chunk_id found in chunk input: {chunk_id}")
        seen_ids.add(chunk_id)


# =========================================================
# OpenAI embeddings
# =========================================================
def build_openai_client() -> OpenAI:
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Add it to environment before running embeddings."
        )
    return OpenAI(api_key=api_key)


def batched(items: List[Dict[str, Any]], batch_size: int) -> Iterable[List[Dict[str, Any]]]:
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def request_embeddings_with_retry(
    client: OpenAI,
    texts: List[str],
    config: EmbeddingConfig,
) -> List[List[float]]:
    last_error: Exception | None = None

    for attempt in range(1, config.max_retries + 1):
        try:
            request_kwargs: Dict[str, Any] = {
                "model": config.model_name,
                "input": texts,
            }

            if config.dimensions is not None:
                request_kwargs["dimensions"] = config.dimensions

            response = client.embeddings.create(**request_kwargs)

            vectors = [item.embedding for item in response.data]
            if len(vectors) != len(texts):
                raise ValueError(
                    f"Embedding response count mismatch: expected {len(texts)}, got {len(vectors)}"
                )

            return vectors

        except Exception as exc:
            last_error = exc
            logger.warning(
                "Embedding request failed on attempt %s/%s: %s",
                attempt,
                config.max_retries,
                exc,
            )
            if attempt < config.max_retries:
                sleep_time = config.retry_sleep_seconds * attempt
                time.sleep(sleep_time)

    raise RuntimeError(f"Embedding request failed after retries: {last_error}") from last_error


# =========================================================
# Record shaping
# =========================================================
def build_embedding_record(
    chunk_record: Dict[str, Any],
    vector: List[float],
    config: EmbeddingConfig,
) -> Dict[str, Any]:
    metadata = {
        "chunk_id": chunk_record["chunk_id"],
        "source_document_id": chunk_record["source_document_id"],
        "chunk_index": chunk_record["chunk_index"],
        "document_title": chunk_record.get("document_title"),
        "document_type": chunk_record.get("document_type"),
        "department": chunk_record.get("department"),
        "business_domain": chunk_record.get("business_domain"),
        "region_scope": chunk_record.get("region_scope"),
        "owner_role": chunk_record.get("owner_role"),
        "topic": chunk_record.get("topic"),
        "heading_path": chunk_record.get("heading_path"),
        "section_title": chunk_record.get("section_title"),
        "keyword_tags": chunk_record.get("keyword_tags", []),
        "effective_date": chunk_record.get("effective_date"),
        "review_date": chunk_record.get("review_date"),
        "version": chunk_record.get("version"),
        "confidentiality_level": chunk_record.get("confidentiality_level"),
        "document_status": chunk_record.get("document_status"),
        "approval_level": chunk_record.get("approval_level"),
        "source_system": chunk_record.get("source_system"),
        "company_name": chunk_record.get("company_name"),
        "source_path": chunk_record.get("source_path"),
        "related_structured_domains": chunk_record.get("related_structured_domains", []),
        "chunk_text": chunk_record["chunk_text"],
    }

    record = {
        "id": chunk_record["chunk_id"],
        "values": vector,
        "metadata": metadata,
        "text": chunk_record["chunk_text"],
        "embedding_model": config.model_name,
        "embedding_dimensions": len(vector),
    }

    if config.namespace:
        record["namespace"] = config.namespace

    return record


def validate_embedding_records(records: List[Dict[str, Any]]) -> Tuple[int, int]:
    if not records:
        raise ValueError("No embedding records to validate.")

    dimensions = len(records[0]["values"])
    if dimensions <= 0:
        raise ValueError("Embedding dimension must be positive.")

    for record in records:
        vector = record.get("values")
        if not isinstance(vector, list) or not vector:
            raise ValueError(f"Invalid vector for record {record.get('id')}")

        if len(vector) != dimensions:
            raise ValueError(
                f"Inconsistent embedding dimension for record {record.get('id')}: "
                f"expected {dimensions}, got {len(vector)}"
            )

    return len(records), dimensions


# =========================================================
# Output
# =========================================================
def write_jsonl(records: Iterable[Dict[str, Any]], path: Path) -> int:
    ensure_dir(path.parent)
    count = 0

    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1

    return count


def write_csv(records: List[Dict[str, Any]], path: Path) -> None:
    ensure_dir(path.parent)

    flattened_rows: List[Dict[str, Any]] = []
    for record in records:
        flattened_rows.append(
            {
                "id": record["id"],
                "embedding_model": record["embedding_model"],
                "embedding_dimensions": record["embedding_dimensions"],
                "namespace": record.get("namespace"),
                "source_document_id": record["metadata"].get("source_document_id"),
                "chunk_index": record["metadata"].get("chunk_index"),
                "document_title": record["metadata"].get("document_title"),
                "document_type": record["metadata"].get("document_type"),
                "department": record["metadata"].get("department"),
                "business_domain": record["metadata"].get("business_domain"),
                "region_scope": record["metadata"].get("region_scope"),
                "topic": record["metadata"].get("topic"),
                "heading_path": record["metadata"].get("heading_path"),
                "source_path": record["metadata"].get("source_path"),
                "text": record["text"],
            }
        )

    df = pd.DataFrame(flattened_rows)
    df.to_csv(path, index=False)


def write_manifest(
    path: Path,
    *,
    input_chunks_path: Path,
    output_jsonl_path: Path,
    output_csv_path: Path,
    model_name: str,
    dimensions: int,
    total_records: int,
    namespace: str | None,
) -> None:
    ensure_dir(path.parent)

    manifest = {
        "input_chunks_path": str(input_chunks_path),
        "output_embeddings_jsonl_path": str(output_jsonl_path),
        "output_embeddings_csv_path": str(output_csv_path),
        "embedding_model": model_name,
        "embedding_dimensions": dimensions,
        "total_embedding_records": total_records,
        "namespace": namespace,
    }

    with path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


# =========================================================
# CLI
# =========================================================
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate embeddings for EDIP RAG document chunks."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to rag_ingestion_config.yaml",
    )
    parser.add_argument(
        "--input-jsonl",
        type=Path,
        default=DEFAULT_CHUNKS_JSONL,
        help="Path to document_chunks.jsonl",
    )
    parser.add_argument(
        "--output-jsonl",
        type=Path,
        default=None,
        help="Optional override for chunk_embeddings.jsonl",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Optional override for chunk_embeddings.csv",
    )
    parser.add_argument(
        "--manifest-json",
        type=Path,
        default=None,
        help="Optional override for embedding_manifest.json",
    )
    return parser.parse_args()


# =========================================================
# Main
# =========================================================
def main() -> None:
    setup_logging()
    args = parse_args()

    paths = build_default_paths()
    config = load_yaml(args.config)
    embed_config = resolve_embedding_config(config)

    input_jsonl = args.input_jsonl
    output_jsonl = args.output_jsonl or paths.embeddings_jsonl
    output_csv = args.output_csv or paths.embeddings_csv
    manifest_json = args.manifest_json or paths.manifest_json

    chunk_records = load_jsonl(input_jsonl)
    validate_chunk_records(chunk_records)

    logger.info("Loaded chunk records: %s", len(chunk_records))
    logger.info("Embedding model: %s", embed_config.model_name)

    client = build_openai_client()

    embedding_records: List[Dict[str, Any]] = []

    for batch in batched(chunk_records, embed_config.batch_size):
        texts = [str(row["chunk_text"]) for row in batch]
        vectors = request_embeddings_with_retry(
            client=client,
            texts=texts,
            config=embed_config,
        )

        for chunk_record, vector in zip(batch, vectors):
            embedding_records.append(
                build_embedding_record(
                    chunk_record=chunk_record,
                    vector=vector,
                    config=embed_config,
                )
            )

    total_records, dimensions = validate_embedding_records(embedding_records)

    jsonl_count = write_jsonl(embedding_records, output_jsonl)
    write_csv(embedding_records, output_csv)
    write_manifest(
        manifest_json,
        input_chunks_path=input_jsonl,
        output_jsonl_path=output_jsonl,
        output_csv_path=output_csv,
        model_name=embed_config.model_name,
        dimensions=dimensions,
        total_records=total_records,
        namespace=embed_config.namespace,
    )

    logger.info("Embeddings written to JSONL: %s", output_jsonl)
    logger.info("Embeddings written to CSV: %s", output_csv)
    logger.info("Manifest written to: %s", manifest_json)
    logger.info("Total embedding records: %s", jsonl_count)
    logger.info("Embedding dimensions: %s", dimensions)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.error("Embedding failed: %s", exc)
        raise
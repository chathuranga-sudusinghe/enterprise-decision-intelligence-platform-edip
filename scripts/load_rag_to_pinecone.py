from __future__ import annotations

import argparse
import json
import logging
import math
import os
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import yaml
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec


# =========================================================
# Logging
# =========================================================
logger = logging.getLogger("load_rag_to_pinecone")


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
DEFAULT_EMBEDDINGS_JSONL = PROJECT_ROOT / "data" / "processed" / "rag" / "chunk_embeddings.jsonl"
DEFAULT_MANIFEST_JSON = PROJECT_ROOT / "data" / "processed" / "rag" / "embedding_manifest.json"
DEFAULT_NAMESPACE = "edip-phase-6"
DEFAULT_METRIC = "cosine"
DEFAULT_CLOUD = "aws"
DEFAULT_REGION = "us-east-1"
DEFAULT_BATCH_SIZE = 50
DEFAULT_WAIT_SECONDS = 2.0


# =========================================================
# Helpers
# =========================================================
def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing YAML config file: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc


def resolve_nested(config: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    current: Any = config
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def get_pinecone_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Supports a few config shapes safely.
    """
    index_name = (
        resolve_nested(config, ["pinecone", "index_name"])
        or resolve_nested(config, ["vector_store", "index_name"])
        or resolve_nested(config, ["retrieval", "pinecone_index_name"])
        or "edip-rag-index"
    )

    namespace = (
        resolve_nested(config, ["pinecone", "namespace"])
        or resolve_nested(config, ["vector_store", "namespace"])
        or DEFAULT_NAMESPACE
    )

    metric = (
        resolve_nested(config, ["pinecone", "metric"])
        or resolve_nested(config, ["vector_store", "metric"])
        or DEFAULT_METRIC
    )

    cloud = (
        resolve_nested(config, ["pinecone", "cloud"])
        or resolve_nested(config, ["vector_store", "cloud"])
        or DEFAULT_CLOUD
    )

    region = (
        resolve_nested(config, ["pinecone", "region"])
        or resolve_nested(config, ["vector_store", "region"])
        or DEFAULT_REGION
    )

    batch_size = int(
        resolve_nested(config, ["pinecone", "batch_size"], DEFAULT_BATCH_SIZE)
        or DEFAULT_BATCH_SIZE
    )

    wait_seconds = float(
        resolve_nested(config, ["pinecone", "wait_seconds"], DEFAULT_WAIT_SECONDS)
        or DEFAULT_WAIT_SECONDS
    )

    return {
        "index_name": str(index_name),
        "namespace": str(namespace),
        "metric": str(metric),
        "cloud": str(cloud),
        "region": str(region),
        "batch_size": batch_size,
        "wait_seconds": wait_seconds,
    }


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required JSON file not found: {path}")

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing embeddings file: {path}. Run embed_rag_chunks.py first."
        )

    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON line in {path} at line {line_number}: {exc}"
                ) from exc

    if not records:
        raise ValueError(f"No embedding records found in {path}")

    return records


def build_pinecone_client() -> Pinecone:   # Pinecone client initialization with error handling for missing API key
    load_dotenv()

    api_key = os.getenv("PINECONE_API_KEY")                  
    if not api_key:
        raise EnvironmentError(
            "PINECONE_API_KEY is not set. Add it to environment before loading vectors."
        )

    return Pinecone(api_key=api_key)


def sanitize_metadata_value(value: Any) -> Any:
    """
    Pinecone metadata should be JSON-serializable simple values.
    """
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return value

    if isinstance(value, list):
        clean_list: List[Any] = []
        for item in value:
            if isinstance(item, (str, int, float, bool)):
                if isinstance(item, float) and (math.isnan(item) or math.isinf(item)):
                    continue
                clean_list.append(item)
            elif item is not None:
                clean_list.append(str(item))
        return clean_list

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)

    return str(value)


def build_metadata(record: Dict[str, Any]) -> Dict[str, Any]:
    metadata_fields = [
        "source_document_id",
        "chunk_index",
        "document_type",
        "department",
        "business_domain",
        "region_scope",
        "owner_role",
        "topic",
        "heading_path",
        "section_title",
        "chunk_word_count",
        "keyword_tags",
        "effective_date",
        "review_date",
        "version",
        "confidentiality_level",
        "document_status",
        "approval_level",
        "source_system",
        "company_name",
        "source_path",
        "document_title",
        "related_structured_domains",
    ]

    metadata: Dict[str, Any] = {}

    for field in metadata_fields:
        if field in record:
            cleaned = sanitize_metadata_value(record[field])
            if cleaned is not None:
                metadata[field] = cleaned

    return metadata


def validate_embedding_record(
    record: Dict[str, Any],
    expected_dimension: int | None = None,
) -> Tuple[str, List[float], Dict[str, Any]]:
    # -----------------------------------------------------
    # Resolve chunk_id from multiple possible shapes
    # -----------------------------------------------------
    chunk_id = record.get("chunk_id")

    if not chunk_id:
        chunk_id = record.get("id")

    if not chunk_id:
        chunk_id = record.get("record_id")

    nested_metadata = record.get("metadata")
    if not chunk_id and isinstance(nested_metadata, dict):
        chunk_id = nested_metadata.get("chunk_id")

    if not chunk_id:
        source_document_id = (
            record.get("source_document_id")
            or (nested_metadata.get("source_document_id") if isinstance(nested_metadata, dict) else None)
        )
        chunk_index = (
            record.get("chunk_index")
            or (nested_metadata.get("chunk_index") if isinstance(nested_metadata, dict) else None)
        )

        if source_document_id and chunk_index is not None:
            chunk_id = f"{source_document_id}-chunk-{int(chunk_index):04d}"

    if not chunk_id or not isinstance(chunk_id, str) or not chunk_id.strip():
        raise ValueError(
            f"Embedding record is missing a usable chunk_id. Available keys: {list(record.keys())}"
        )

    chunk_id = chunk_id.strip()

    # -----------------------------------------------------
    # Resolve embedding vector
    # -----------------------------------------------------
    embedding = record.get("embedding")
    if embedding is None:
        embedding = record.get("values")

    if not isinstance(embedding, list) or not embedding:
        raise ValueError(f"Embedding record {chunk_id} has missing or invalid embedding vector.")

    try:
        vector = [float(x) for x in embedding]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Embedding record {chunk_id} contains non-numeric vector values.") from exc

    if expected_dimension is not None and len(vector) != expected_dimension:
        raise ValueError(
            f"Embedding record {chunk_id} dimension mismatch: expected {expected_dimension}, got {len(vector)}."
        )

    # -----------------------------------------------------
    # Merge metadata from top-level + nested metadata
    # -----------------------------------------------------
    merged_record = dict(record)
    if isinstance(nested_metadata, dict):
        for key, value in nested_metadata.items():
            merged_record.setdefault(key, value)

    merged_record["chunk_id"] = chunk_id

    metadata = build_metadata(merged_record)
    return chunk_id, vector, metadata


def extract_dimension(records: List[Dict[str, Any]], manifest: Dict[str, Any]) -> int:
    manifest_dim = manifest.get("embedding_dimensions")
    if manifest_dim is not None:
        return int(manifest_dim)

    first_embedding = records[0].get("embedding")
    if not isinstance(first_embedding, list) or not first_embedding:
        raise ValueError("Cannot determine embedding dimension from records.")
    return len(first_embedding)


def ensure_index(
    client: Pinecone,
    index_name: str,
    dimension: int,
    metric: str,
    cloud: str,
    region: str,
) -> None:
    existing_indexes = {idx["name"] for idx in client.list_indexes()}

    if index_name in existing_indexes:
        logger.info("Pinecone index already exists: %s", index_name)
        return

    logger.info(
        "Creating Pinecone index: %s | dimension=%s | metric=%s | cloud=%s | region=%s",
        index_name,
        dimension,
        metric,
        cloud,
        region,
    )
    client.create_index(
        name=index_name,
        dimension=dimension,
        metric=metric,
        spec=ServerlessSpec(cloud=cloud, region=region),
    )


def wait_for_index_ready(client: Pinecone, index_name: str, wait_seconds: float) -> None:
    logger.info("Waiting for index readiness: %s", index_name)

    while True:
        description = client.describe_index(index_name)
        status = getattr(description, "status", None)

        ready = False
        if isinstance(status, dict):
            ready = bool(status.get("ready"))
        elif hasattr(status, "ready"):
            ready = bool(status.ready)

        if ready:
            logger.info("Index is ready: %s", index_name)
            return

        time.sleep(wait_seconds)


def chunked(items: List[Any], size: int) -> Iterable[List[Any]]:
    for start in range(0, len(items), size):
        yield items[start:start + size]


def build_vectors(
    records: List[Dict[str, Any]],
    expected_dimension: int,
) -> List[Dict[str, Any]]:
    seen_ids: set[str] = set()
    vectors: List[Dict[str, Any]] = []

    for record in records:
        chunk_id, vector, metadata = validate_embedding_record(
            record=record,
            expected_dimension=expected_dimension,
        )

        if chunk_id in seen_ids:
            raise ValueError(f"Duplicate chunk_id detected in embeddings file: {chunk_id}")
        seen_ids.add(chunk_id)

        vectors.append(
            {
                "id": chunk_id,
                "values": vector,
                "metadata": metadata,
            }
        )

    return vectors


def write_load_manifest(
    output_path: Path,
    *,
    index_name: str,
    namespace: str,
    total_vectors: int,
    embedding_dimension: int,
) -> None:
    ensure_dir(output_path.parent)

    payload = {
        "index_name": index_name,
        "namespace": namespace,
        "total_vectors_loaded": total_vectors,
        "embedding_dimension": embedding_dimension,
        "loaded_at_epoch": int(time.time()),
    }

    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# =========================================================
# CLI
# =========================================================
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load EDIP chunk embeddings into Pinecone."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to rag_ingestion_config.yaml",
    )
    parser.add_argument(
        "--embeddings-jsonl",
        type=Path,
        default=DEFAULT_EMBEDDINGS_JSONL,
        help="Path to chunk_embeddings.jsonl",
    )
    parser.add_argument(
        "--manifest-json",
        type=Path,
        default=DEFAULT_MANIFEST_JSON,
        help="Path to embedding_manifest.json",
    )
    parser.add_argument(
        "--namespace",
        type=str,
        default=None,
        help="Optional Pinecone namespace override",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Optional upsert batch size override",
    )
    return parser.parse_args()


# =========================================================
# Main
# =========================================================
def main() -> None:
    setup_logging()

    args = parse_args()
    config = load_yaml(args.config)
    pinecone_cfg = get_pinecone_config(config)

    namespace = args.namespace or pinecone_cfg["namespace"]
    batch_size = args.batch_size or pinecone_cfg["batch_size"]

    if batch_size <= 0:
        raise ValueError("batch_size must be a positive integer.")

    manifest = load_json(args.manifest_json)
    embedding_records = load_jsonl(args.embeddings_jsonl)

    logger.info("Loaded embedding records: %s", len(embedding_records))

    dimension = extract_dimension(embedding_records, manifest)
    logger.info("Embedding dimension: %s", dimension)

    client = build_pinecone_client()

    ensure_index(
        client=client,
        index_name=pinecone_cfg["index_name"],
        dimension=dimension,
        metric=pinecone_cfg["metric"],
        cloud=pinecone_cfg["cloud"],
        region=pinecone_cfg["region"],
    )

    wait_for_index_ready(
        client=client,
        index_name=pinecone_cfg["index_name"],
        wait_seconds=pinecone_cfg["wait_seconds"],
    )

    index = client.Index(pinecone_cfg["index_name"])
    vectors = build_vectors(
        records=embedding_records,
        expected_dimension=dimension,
    )

    logger.info(
        "Starting upsert to Pinecone | index=%s | namespace=%s | vectors=%s | batch_size=%s",
        pinecone_cfg["index_name"],
        namespace,
        len(vectors),
        batch_size,
    )

    total_upserted = 0
    for batch_number, batch in enumerate(chunked(vectors, batch_size), start=1):
        index.upsert(vectors=batch, namespace=namespace)
        total_upserted += len(batch)
        logger.info(
            "Upserted batch %s | batch_size=%s | total_upserted=%s",
            batch_number,
            len(batch),
            total_upserted,
        )

    stats = index.describe_index_stats()
    logger.info("Pinecone index stats: %s", stats)

    load_manifest_path = PROJECT_ROOT / "data" / "processed" / "rag" / "pinecone_load_manifest.json"
    write_load_manifest(
        output_path=load_manifest_path,
        index_name=pinecone_cfg["index_name"],
        namespace=namespace,
        total_vectors=total_upserted,
        embedding_dimension=dimension,
    )

    logger.info("Pinecone load manifest written to: %s", load_manifest_path)
    logger.info("Pinecone load complete. Total vectors upserted: %s", total_upserted)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.error("Pinecone load failed: %s", exc)
        raise
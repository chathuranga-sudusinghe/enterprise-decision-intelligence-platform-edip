from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone


# =========================================================
# Logging
# =========================================================
logger = logging.getLogger("test_rag_retrieval")


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


# =========================================================
# Paths / defaults
# =========================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "rag_ingestion_config.yaml"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "rag" / "retrieval_test_results.json"
DEFAULT_TOP_K = 5


# =========================================================
# Helpers
# =========================================================
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


def get_embedding_model(config: Dict[str, Any]) -> str:
    return (
        resolve_nested(config, ["embedding", "model"])
        or resolve_nested(config, ["embeddings", "model"])
        or "text-embedding-3-small"
    )


def get_pinecone_config(config: Dict[str, Any]) -> Dict[str, Any]:
    index_name = (
        resolve_nested(config, ["pinecone", "index_name"])
        or resolve_nested(config, ["vector_store", "index_name"])
        or resolve_nested(config, ["retrieval", "pinecone_index_name"])
        or "edip-rag-index"
    )

    namespace = (
        resolve_nested(config, ["pinecone", "namespace"])
        or resolve_nested(config, ["vector_store", "namespace"])
        or "edip-phase-6"
    )

    top_k = int(
        resolve_nested(config, ["retrieval", "top_k"], DEFAULT_TOP_K)
        or DEFAULT_TOP_K
    )

    return {
        "index_name": str(index_name),
        "namespace": str(namespace),
        "top_k": top_k,
    }


def build_openai_client() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Add it to environment before running retrieval tests."
        )

    return OpenAI(api_key=api_key)


def build_pinecone_client() -> Pinecone:
    load_dotenv()
    api_key = os.getenv("PINECONE_API_KEY")

    if not api_key:
        raise EnvironmentError(
            "PINECONE_API_KEY is not set. Add it to environment before running retrieval tests."
        )

    return Pinecone(api_key=api_key)


def embed_query(client: OpenAI, model: str, query_text: str) -> List[float]:
    response = client.embeddings.create(
        model=model,
        input=query_text,
    )
    return list(response.data[0].embedding)


def safe_metadata(metadata: Dict[str, Any] | None) -> Dict[str, Any]:
    return metadata if isinstance(metadata, dict) else {}


def simplify_match(match: Any) -> Dict[str, Any]:
    metadata = safe_metadata(getattr(match, "metadata", None))

    return {
        "id": getattr(match, "id", None),
        "score": getattr(match, "score", None),
        "document_type": metadata.get("document_type"),
        "business_domain": metadata.get("business_domain"),
        "region_scope": metadata.get("region_scope"),
        "owner_role": metadata.get("owner_role"),
        "topic": metadata.get("topic"),
        "source_document_id": metadata.get("source_document_id"),
        "section_title": metadata.get("section_title"),
        "heading_path": metadata.get("heading_path"),
        "document_title": metadata.get("document_title"),
        "source_path": metadata.get("source_path"),
        "version": metadata.get("version"),
        "confidentiality_level": metadata.get("confidentiality_level"),
    }


def query_pinecone(
    *,
    index: Any,
    vector: List[float],
    namespace: str,
    top_k: int,
    metadata_filter: Dict[str, Any] | None = None,
) -> Tuple[int, List[Dict[str, Any]]]:
    response = index.query(
        vector=vector,
        namespace=namespace,
        top_k=top_k,
        include_metadata=True,
        filter=metadata_filter,
    )

    matches = getattr(response, "matches", []) or []
    results = [simplify_match(match) for match in matches]
    return len(results), results


def ensure_output_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    ensure_output_dir(path)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def validate_basic_result_shape(results: List[Dict[str, Any]]) -> List[str]:
    issues: List[str] = []

    for idx, item in enumerate(results, start=1):
        if not item.get("id"):
            issues.append(f"Result {idx} missing id.")
        if item.get("score") is None:
            issues.append(f"Result {idx} missing score.")
        if not item.get("source_document_id"):
            issues.append(f"Result {idx} missing source_document_id.")
        if not item.get("document_type"):
            issues.append(f"Result {idx} missing document_type.")
        if not item.get("business_domain"):
            issues.append(f"Result {idx} missing business_domain.")
        if not item.get("region_scope"):
            issues.append(f"Result {idx} missing region_scope.")
        if not item.get("topic"):
            issues.append(f"Result {idx} missing topic.")

    return issues


def validate_filter_match(
    results: List[Dict[str, Any]],
    expected_pairs: Dict[str, Any],
) -> List[str]:
    issues: List[str] = []

    for idx, item in enumerate(results, start=1):
        for key, expected_value in expected_pairs.items():
            actual_value = item.get(key)
            if actual_value != expected_value:
                issues.append(
                    f"Result {idx} failed filter validation for '{key}': "
                    f"expected '{expected_value}', got '{actual_value}'."
                )

    return issues


def run_single_test_case(
    *,
    test_name: str,
    query_text: str,
    openai_client: OpenAI,
    embedding_model: str,
    pinecone_index: Any,
    namespace: str,
    top_k: int,
    metadata_filter: Dict[str, Any] | None = None,
    expected_filter_fields: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    logger.info("Running retrieval test: %s", test_name)

    query_vector = embed_query(
        client=openai_client,
        model=embedding_model,
        query_text=query_text,
    )

    result_count, results = query_pinecone(
        index=pinecone_index,
        vector=query_vector,
        namespace=namespace,
        top_k=top_k,
        metadata_filter=metadata_filter,
    )

    issues = validate_basic_result_shape(results)

    if expected_filter_fields:
        issues.extend(validate_filter_match(results, expected_filter_fields))

    status = "pass"
    if result_count == 0:
        status = "fail"
        issues.append("No retrieval results returned.")
    elif issues:
        status = "fail"

    return {
        "test_name": test_name,
        "query": query_text,
        "namespace": namespace,
        "top_k": top_k,
        "filter": metadata_filter,
        "result_count": result_count,
        "status": status,
        "issues": issues,
        "results": results,
    }


def build_default_test_cases() -> List[Dict[str, Any]]:
    """
    These are aligned to your EDIP NorthStar document set and retrieval fields.
    """
    return [
        {
            "test_name": "policy_retrieval_replenishment",
            "query": "What is the replenishment policy for service level and safety stock in NorthStar?",
            "filter": {"document_type": "policy", "business_domain": "replenishment"},
            "expected_filter_fields": {
                "document_type": "policy",
                "business_domain": "replenishment",
            },
        },
        {
            "test_name": "sop_retrieval_warehouse",
            "query": "What steps should warehouse teams follow during receiving and inbound handling?",
            "filter": {"document_type": "sop", "business_domain": "warehouse"},
            "expected_filter_fields": {
                "document_type": "sop",
                "business_domain": "warehouse",
            },
        },
        {
            "test_name": "playbook_retrieval_overrides",
            "query": "How should planners handle override decisions and repeated override patterns?",
            "filter": {"document_type": "playbook"},
            "expected_filter_fields": {
                "document_type": "playbook",
            },
        },
        {
            "test_name": "guide_retrieval_supplier_delay",
            "query": "What should NorthStar do when supplier delays increase stockout risk?",
            "filter": {"document_type": "guide"},
            "expected_filter_fields": {
                "document_type": "guide",
            },
        },
        {
            "test_name": "enterprise_scope_filter",
            "query": "Show enterprise-wide decision guidance for escalation and replenishment exceptions.",
            "filter": {"region_scope": "enterprise"},
            "expected_filter_fields": {
                "region_scope": "enterprise",
            },
        },
    ]


# =========================================================
# CLI
# =========================================================
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run EDIP Phase 6 RAG retrieval integration tests."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to rag_ingestion_config.yaml",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path to write retrieval test results JSON",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Optional top-k override",
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
    embedding_model = get_embedding_model(config)

    top_k = args.top_k or pinecone_cfg["top_k"]
    if top_k <= 0:
        raise ValueError("top_k must be a positive integer.")

    openai_client = build_openai_client()
    pinecone_client = build_pinecone_client()

    index = pinecone_client.Index(pinecone_cfg["index_name"])

    logger.info("Using embedding model: %s", embedding_model)
    logger.info(
        "Testing Pinecone retrieval | index=%s | namespace=%s | top_k=%s",
        pinecone_cfg["index_name"],
        pinecone_cfg["namespace"],
        top_k,
    )

    test_cases = build_default_test_cases()
    all_results: List[Dict[str, Any]] = []

    for case in test_cases:
        result = run_single_test_case(
            test_name=case["test_name"],
            query_text=case["query"],
            openai_client=openai_client,
            embedding_model=embedding_model,
            pinecone_index=index,
            namespace=pinecone_cfg["namespace"],
            top_k=top_k,
            metadata_filter=case.get("filter"),
            expected_filter_fields=case.get("expected_filter_fields"),
        )
        all_results.append(result)

        logger.info(
            "Test complete | name=%s | status=%s | result_count=%s",
            result["test_name"],
            result["status"],
            result["result_count"],
        )

        if result["issues"]:
            for issue in result["issues"]:
                logger.warning("Issue | %s | %s", result["test_name"], issue)

    passed = sum(1 for item in all_results if item["status"] == "pass")
    failed = sum(1 for item in all_results if item["status"] == "fail")

    summary = {
        "project": "EDIP",
        "phase": "phase_6_rag_retrieval_validation",
        "index_name": pinecone_cfg["index_name"],
        "namespace": pinecone_cfg["namespace"],
        "embedding_model": embedding_model,
        "top_k": top_k,
        "tests_run": len(all_results),
        "tests_passed": passed,
        "tests_failed": failed,
        "overall_status": "pass" if failed == 0 else "fail",
        "results": all_results,
    }

    write_json(args.output, summary)

    logger.info("Retrieval test results written to: %s", args.output)
    logger.info(
        "Retrieval validation complete | passed=%s | failed=%s | overall_status=%s",
        passed,
        failed,
        summary["overall_status"],
    )

    if failed > 0:
        raise RuntimeError(
            f"Retrieval validation failed. Passed={passed}, Failed={failed}. "
            f"Check results file: {args.output}"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.error("Retrieval test failed: %s", exc)
        raise
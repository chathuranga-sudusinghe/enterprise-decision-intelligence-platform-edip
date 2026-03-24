# tests/integration/test_kafka_event_generation.py

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import pandas as pd
import pytest
import yaml


# =========================================================
# Paths / Constants
# =========================================================
@dataclass(frozen=True)
class Paths:
    project_root: Path
    config_path: Path
    output_dir: Path


def build_paths() -> Paths:
    project_root = Path(__file__).resolve().parents[2]
    return Paths(
        project_root=project_root,
        config_path=project_root / "configs" / "kafka_event_schema.yaml",
        output_dir=project_root / "data" / "exports" / "kafka_events",
    )


TOPIC_OUTPUT_FILES: Dict[str, str] = {
    "sales.order.created": "sales.order.created.jsonl",
    "sales.order.completed": "sales.order.completed.jsonl",
    "inventory.stock.updated": "inventory.stock.updated.jsonl",
    "inventory.low_stock.alert": "inventory.low_stock.alert.jsonl",
    "logistics.shipment.delayed": "logistics.shipment.delayed.jsonl",
    "returns.return.created": "returns.return.created.jsonl",
    "planning.forecast.generated": "planning.forecast.generated.jsonl",
    "planning.replenishment.approved": "planning.replenishment.approved.jsonl",
}


# =========================================================
# Helpers
# =========================================================
def load_yaml_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Kafka schema config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("Kafka schema config must load as a dictionary.")

    return config


def read_jsonl_file(file_path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []

    with file_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()

            # Skip empty lines safely.
            if not stripped:
                continue

            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise AssertionError(
                    f"Invalid JSON in {file_path.name} at line {line_number}: {exc}"
                ) from exc

            if not isinstance(record, dict):
                raise AssertionError(
                    f"Each JSONL row must be an object/dict in {file_path.name}, line {line_number}."
                )

            records.append(record)

    return records


def parse_timestamp_or_fail(value: Any, context: str) -> None:
    try:
        pd.to_datetime(value, utc=True, errors="raise")
    except Exception as exc:
        raise AssertionError(f"Invalid event_timestamp for {context}: {value}") from exc


def safe_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        if pd.isna(value):
            return default
    except TypeError:
        pass

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        if pd.isna(value):
            return default
    except TypeError:
        pass

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except TypeError:
        pass
    return str(value)


def event_context(file_name: str, index: int) -> str:
    return f"{file_name} event #{index}"


def assert_required_envelope_fields(
    event: Dict[str, Any],
    required_fields: Iterable[str],
    context: str,
) -> None:
    for field_name in required_fields:
        assert field_name in event, f"Missing required field '{field_name}' in {context}"

    # Basic non-null checks for critical fields.
    for field_name in [
        "event_id",
        "event_type",
        "event_timestamp",
        "source_system",
        "entity_type",
        "entity_id",
        "schema_version",
    ]:
        assert event.get(field_name) not in (None, ""), (
            f"Critical field '{field_name}' is empty in {context}"
        )

    assert isinstance(event.get("payload_json"), dict), (
        f"'payload_json' must be a dictionary in {context}"
    )


# =========================================================
# Pytest fixtures
# =========================================================
@pytest.fixture(scope="module")
def paths() -> Paths:
    return build_paths()


@pytest.fixture(scope="module")
def kafka_config(paths: Paths) -> Dict[str, Any]:
    return load_yaml_config(paths.config_path)


@pytest.fixture(scope="module")
def required_fields(kafka_config: Dict[str, Any]) -> List[str]:
    fields = kafka_config.get("required_envelope_fields", [])
    assert isinstance(fields, list) and fields, "required_envelope_fields must be a non-empty list."
    return fields


@pytest.fixture(scope="module")
def topics_cfg(kafka_config: Dict[str, Any]) -> Dict[str, Any]:
    topics = kafka_config.get("topics", {})
    assert isinstance(topics, dict) and topics, "topics config must be a non-empty dictionary."
    return topics


@pytest.fixture(scope="module")
def topic_records(paths: Paths) -> Dict[str, List[Dict[str, Any]]]:
    all_records: Dict[str, List[Dict[str, Any]]] = {}

    for topic, file_name in TOPIC_OUTPUT_FILES.items():
        file_path = paths.output_dir / file_name
        assert file_path.exists(), f"Expected Kafka JSONL file not found: {file_path}"
        all_records[topic] = read_jsonl_file(file_path)

    return all_records


# =========================================================
# Core validation tests
# =========================================================
def test_expected_topic_files_exist(paths: Paths) -> None:
    for topic, file_name in TOPIC_OUTPUT_FILES.items():
        file_path = paths.output_dir / file_name
        assert file_path.exists(), f"Missing output file for topic '{topic}': {file_path}"


def test_config_topics_match_expected_topic_files(topics_cfg: Dict[str, Any]) -> None:
    config_topics = set(topics_cfg.keys())
    expected_topics = set(TOPIC_OUTPUT_FILES.keys())

    assert config_topics == expected_topics, (
        "Kafka config topics and expected output topics do not match."
    )


@pytest.mark.parametrize("topic,file_name", list(TOPIC_OUTPUT_FILES.items()))
def test_jsonl_file_is_readable(
    paths: Paths,
    topic: str,
    file_name: str,
) -> None:
    file_path = paths.output_dir / file_name
    records = read_jsonl_file(file_path)
    assert isinstance(records, list), f"Records must load as a list for topic '{topic}'."


@pytest.mark.parametrize("topic,file_name", list(TOPIC_OUTPUT_FILES.items()))
def test_all_events_have_required_envelope_fields(
    paths: Paths,
    required_fields: List[str],
    topic: str,
    file_name: str,
) -> None:
    file_path = paths.output_dir / file_name
    records = read_jsonl_file(file_path)

    for index, event in enumerate(records, start=1):
        context = event_context(file_name, index)
        assert_required_envelope_fields(event, required_fields, context)


@pytest.mark.parametrize("topic,file_name", list(TOPIC_OUTPUT_FILES.items()))
def test_event_type_matches_topic_file(
    paths: Paths,
    topic: str,
    file_name: str,
) -> None:
    file_path = paths.output_dir / file_name
    records = read_jsonl_file(file_path)

    for index, event in enumerate(records, start=1):
        context = event_context(file_name, index)
        assert event["event_type"] == topic, (
            f"event_type mismatch in {context}: expected '{topic}', got '{event['event_type']}'"
        )


@pytest.mark.parametrize("topic,file_name", list(TOPIC_OUTPUT_FILES.items()))
def test_event_id_is_unique_within_each_topic_file(
    paths: Paths,
    topic: str,
    file_name: str,
) -> None:
    file_path = paths.output_dir / file_name
    records = read_jsonl_file(file_path)

    event_ids: List[str] = [safe_str(event.get("event_id")) for event in records]
    unique_ids: Set[str] = set(event_ids)

    assert len(event_ids) == len(unique_ids), (
        f"Duplicate event_id values found in topic '{topic}'."
    )


@pytest.mark.parametrize("topic,file_name", list(TOPIC_OUTPUT_FILES.items()))
def test_event_timestamp_is_valid(
    paths: Paths,
    topic: str,
    file_name: str,
) -> None:
    file_path = paths.output_dir / file_name
    records = read_jsonl_file(file_path)

    for index, event in enumerate(records, start=1):
        context = event_context(file_name, index)
        parse_timestamp_or_fail(event.get("event_timestamp"), context)


@pytest.mark.parametrize("topic,file_name", list(TOPIC_OUTPUT_FILES.items()))
def test_payload_json_is_dictionary(
    paths: Paths,
    topic: str,
    file_name: str,
) -> None:
    file_path = paths.output_dir / file_name
    records = read_jsonl_file(file_path)

    for index, event in enumerate(records, start=1):
        context = event_context(file_name, index)
        assert isinstance(event.get("payload_json"), dict), (
            f"payload_json must be a dictionary in {context}"
        )


# =========================================================
# Topic-specific business rule validation
# =========================================================
def test_low_stock_alert_events_only_contain_low_stock_rows(
    topic_records: Dict[str, List[Dict[str, Any]]],
) -> None:
    records = topic_records["inventory.low_stock.alert"]

    for index, event in enumerate(records, start=1):
        payload = event["payload_json"]
        available_qty = safe_float(payload.get("available_qty"), default=0.0)
        reorder_point = safe_float(payload.get("reorder_point"), default=0.0)

        assert reorder_point > 0, (
            f"Low-stock alert event #{index} has invalid reorder_point={reorder_point}."
        )
        assert available_qty <= reorder_point, (
            f"Low-stock alert event #{index} violates rule: "
            f"available_qty={available_qty}, reorder_point={reorder_point}"
        )

        assert payload.get("alert_reason") == "available_qty_below_or_equal_reorder_point", (
            f"Unexpected alert_reason in low-stock alert event #{index}."
        )


def test_delayed_shipment_events_only_contain_delayed_rows(
    topic_records: Dict[str, List[Dict[str, Any]]],
) -> None:
    records = topic_records["logistics.shipment.delayed"]

    for index, event in enumerate(records, start=1):
        payload = event["payload_json"]
        delay_days = safe_int(payload.get("delay_days"), default=0)

        status_candidates = [
            payload.get("shipment_status"),
            payload.get("status"),
            payload.get("delivery_status"),
            payload.get("raw_record", {}).get("shipment_status"),
            payload.get("raw_record", {}).get("status"),
            payload.get("raw_record", {}).get("delivery_status"),
        ]
        status_text = " ".join([safe_str(x).lower() for x in status_candidates if x is not None])

        assert delay_days > 0 or "delay" in status_text, (
            f"Delayed shipment event #{index} does not appear delayed."
        )


def test_approved_replenishment_events_only_contain_approved_rows(
    topic_records: Dict[str, List[Dict[str, Any]]],
) -> None:
    records = topic_records["planning.replenishment.approved"]

    valid_statuses = {"approved", "accepted", "confirmed"}

    for index, event in enumerate(records, start=1):
        payload = event["payload_json"]

        status_candidates = [
            payload.get("approval_status"),
            payload.get("raw_record", {}).get("decision_status"),
            payload.get("raw_record", {}).get("approval_status"),
            payload.get("raw_record", {}).get("recommendation_status"),
            payload.get("raw_record", {}).get("status"),
        ]
        normalized_statuses = {
            safe_str(value).strip().lower()
            for value in status_candidates
            if safe_str(value).strip() != ""
        }

        approved_flag_candidates = [
            payload.get("raw_record", {}).get("approved_flag"),
            payload.get("raw_record", {}).get("is_approved"),
        ]

        approved_flag_found = False
        for value in approved_flag_candidates:
            if safe_str(value).strip().lower() in {"1", "true", "yes", "y"}:
                approved_flag_found = True
                break

        assert approved_flag_found or bool(normalized_statuses & valid_statuses), (
            f"Approved replenishment event #{index} does not appear approved."
        )


# =========================================================
# Optional sanity check
# =========================================================
def test_topic_files_are_not_all_empty(topic_records: Dict[str, List[Dict[str, Any]]]) -> None:
    total_event_count = sum(len(records) for records in topic_records.values())
    assert total_event_count > 0, "All Kafka topic files are empty."
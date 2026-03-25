from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from scripts.kafka_producer import (
    TOPIC_FILES,
    Paths,
    build_paths,
    extract_message_key,
    iter_jsonl_records,
    publish_all_topics,
    send_topic_file,
)


# =========================================================
# Test doubles
# =========================================================
class FakeKafkaFuture:
    """
    Minimal Kafka future stub for producer.send(...).get(...).
    """

    def get(self, timeout: int = 30) -> None:
        # Simulate successful Kafka acknowledgment.
        return None


class FakeKafkaProducer:
    """
    Minimal Kafka producer stub for unit testing send behavior.
    """

    def __init__(self) -> None:
        self.sent_messages: List[Dict[str, Any]] = []

    def send(self, topic: str, key: str | None, value: Dict[str, Any]) -> FakeKafkaFuture:
        self.sent_messages.append(
            {
                "topic": topic,
                "key": key,
                "value": value,
            }
        )
        return FakeKafkaFuture()


# =========================================================
# Tests for path/config helpers
# =========================================================
def test_build_paths_returns_expected_structure() -> None:
    """
    Validate build_paths() returns project_root and kafka_events_dir.
    """
    paths = build_paths()

    assert isinstance(paths, Paths)
    assert isinstance(paths.project_root, Path)
    assert isinstance(paths.kafka_events_dir, Path)
    assert paths.kafka_events_dir == paths.project_root / "data" / "exports" / "kafka_events"


# =========================================================
# Tests for JSONL record reading
# =========================================================
def test_iter_jsonl_records_reads_valid_records(tmp_path: Path) -> None:
    """
    Validate iter_jsonl_records() yields valid JSON records from a JSONL file.
    """
    file_path = tmp_path / "events.jsonl"
    file_path.write_text(
        "\n".join(
            [
                json.dumps({"event_id": "evt-1", "value": 10}),
                json.dumps({"event_id": "evt-2", "value": 20}),
            ]
        ),
        encoding="utf-8",
    )

    records = list(iter_jsonl_records(file_path))

    assert len(records) == 2
    assert records[0]["event_id"] == "evt-1"
    assert records[1]["event_id"] == "evt-2"


def test_iter_jsonl_records_skips_blank_and_invalid_json_lines(tmp_path: Path) -> None:
    """
    Validate iter_jsonl_records() skips blank lines and invalid JSON safely.
    """
    file_path = tmp_path / "events.jsonl"
    file_path.write_text(
        "\n".join(
            [
                json.dumps({"event_id": "evt-1"}),
                "",
                "{invalid-json}",
                json.dumps({"event_id": "evt-2"}),
            ]
        ),
        encoding="utf-8",
    )

    records = list(iter_jsonl_records(file_path))

    assert len(records) == 2
    assert records[0]["event_id"] == "evt-1"
    assert records[1]["event_id"] == "evt-2"


def test_iter_jsonl_records_returns_empty_when_file_missing(tmp_path: Path) -> None:
    """
    Validate iter_jsonl_records() yields no records when file does not exist.
    """
    missing_file = tmp_path / "missing.jsonl"

    records = list(iter_jsonl_records(missing_file))

    assert records == []


# =========================================================
# Tests for message key extraction
# =========================================================
def test_extract_message_key_prefers_event_id() -> None:
    """
    Validate extract_message_key() prefers event_id over entity_id.
    """
    record = {
        "event_id": "evt-100",
        "entity_id": "entity-200",
    }

    assert extract_message_key(record) == "evt-100"


def test_extract_message_key_falls_back_to_entity_id() -> None:
    """
    Validate extract_message_key() falls back to entity_id when event_id is missing.
    """
    record = {
        "entity_id": "entity-200",
    }

    assert extract_message_key(record) == "entity-200"


def test_extract_message_key_returns_none_when_no_supported_key_exists() -> None:
    """
    Validate extract_message_key() returns None when both keys are missing.
    """
    record = {"name": "test"}

    assert extract_message_key(record) is None


# =========================================================
# Tests for topic publishing
# =========================================================
def test_send_topic_file_publishes_all_valid_records(tmp_path: Path) -> None:
    """
    Validate send_topic_file() publishes all valid records successfully.
    """
    producer = FakeKafkaProducer()
    topic = "inventory.low_stock.alert"
    file_path = tmp_path / "inventory.low_stock.alert.jsonl"
    file_path.write_text(
        "\n".join(
            [
                json.dumps({"event_id": "evt-1", "payload": {"x": 1}}),
                json.dumps({"event_id": "evt-2", "payload": {"x": 2}}),
            ]
        ),
        encoding="utf-8",
    )

    success_count, failure_count = send_topic_file(
        producer=producer,
        topic=topic,
        file_path=file_path,
        max_messages=None,
    )

    assert success_count == 2
    assert failure_count == 0
    assert len(producer.sent_messages) == 2
    assert producer.sent_messages[0]["topic"] == topic
    assert producer.sent_messages[0]["key"] == "evt-1"
    assert producer.sent_messages[1]["key"] == "evt-2"


def test_send_topic_file_respects_max_messages_limit(tmp_path: Path) -> None:
    """
    Validate send_topic_file() stops early when max_messages is reached.
    """
    producer = FakeKafkaProducer()
    topic = "inventory.low_stock.alert"
    file_path = tmp_path / "inventory.low_stock.alert.jsonl"
    file_path.write_text(
        "\n".join(
            [
                json.dumps({"event_id": "evt-1"}),
                json.dumps({"event_id": "evt-2"}),
                json.dumps({"event_id": "evt-3"}),
            ]
        ),
        encoding="utf-8",
    )

    success_count, failure_count = send_topic_file(
        producer=producer,
        topic=topic,
        file_path=file_path,
        max_messages=2,
    )

    assert success_count == 2
    assert failure_count == 0
    assert len(producer.sent_messages) == 2
    assert producer.sent_messages[0]["key"] == "evt-1"
    assert producer.sent_messages[1]["key"] == "evt-2"


def test_send_topic_file_returns_zero_counts_when_file_missing(tmp_path: Path) -> None:
    """
    Validate send_topic_file() returns zero counts when the topic file is missing.
    """
    producer = FakeKafkaProducer()
    topic = "inventory.low_stock.alert"
    missing_file = tmp_path / "missing.jsonl"

    success_count, failure_count = send_topic_file(
        producer=producer,
        topic=topic,
        file_path=missing_file,
        max_messages=None,
    )

    assert success_count == 0
    assert failure_count == 0
    assert producer.sent_messages == []


# =========================================================
# Tests for multi-topic publishing
# =========================================================
def test_publish_all_topics_returns_summary_for_each_topic(tmp_path: Path) -> None:
    """
    Validate publish_all_topics() returns a full per-topic summary.
    """
    producer = FakeKafkaProducer()
    kafka_events_dir = tmp_path / "kafka_events"
    kafka_events_dir.mkdir(parents=True, exist_ok=True)

    # Create files for only two topics. Remaining topics should safely return zero counts.
    (kafka_events_dir / TOPIC_FILES["sales.order.created"]).write_text(
        json.dumps({"event_id": "sales-evt-1"}),
        encoding="utf-8",
    )
    (kafka_events_dir / TOPIC_FILES["inventory.low_stock.alert"]).write_text(
        json.dumps({"event_id": "stock-evt-1"}),
        encoding="utf-8",
    )

    paths = Paths(
        project_root=tmp_path,
        kafka_events_dir=kafka_events_dir,
    )

    summary = publish_all_topics(
        producer=producer,
        paths=paths,
        max_messages_per_topic=None,
    )

    assert set(summary.keys()) == set(TOPIC_FILES.keys())
    assert summary["sales.order.created"]["success"] == 1
    assert summary["sales.order.created"]["failed"] == 0
    assert summary["inventory.low_stock.alert"]["success"] == 1
    assert summary["inventory.low_stock.alert"]["failed"] == 0

    # Topics without files should safely return zero counts.
    assert summary["sales.order.completed"]["success"] == 0
    assert summary["sales.order.completed"]["failed"] == 0
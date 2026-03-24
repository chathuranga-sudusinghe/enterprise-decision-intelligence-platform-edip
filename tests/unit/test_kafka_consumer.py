from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from scripts.kafka_consumer import (
    ConsumerRunSummary,
    consume_messages,
    extract_event_id,
    log_summary,
    parse_topics_from_env,
    process_single_message,
)


# =========================================================
# Test doubles
# =========================================================
@dataclass
class FakeProcessingResult:
    """
    Minimal processing result object matching the attributes used by
    scripts.kafka_consumer.process_single_message().
    """

    event_id: str
    status: str
    action_taken: str
    message: str
    decision_payload: Dict[str, Any]
    warnings: List[str]


class FakeEventProcessingService:
    """
    Minimal event-processing service stub for consumer unit tests.
    """

    def __init__(self, result: FakeProcessingResult | None = None) -> None:
        self.result = result
        self.received_events: List[Dict[str, Any]] = []

    def process_event(self, event: Dict[str, Any]) -> FakeProcessingResult:
        self.received_events.append(event)

        if self.result is None:
            return FakeProcessingResult(
                event_id=str(event.get("event_id", "")),
                status="processed",
                action_taken="default_action",
                message="Processed successfully.",
                decision_payload={"event_id": event.get("event_id")},
                warnings=[],
            )

        return self.result


@dataclass
class FakeKafkaMessage:
    """
    Minimal Kafka-like message object used by consume_messages().
    """

    topic: str
    value: Any
    partition: int = 0
    offset: int = 0
    key: str | None = None


class FakeKafkaConsumer:
    """
    Minimal iterable Kafka-like consumer for unit tests.
    """

    def __init__(self, messages: List[FakeKafkaMessage]) -> None:
        self.messages = messages

    def __iter__(self):
        return iter(self.messages)


# =========================================================
# Helpers
# =========================================================
def build_valid_event(event_id: str = "evt-1001") -> Dict[str, Any]:
    """
    Build one valid Kafka event envelope for consumer tests.
    """
    return {
        "event_id": event_id,
        "event_type": "inventory.low_stock.alert",
        "event_timestamp": "2026-03-21T10:00:00+00:00",
        "source_system": "test_suite",
        "entity_type": "inventory_snapshot",
        "entity_id": "inv-1001",
        "region_id": 1,
        "schema_version": "1.0",
        "payload_json": {
            "product_id": 245,
            "sku_code": "SKU-100245",
            "store_id": 3,
            "warehouse_id": "",
            "available_qty": 8,
            "reorder_point": 30,
            "safety_stock": 15,
        },
    }


# =========================================================
# Tests for topic parsing
# =========================================================
def test_parse_topics_from_env_returns_default_when_env_missing(monkeypatch) -> None:
    """
    Validate parse_topics_from_env() returns defaults when env is not set.
    """
    default_topics = ["topic.a", "topic.b"]
    monkeypatch.delenv("KAFKA_CONSUMER_TOPICS", raising=False)

    result = parse_topics_from_env(default_topics)

    assert result == default_topics


def test_parse_topics_from_env_parses_comma_separated_topics(monkeypatch) -> None:
    """
    Validate parse_topics_from_env() parses and trims comma-separated topics.
    """
    default_topics = ["topic.default"]
    monkeypatch.setenv(
        "KAFKA_CONSUMER_TOPICS",
        " inventory.low_stock.alert , sales.order.created , planning.forecast.generated ",
    )

    result = parse_topics_from_env(default_topics)

    assert result == [
        "inventory.low_stock.alert",
        "sales.order.created",
        "planning.forecast.generated",
    ]


def test_parse_topics_from_env_returns_default_for_blank_env(monkeypatch) -> None:
    """
    Validate parse_topics_from_env() returns defaults for blank env values.
    """
    default_topics = ["topic.default"]
    monkeypatch.setenv("KAFKA_CONSUMER_TOPICS", "   ")

    result = parse_topics_from_env(default_topics)

    assert result == default_topics


# =========================================================
# Tests for event id extraction
# =========================================================
def test_extract_event_id_prefers_event_id() -> None:
    """
    Validate extract_event_id() prefers event_id over entity_id.
    """
    payload = {
        "event_id": "evt-123",
        "entity_id": "entity-999",
    }

    assert extract_event_id(payload) == "evt-123"


def test_extract_event_id_falls_back_to_entity_id() -> None:
    """
    Validate extract_event_id() falls back to entity_id when event_id is missing.
    """
    payload = {
        "entity_id": "entity-999",
    }

    assert extract_event_id(payload) == "entity-999"


def test_extract_event_id_returns_none_when_both_missing() -> None:
    """
    Validate extract_event_id() returns None when both keys are missing.
    """
    payload = {
        "name": "test",
    }

    assert extract_event_id(payload) is None


# =========================================================
# Tests for single-message processing
# =========================================================
def test_process_single_message_increments_processed_count() -> None:
    """
    Validate process_single_message() increments processed count for processed results.
    """
    topic = "inventory.low_stock.alert"
    payload = build_valid_event()
    summary = ConsumerRunSummary()

    service = FakeEventProcessingService(
        result=FakeProcessingResult(
            event_id="evt-1001",
            status="processed",
            action_taken="replenishment_review_triggered",
            message="Processed successfully.",
            decision_payload={"sku_code": "SKU-100245"},
            warnings=[],
        )
    )

    process_single_message(
        topic=topic,
        payload=payload,
        event_processing_service=service,
        summary=summary,
    )

    assert len(service.received_events) == 1
    assert summary.processed_counts[topic] == 1
    assert summary.ignored_counts.get(topic, 0) == 0
    assert summary.error_counts.get(topic, 0) == 0


def test_process_single_message_increments_ignored_count() -> None:
    """
    Validate process_single_message() increments ignored count for ignored results.
    """
    topic = "inventory.low_stock.alert"
    payload = build_valid_event()
    summary = ConsumerRunSummary()

    service = FakeEventProcessingService(
        result=FakeProcessingResult(
            event_id="evt-1001",
            status="ignored",
            action_taken="no_handler",
            message="Ignored event.",
            decision_payload={},
            warnings=["Unhandled event_type"],
        )
    )

    process_single_message(
        topic=topic,
        payload=payload,
        event_processing_service=service,
        summary=summary,
    )

    assert summary.processed_counts.get(topic, 0) == 0
    assert summary.ignored_counts[topic] == 1
    assert summary.error_counts.get(topic, 0) == 0


def test_process_single_message_increments_error_count_for_non_processed_status() -> None:
    """
    Validate process_single_message() increments error count for non-processed, non-ignored results.
    """
    topic = "inventory.low_stock.alert"
    payload = build_valid_event()
    summary = ConsumerRunSummary()

    service = FakeEventProcessingService(
        result=FakeProcessingResult(
            event_id="evt-1001",
            status="failed",
            action_taken="processing_failed",
            message="Processing failed.",
            decision_payload={},
            warnings=["Unexpected issue"],
        )
    )

    process_single_message(
        topic=topic,
        payload=payload,
        event_processing_service=service,
        summary=summary,
    )

    assert summary.processed_counts.get(topic, 0) == 0
    assert summary.ignored_counts.get(topic, 0) == 0
    assert summary.error_counts[topic] == 1


# =========================================================
# Tests for consumer loop
# =========================================================
def test_consume_messages_processes_valid_message_and_updates_summary() -> None:
    """
    Validate consume_messages() processes one valid message successfully.
    """
    topic = "inventory.low_stock.alert"
    event = build_valid_event("evt-2001")

    consumer = FakeKafkaConsumer(
        messages=[
            FakeKafkaMessage(
                topic=topic,
                value=event,
                partition=0,
                offset=10,
                key="evt-2001",
            )
        ]
    )

    service = FakeEventProcessingService(
        result=FakeProcessingResult(
            event_id="evt-2001",
            status="processed",
            action_taken="replenishment_review_triggered",
            message="Processed successfully.",
            decision_payload={"sku_code": "SKU-100245"},
            warnings=[],
        )
    )

    summary = consume_messages(
        consumer=consumer,
        event_processing_service=service,
        max_messages=1,
    )

    assert summary.consumed_counts[topic] == 1
    assert summary.processed_counts[topic] == 1
    assert summary.ignored_counts.get(topic, 0) == 0
    assert summary.error_counts.get(topic, 0) == 0


def test_consume_messages_marks_invalid_payload_as_error() -> None:
    """
    Validate consume_messages() marks invalid non-dict payload as error.
    """
    topic = "inventory.low_stock.alert"

    consumer = FakeKafkaConsumer(
        messages=[
            FakeKafkaMessage(
                topic=topic,
                value="not-a-dict",
                partition=0,
                offset=11,
                key="bad-msg",
            )
        ]
    )

    service = FakeEventProcessingService()

    summary = consume_messages(
        consumer=consumer,
        event_processing_service=service,
        max_messages=1,
    )

    assert summary.consumed_counts[topic] == 1
    assert summary.processed_counts.get(topic, 0) == 0
    assert summary.ignored_counts.get(topic, 0) == 0
    assert summary.error_counts[topic] == 1
    assert len(service.received_events) == 0


def test_consume_messages_increments_error_when_processing_raises_exception() -> None:
    """
    Validate consume_messages() increments error count when processing fails.
    """
    topic = "inventory.low_stock.alert"
    event = build_valid_event("evt-3001")

    consumer = FakeKafkaConsumer(
        messages=[
            FakeKafkaMessage(
                topic=topic,
                value=event,
                partition=0,
                offset=12,
                key="evt-3001",
            )
        ]
    )

    class ExplodingService:
        def process_event(self, event: Dict[str, Any]) -> Any:
            raise RuntimeError("boom")

    summary = consume_messages(
        consumer=consumer,
        event_processing_service=ExplodingService(),
        max_messages=1,
    )

    assert summary.consumed_counts[topic] == 1
    assert summary.processed_counts.get(topic, 0) == 0
    assert summary.ignored_counts.get(topic, 0) == 0
    assert summary.error_counts[topic] == 1


def test_consume_messages_respects_max_messages_limit() -> None:
    """
    Validate consume_messages() stops after max_messages is reached.
    """
    topic = "inventory.low_stock.alert"

    consumer = FakeKafkaConsumer(
        messages=[
            FakeKafkaMessage(topic=topic, value=build_valid_event("evt-1"), offset=1),
            FakeKafkaMessage(topic=topic, value=build_valid_event("evt-2"), offset=2),
            FakeKafkaMessage(topic=topic, value=build_valid_event("evt-3"), offset=3),
        ]
    )

    service = FakeEventProcessingService()

    summary = consume_messages(
        consumer=consumer,
        event_processing_service=service,
        max_messages=2,
    )

    assert summary.consumed_counts[topic] == 2
    assert summary.processed_counts[topic] == 2
    assert len(service.received_events) == 2


# =========================================================
# Tests for summary logging
# =========================================================
def test_log_summary_runs_without_error() -> None:
    """
    Validate log_summary() can run with populated summary data.
    """
    summary = ConsumerRunSummary()
    summary.increment_consumed("inventory.low_stock.alert")
    summary.increment_processed("inventory.low_stock.alert")
    summary.increment_consumed("sales.order.created")
    summary.increment_error("sales.order.created")

    log_summary(summary)

    assert summary.consumed_counts["inventory.low_stock.alert"] == 1
    assert summary.processed_counts["inventory.low_stock.alert"] == 1
    assert summary.error_counts["sales.order.created"] == 1
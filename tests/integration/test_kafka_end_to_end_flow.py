from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, Dict, Iterable, List

from app.services.event_processing_service import EventProcessingService
from scripts.kafka_consumer import consume_messages
from scripts.kafka_producer import extract_message_key


# =========================================================
# Constants
# =========================================================
EXPECTED_TOPIC = "inventory.low_stock.alert"
EXPECTED_ACTION = "replenishment_review_triggered"


# =========================================================
# Test doubles
# =========================================================
class DummyForecastService:
    """
    Deterministic recommendation service stub for end-to-end testing.
    """

    def get_recommendations(self, **kwargs: Any) -> Dict[str, Any]:
        return {
            "recommendation_type": "urgent_replenishment_review",
            "recommended_order_qty": 60,
            "priority_level": "high",
            "reason_code": "low_stock_high_risk",
        }


@dataclass
class FakeKafkaMessage:
    """
    Minimal Kafka-like message object for testing consumer flow.
    """

    topic: str
    value: Dict[str, Any]
    partition: int = 0
    offset: int = 0
    key: str | None = None


class FakeKafkaConsumer:
    """
    Minimal iterable Kafka-like consumer for integration testing.
    """

    def __init__(self, messages: List[FakeKafkaMessage]) -> None:
        self.messages = messages

    def __iter__(self) -> Iterable[FakeKafkaMessage]:
        return iter(self.messages)


# =========================================================
# Test data builder
# =========================================================
def build_low_stock_event() -> Dict[str, Any]:
    """
    Build one realistic low-stock Kafka event that matches:
    - kafka_producer message shape
    - kafka_consumer processing flow
    - EventProcessingService low-stock handler contract
    """
    return {
        "event_id": "evt-low-stock-0001",
        "event_type": EXPECTED_TOPIC,
        "event_timestamp": datetime.now(UTC).isoformat(),
        "source_system": "edip_test_suite",
        "entity_type": "inventory_snapshot",
        "entity_id": "inv-snapshot-100245-1",
        "region_id": 1,
        "schema_version": "1.0",
        "payload_json": {
            "product_id": 245,
            "sku_code": "SKU-100245",
            "warehouse_id": "",
            "store_id": 3,
            "available_qty": 8,
            "reorder_point": 30,
            "safety_stock": 15,
        },
    }


# =========================================================
# Helpers
# =========================================================
def result_to_dict(result: Any) -> Dict[str, Any]:
    """
    Convert EventProcessingResult to a plain dictionary.
    """
    if hasattr(result, "__dataclass_fields__"):
        return asdict(result)

    if hasattr(result, "__dict__"):
        return dict(result.__dict__)

    raise AssertionError(f"Unsupported result type: {type(result)!r}")


# =========================================================
# Tests
# =========================================================
def test_kafka_end_to_end_flow_low_stock_alert_maps_to_replenishment_action() -> None:
    """
    Validate one full low-stock path:

    producer-style event -> consumer-style receipt -> real EventProcessingService
    -> correct final business action and decision payload
    """
    # -----------------------------------------------------
    # Step 1: simulate producer publishing one event
    # -----------------------------------------------------
    source_event = build_low_stock_event()
    produced_event = deepcopy(source_event)
    produced_event_json = json.dumps(produced_event)
    produced_key = extract_message_key(produced_event)

    assert produced_event["event_type"] == EXPECTED_TOPIC
    assert produced_event["event_id"] == source_event["event_id"]
    assert isinstance(produced_event["payload_json"], dict)
    assert produced_key == "evt-low-stock-0001"

    # -----------------------------------------------------
    # Step 2: simulate consumer receiving the same event
    # -----------------------------------------------------
    consumed_event = json.loads(produced_event_json)

    assert consumed_event["event_id"] == produced_event["event_id"]
    assert consumed_event["event_type"] == produced_event["event_type"]
    assert consumed_event["payload_json"]["sku_code"] == "SKU-100245"

    # -----------------------------------------------------
    # Step 3: process with the real service
    # -----------------------------------------------------
    service = EventProcessingService(
        forecast_service=DummyForecastService(),
    )

    raw_result = service.process_event(consumed_event)
    result = result_to_dict(raw_result)
    decision_payload = result["decision_payload"]

    # -----------------------------------------------------
    # Step 4: validate final business action
    # -----------------------------------------------------
    assert result["status"] == "processed"
    assert result["action_taken"] == EXPECTED_ACTION

    # -----------------------------------------------------
    # Step 5: validate returned business payload
    # -----------------------------------------------------
    assert result["event_id"] == consumed_event["event_id"]
    assert result["event_type"] == EXPECTED_TOPIC

    assert decision_payload["product_id"] == "245"
    assert decision_payload["sku_code"] == "SKU-100245"
    assert decision_payload["warehouse_id"] == ""
    assert decision_payload["store_id"] == "3"
    assert decision_payload["available_qty"] == 8.0
    assert decision_payload["reorder_point"] == 30.0
    assert decision_payload["safety_stock"] == 15.0

    # -----------------------------------------------------
    # Step 6: validate recommendation payload
    # -----------------------------------------------------
    recommended_next_action = decision_payload["recommended_next_action"]

    assert isinstance(recommended_next_action, dict)
    assert recommended_next_action["recommendation_type"] == "urgent_replenishment_review"
    assert recommended_next_action["recommended_order_qty"] == 60
    assert recommended_next_action["priority_level"] == "high"
    assert recommended_next_action["reason_code"] == "low_stock_high_risk"

    # -----------------------------------------------------
    # Step 7: validate human-meaningful output
    # -----------------------------------------------------
    assert isinstance(result["message"], str)
    assert result["message"].strip() != ""
    assert "replenishment review triggered" in result["message"].lower()

    # -----------------------------------------------------
    # Step 8: validate warnings and metadata
    # -----------------------------------------------------
    assert result["warnings"] == []
    assert isinstance(result["processed_at"], str)
    assert result["processed_at"].strip() != ""


def test_kafka_end_to_end_flow_consumer_loop_updates_summary_correctly() -> None:
    """
    Validate the real consumer-side flow using consume_messages().
    """
    event = build_low_stock_event()

    fake_messages = [
        FakeKafkaMessage(
            topic=EXPECTED_TOPIC,
            value=event,
            partition=0,
            offset=12,
            key=extract_message_key(event),
        )
    ]
    fake_consumer = FakeKafkaConsumer(messages=fake_messages)

    service = EventProcessingService(
        forecast_service=DummyForecastService(),
    )

    summary = consume_messages(
        consumer=fake_consumer,
        event_processing_service=service,
        max_messages=1,
    )

    assert summary.consumed_counts[EXPECTED_TOPIC] == 1
    assert summary.processed_counts[EXPECTED_TOPIC] == 1
    assert summary.ignored_counts.get(EXPECTED_TOPIC, 0) == 0
    assert summary.error_counts.get(EXPECTED_TOPIC, 0) == 0


def test_kafka_end_to_end_flow_produced_and_consumed_event_match_by_event_id() -> None:
    """
    Produced event and consumed event must match by event_id.
    """
    produced_event = build_low_stock_event()
    consumed_event = json.loads(json.dumps(produced_event))

    assert produced_event["event_id"] == consumed_event["event_id"]
    assert produced_event["event_type"] == consumed_event["event_type"]
    assert produced_event["entity_id"] == consumed_event["entity_id"]
    assert produced_event["schema_version"] == consumed_event["schema_version"]


def test_kafka_end_to_end_flow_event_envelope_is_complete() -> None:
    """
    Validate the required Kafka event envelope fields.
    """
    event = build_low_stock_event()

    required_fields = [
        "event_id",
        "event_type",
        "event_timestamp",
        "source_system",
        "entity_type",
        "entity_id",
        "region_id",
        "payload_json",
        "schema_version",
    ]

    for field_name in required_fields:
        assert field_name in event
        assert event[field_name] is not None

    assert isinstance(event["payload_json"], dict)
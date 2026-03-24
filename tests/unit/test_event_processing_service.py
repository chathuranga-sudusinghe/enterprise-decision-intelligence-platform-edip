# tests/unit/test_event_processing_service.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest

from app.services.event_processing_service import (
    EventProcessingResult,
    EventProcessingService,
)


# =========================================================
# Test doubles
# =========================================================
class FakeForecastService:
    """Simple fake forecast service for unit tests."""

    def __init__(
        self,
        response: Optional[Dict[str, Any]] = None,
        should_raise: bool = False,
    ) -> None:
        self.response = response or {
            "recommended_action": "urgent_replenishment_review",
            "top_n": 1,
        }
        self.should_raise = should_raise
        self.calls: List[Dict[str, Any]] = []

    def get_recommendations(self, **kwargs: Any) -> Dict[str, Any]:
        """Track calls and return a controlled response."""
        self.calls.append(kwargs)

        if self.should_raise:
            raise RuntimeError("Forecast service failed.")

        return self.response


class FakeDecisionLogWriter:
    """Simple fake decision log writer for unit tests."""

    def __init__(self, should_raise: bool = False) -> None:
        self.should_raise = should_raise
        self.saved_records: List[Dict[str, Any]] = []

    def save_decision(self, decision_record: Dict[str, Any]) -> None:
        """Track saved decision records."""
        if self.should_raise:
            raise RuntimeError("Decision log write failed.")

        self.saved_records.append(decision_record)


# =========================================================
# Helpers
# =========================================================
def build_base_event(
    *,
    event_type: str = "inventory.low_stock.alert",
    payload_json: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a valid base Kafka event for tests."""
    return {
        "event_id": "EVT-TEST-0001",
        "event_type": event_type,
        "event_timestamp": "2026-03-21T10:00:00+00:00",
        "source_system": "edip_phase_6_streaming_simulation",
        "entity_type": "inventory_alert",
        "entity_id": "SKU-1001-WH-01",
        "region_id": 1,
        "payload_json": payload_json
        or {
            "product_id": "SKU-1001",
            "sku_code": "SKU-1001",
            "warehouse_id": "WH-01",
            "store_id": None,
            "available_qty": 4,
            "reorder_point": 10,
            "safety_stock": 5,
            "alert_reason": "available_qty_below_or_equal_reorder_point",
        },
        "schema_version": "1.0",
    }


# =========================================================
# Core tests
# =========================================================
def test_process_event_returns_event_processing_result_for_valid_event() -> None:
    """A valid event should return a standard EventProcessingResult."""
    service = EventProcessingService()

    event = build_base_event()
    result = service.process_event(event)

    assert isinstance(result, EventProcessingResult)
    assert result.event_id == event["event_id"]
    assert result.event_type == event["event_type"]
    assert result.status == "processed"


def test_process_event_raises_for_missing_required_fields() -> None:
    """Missing required envelope fields should raise a ValueError."""
    service = EventProcessingService()

    event = build_base_event()
    del event["payload_json"]

    with pytest.raises(ValueError, match="missing required fields"):
        service.process_event(event)


def test_process_event_raises_when_payload_json_is_not_dict() -> None:
    """payload_json must be a dictionary."""
    service = EventProcessingService()

    event = build_base_event(payload_json="not-a-dict")

    with pytest.raises(ValueError, match="payload_json"):
        service.process_event(event)


def test_unknown_event_type_returns_ignored_result() -> None:
    """Unknown event types should be ignored safely."""
    service = EventProcessingService()

    event = build_base_event(event_type="unknown.topic.event")
    result = service.process_event(event)

    assert result.status == "ignored"
    assert result.action_taken == "no_handler"
    assert "No handler is registered" in result.message
    assert len(result.warnings) == 1
    assert "Unhandled event_type" in result.warnings[0]


# =========================================================
# Low-stock event tests
# =========================================================
def test_low_stock_event_calls_forecast_service_and_returns_recommendation() -> None:
    """Low-stock processing should call forecast service and include recommendation payload."""
    fake_forecast_service = FakeForecastService(
        response={
            "recommended_action": "urgent_replenishment_review",
            "priority": "high",
        }
    )
    service = EventProcessingService(forecast_service=fake_forecast_service)

    event = build_base_event()
    result = service.process_event(event)

    assert result.status == "processed"
    assert result.action_taken == "replenishment_review_triggered"
    assert result.decision_payload["product_id"] == "SKU-1001"
    assert result.decision_payload["available_qty"] == 4
    assert result.decision_payload["reorder_point"] == 10
    assert result.decision_payload["recommended_next_action"] == {
        "recommended_action": "urgent_replenishment_review",
        "priority": "high",
    }

    assert len(fake_forecast_service.calls) == 1
    assert fake_forecast_service.calls[0]["product_id"] == "SKU-1001"
    assert fake_forecast_service.calls[0]["warehouse_id"] == "WH-01"
    assert fake_forecast_service.calls[0]["region_id"] == 1
    assert fake_forecast_service.calls[0]["top_n"] == 1


def test_low_stock_event_handles_forecast_service_failure_with_warning() -> None:
    """Forecast failure should not break event processing; warning should be added."""
    fake_forecast_service = FakeForecastService(should_raise=True)
    service = EventProcessingService(forecast_service=fake_forecast_service)

    event = build_base_event()
    result = service.process_event(event)

    assert result.status == "processed"
    assert result.action_taken == "replenishment_review_triggered"
    assert result.decision_payload["recommended_next_action"] == {}
    assert len(result.warnings) == 1
    assert "Forecast/recommendation service failed" in result.warnings[0]


# =========================================================
# Decision log tests
# =========================================================
def test_decision_log_writer_is_called_after_successful_processing() -> None:
    """Decision log writer should receive one saved decision record."""
    fake_log_writer = FakeDecisionLogWriter()
    service = EventProcessingService(decision_log_writer=fake_log_writer)

    event = build_base_event()
    result = service.process_event(event)

    assert result.status == "processed"
    assert len(fake_log_writer.saved_records) == 1

    saved_record = fake_log_writer.saved_records[0]
    assert saved_record["event_id"] == event["event_id"]
    assert saved_record["event_type"] == event["event_type"]
    assert saved_record["entity_id"] == event["entity_id"]
    assert saved_record["region_id"] == event["region_id"]
    assert saved_record["status"] == "processed"
    assert saved_record["action_taken"] == "replenishment_review_triggered"


def test_decision_log_writer_failure_does_not_break_processing() -> None:
    """Decision log write failure should not break the main processing flow."""
    fake_log_writer = FakeDecisionLogWriter(should_raise=True)
    service = EventProcessingService(decision_log_writer=fake_log_writer)

    event = build_base_event()
    result = service.process_event(event)

    assert result.status == "processed"
    assert result.action_taken == "replenishment_review_triggered"


# =========================================================
# Other topic handler tests
# =========================================================
def test_logistics_shipment_delayed_event_is_processed_correctly() -> None:
    """Shipment delay events should return the expected action and payload."""
    service = EventProcessingService()

    event = build_base_event(
        event_type="logistics.shipment.delayed",
        payload_json={
            "shipment_id": "SHIP-2001",
            "supplier_id": "SUP-77",
            "warehouse_id": "WH-01",
            "expected_date": "2026-03-21",
            "new_expected_date": "2026-03-24",
            "delay_days": 3,
            "impact_severity": "high",
        },
    )
    result = service.process_event(event)

    assert result.status == "processed"
    assert result.action_taken == "supply_risk_flagged"
    assert result.decision_payload["shipment_id"] == "SHIP-2001"
    assert result.decision_payload["supplier_id"] == "SUP-77"
    assert result.decision_payload["warehouse_id"] == "WH-01"
    assert result.decision_payload["delay_days"] == 3
    assert result.decision_payload["impact_severity"] == "high"


def test_sales_order_created_event_is_processed_correctly() -> None:
    """Order-created events should be processed as demand signals."""
    service = EventProcessingService()

    event = build_base_event(
        event_type="sales.order.created",
        payload_json={
            "order_id": "ORD-1001",
            "customer_id": "CUST-101",
            "channel_id": "ONLINE",
            "region_id": 1,
            "order_value": 250.0,
            "total_units": 6,
        },
    )
    result = service.process_event(event)

    assert result.status == "processed"
    assert result.action_taken == "demand_signal_recorded"
    assert result.decision_payload["order_id"] == "ORD-1001"
    assert result.decision_payload["total_units"] == 6
    assert result.decision_payload["order_value"] == 250.0


def test_planning_replenishment_approved_event_is_processed_correctly() -> None:
    """Approved replenishment events should be processed correctly."""
    service = EventProcessingService()

    event = build_base_event(
        event_type="planning.replenishment.approved",
        payload_json={
            "recommendation_id": "REC-901",
            "product_id": "SKU-1001",
            "location_id": "WH-01",
            "recommended_qty": 20,
            "approved_qty": 18,
            "approval_status": "approved",
            "planner_id": "PLN-100",
        },
    )
    result = service.process_event(event)

    assert result.status == "processed"
    assert result.action_taken == "approved_replenishment_registered"
    assert result.decision_payload["recommendation_id"] == "REC-901"
    assert result.decision_payload["approved_qty"] == 18
    assert result.decision_payload["planner_id"] == "PLN-100"
    assert result.decision_payload["approval_status"] == "approved"
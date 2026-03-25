# app/services/event_processing_service.py

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from app.core.logging import get_logger


logger = get_logger(__name__)


# =========================================================
# Protocols / Interfaces
# =========================================================
class ForecastServiceProtocol(Protocol):
    """Duck-typed contract for forecast/recommendation service integration."""

    def get_recommendations(self, **kwargs: Any) -> Dict[str, Any]:
        """Return replenishment or forecast-driven recommendation payload."""
        ...


class DecisionLogWriterProtocol(Protocol):
    """Optional persistence hook for decision log writes."""

    def save_decision(self, decision_record: Dict[str, Any]) -> None:
        """Persist one decision record."""
        ...


# =========================================================
# Data models
# =========================================================
@dataclass
class EventProcessingResult:
    """Standard output for one processed Kafka event."""

    event_id: str
    event_type: str
    status: str
    action_taken: str
    message: str
    decision_payload: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    processed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# =========================================================
# Main service
# =========================================================
class EventProcessingService:
    """
    Central event-processing service for EDIP Phase 6+.

    Responsibility:
    - validate Kafka event envelope
    - dispatch by event_type
    - call downstream services when useful
    - return one clean processing result
    """

    REQUIRED_EVENT_FIELDS = {
        "event_id",
        "event_type",
        "event_timestamp",
        "source_system",
        "entity_type",
        "entity_id",
        "region_id",
        "payload_json",
        "schema_version",
    }

    def __init__(
        self,
        *,
        forecast_service: Optional[ForecastServiceProtocol] = None,
        decision_log_writer: Optional[DecisionLogWriterProtocol] = None,
    ) -> None:
        self.forecast_service = forecast_service
        self.decision_log_writer = decision_log_writer

        self._handlers = {
            "sales.order.created": self._handle_sales_order_created,
            "sales.order.completed": self._handle_sales_order_completed,
            "inventory.stock.updated": self._handle_inventory_stock_updated,
            "inventory.low_stock.alert": self._handle_inventory_low_stock_alert,
            "logistics.shipment.delayed": self._handle_logistics_shipment_delayed,
            "returns.return.created": self._handle_returns_return_created,
            "planning.forecast.generated": self._handle_planning_forecast_generated,
            "planning.replenishment.approved": self._handle_planning_replenishment_approved,
        }

    # =========================================================
    # Public API
    # =========================================================
    def process_event(self, event: Dict[str, Any]) -> EventProcessingResult:
        """
        Process one Kafka event and return a standard result object.
        """
        self._validate_event_envelope(event)

        event_id = self._safe_str(event.get("event_id"))
        event_type = self._safe_str(event.get("event_type"))
        payload = self._get_payload(event)

        logger.info(
            "Processing Kafka event | event_id=%s | event_type=%s | entity_id=%s",
            event_id,
            event_type,
            self._safe_str(event.get("entity_id")),
        )

        handler = self._handlers.get(event_type)
        if handler is None:
            logger.warning("No handler registered for event_type=%s", event_type)
            return EventProcessingResult(
                event_id=event_id,
                event_type=event_type,
                status="ignored",
                action_taken="no_handler",
                message=f"No handler is registered for event_type '{event_type}'.",
                decision_payload={"raw_payload": payload},
                warnings=[f"Unhandled event_type: {event_type}"],
            )

        result = handler(event)

        logger.info(
            "Completed Kafka event processing | event_id=%s | event_type=%s | status=%s | action=%s",
            result.event_id,
            result.event_type,
            result.status,
            result.action_taken,
        )

        if self.decision_log_writer is not None:
            self._write_decision_log_safe(event=event, result=result)

        return result

    # =========================================================
    # Envelope / validation helpers
    # =========================================================
    def _validate_event_envelope(self, event: Dict[str, Any]) -> None:
        if not isinstance(event, dict):
            raise TypeError("Kafka event must be a dictionary.")

        missing_fields = [
            field_name
            for field_name in self.REQUIRED_EVENT_FIELDS
            if field_name not in event
        ]
        if missing_fields:
            raise ValueError(
                f"Kafka event is missing required fields: {missing_fields}"
            )

        if not isinstance(event.get("payload_json"), dict):
            raise ValueError("Kafka event 'payload_json' must be a dictionary.")

    def _get_payload(self, event: Dict[str, Any]) -> Dict[str, Any]:
        payload = event.get("payload_json", {})
        if not isinstance(payload, dict):
            return {}
        return payload

    def _safe_str(self, value: Any, default: str = "") -> str:
        if value is None:
            return default
        return str(value)

    def _safe_int(self, value: Any, default: int = 0) -> int:
        if value in (None, ""):
            return default
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        if value in (None, ""):
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _write_decision_log_safe(
        self,
        *,
        event: Dict[str, Any],
        result: EventProcessingResult,
    ) -> None:
        try:
            decision_record = {
                "event_id": event.get("event_id"),
                "event_type": event.get("event_type"),
                "entity_id": event.get("entity_id"),
                "region_id": event.get("region_id"),
                "status": result.status,
                "action_taken": result.action_taken,
                "message": result.message,
                "decision_payload_json": json.dumps(
                    result.decision_payload,
                    ensure_ascii=False,
                    default=str,
                ),
                "processed_at": result.processed_at,
            }
            self.decision_log_writer.save_decision(decision_record)
        except Exception:
            logger.exception("Decision log write failed.")

    # =========================================================
    # Event handlers
    # =========================================================
    def _handle_sales_order_created(
        self,
        event: Dict[str, Any],
    ) -> EventProcessingResult:
        payload = self._get_payload(event)

        order_id = self._safe_str(payload.get("order_id"))
        total_units = self._safe_float(payload.get("total_units"))
        order_value = self._safe_float(payload.get("order_value"))

        return EventProcessingResult(
            event_id=self._safe_str(event.get("event_id")),
            event_type=self._safe_str(event.get("event_type")),
            status="processed",
            action_taken="demand_signal_recorded",
            message="Order creation event processed as an upstream demand signal.",
            decision_payload={
                "order_id": order_id,
                "total_units": total_units,
                "order_value": order_value,
            },
        )

    def _handle_sales_order_completed(
        self,
        event: Dict[str, Any],
    ) -> EventProcessingResult:
        payload = self._get_payload(event)

        sale_id = self._safe_str(payload.get("sale_id"))
        product_id = self._safe_str(payload.get("product_id"))
        units_sold = self._safe_float(payload.get("units_sold"))
        sales_amount = self._safe_float(payload.get("sales_amount"))

        return EventProcessingResult(
            event_id=self._safe_str(event.get("event_id")),
            event_type=self._safe_str(event.get("event_type")),
            status="processed",
            action_taken="sales_signal_recorded",
            message="Sales completion event processed for downstream demand and performance tracking.",
            decision_payload={
                "sale_id": sale_id,
                "product_id": product_id,
                "units_sold": units_sold,
                "sales_amount": sales_amount,
            },
        )

    def _handle_inventory_stock_updated(
        self,
        event: Dict[str, Any],
    ) -> EventProcessingResult:
        payload = self._get_payload(event)

        product_id = self._safe_str(payload.get("product_id"))
        location_id = self._safe_str(payload.get("location_id"))
        new_qty = self._safe_float(payload.get("new_qty"))
        delta_qty = self._safe_float(payload.get("delta_qty"))
        reason_code = self._safe_str(payload.get("reason_code"))

        return EventProcessingResult(
            event_id=self._safe_str(event.get("event_id")),
            event_type=self._safe_str(event.get("event_type")),
            status="processed",
            action_taken="inventory_state_updated",
            message="Inventory stock movement event processed successfully.",
            decision_payload={
                "product_id": product_id,
                "location_id": location_id,
                "new_qty": new_qty,
                "delta_qty": delta_qty,
                "reason_code": reason_code,
            },
        )

    def _handle_inventory_low_stock_alert(
        self,
        event: Dict[str, Any],
    ) -> EventProcessingResult:
        payload = self._get_payload(event)

        product_id = self._safe_str(payload.get("product_id"))
        sku_code = self._safe_str(payload.get("sku_code"))
        warehouse_id = self._safe_str(payload.get("warehouse_id"))
        store_id = self._safe_str(payload.get("store_id"))
        available_qty = self._safe_float(payload.get("available_qty"))
        reorder_point = self._safe_float(payload.get("reorder_point"))
        safety_stock = self._safe_float(payload.get("safety_stock"))

        recommendation_payload: Dict[str, Any] = {}
        warnings: List[str] = []

        if self.forecast_service is not None:
            try:
                # Generic contract for your current project.
                recommendation_payload = self.forecast_service.get_recommendations(
                    product_id=product_id or None,
                    warehouse_id=warehouse_id or None,
                    store_id=store_id or None,
                    region_id=event.get("region_id"),
                    top_n=1,
                )
            except Exception:
                logger.exception(
                    "Forecast/recommendation service failed for low-stock event."
                )
                warnings.append(
                    "Forecast/recommendation service failed during low-stock processing."
                )

        return EventProcessingResult(
            event_id=self._safe_str(event.get("event_id")),
            event_type=self._safe_str(event.get("event_type")),
            status="processed",
            action_taken="replenishment_review_triggered",
            message="Low-stock alert processed and replenishment review triggered.",
            decision_payload={
                "product_id": product_id,
                "sku_code": sku_code,
                "warehouse_id": warehouse_id,
                "store_id": store_id,
                "available_qty": available_qty,
                "reorder_point": reorder_point,
                "safety_stock": safety_stock,
                "recommended_next_action": recommendation_payload,
            },
            warnings=warnings,
        )

    def _handle_logistics_shipment_delayed(
        self,
        event: Dict[str, Any],
    ) -> EventProcessingResult:
        payload = self._get_payload(event)

        shipment_id = self._safe_str(payload.get("shipment_id"))
        supplier_id = self._safe_str(payload.get("supplier_id"))
        warehouse_id = self._safe_str(payload.get("warehouse_id"))
        delay_days = self._safe_int(payload.get("delay_days"))
        impact_severity = self._safe_str(payload.get("impact_severity"))

        return EventProcessingResult(
            event_id=self._safe_str(event.get("event_id")),
            event_type=self._safe_str(event.get("event_type")),
            status="processed",
            action_taken="supply_risk_flagged",
            message="Delayed shipment event processed and supply risk flagged.",
            decision_payload={
                "shipment_id": shipment_id,
                "supplier_id": supplier_id,
                "warehouse_id": warehouse_id,
                "delay_days": delay_days,
                "impact_severity": impact_severity,
            },
        )

    def _handle_returns_return_created(
        self,
        event: Dict[str, Any],
    ) -> EventProcessingResult:
        payload = self._get_payload(event)

        return_id = self._safe_str(payload.get("return_id"))
        order_id = self._safe_str(payload.get("order_id"))
        sale_id = self._safe_str(payload.get("sale_id"))
        product_id = self._safe_str(payload.get("product_id"))
        return_qty = self._safe_float(payload.get("return_qty"))

        return EventProcessingResult(
            event_id=self._safe_str(event.get("event_id")),
            event_type=self._safe_str(event.get("event_type")),
            status="processed",
            action_taken="return_signal_recorded",
            message="Return event processed for inventory and sales adjustment workflows.",
            decision_payload={
                "return_id": return_id,
                "order_id": order_id,
                "sale_id": sale_id,
                "product_id": product_id,
                "return_qty": return_qty,
            },
        )

    def _handle_planning_forecast_generated(
        self,
        event: Dict[str, Any],
    ) -> EventProcessingResult:
        payload = self._get_payload(event)

        forecast_id = self._safe_str(payload.get("forecast_id"))
        product_id = self._safe_str(payload.get("product_id"))
        location_id = self._safe_str(payload.get("location_id"))
        forecast_qty = self._safe_float(payload.get("forecast_qty"))
        model_name = self._safe_str(payload.get("model_name"))

        return EventProcessingResult(
            event_id=self._safe_str(event.get("event_id")),
            event_type=self._safe_str(event.get("event_type")),
            status="processed",
            action_taken="forecast_signal_registered",
            message="Forecast-generated event processed successfully.",
            decision_payload={
                "forecast_id": forecast_id,
                "product_id": product_id,
                "location_id": location_id,
                "forecast_qty": forecast_qty,
                "model_name": model_name,
            },
        )

    def _handle_planning_replenishment_approved(
        self,
        event: Dict[str, Any],
    ) -> EventProcessingResult:
        payload = self._get_payload(event)

        recommendation_id = self._safe_str(payload.get("recommendation_id"))
        product_id = self._safe_str(payload.get("product_id"))
        location_id = self._safe_str(payload.get("location_id"))
        approved_qty = self._safe_float(payload.get("approved_qty"))
        planner_id = self._safe_str(payload.get("planner_id"))
        approval_status = self._safe_str(payload.get("approval_status"))

        return EventProcessingResult(
            event_id=self._safe_str(event.get("event_id")),
            event_type=self._safe_str(event.get("event_type")),
            status="processed",
            action_taken="approved_replenishment_registered",
            message="Approved replenishment event processed successfully.",
            decision_payload={
                "recommendation_id": recommendation_id,
                "product_id": product_id,
                "location_id": location_id,
                "approved_qty": approved_qty,
                "planner_id": planner_id,
                "approval_status": approval_status,
            },
        )
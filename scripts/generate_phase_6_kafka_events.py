from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import yaml

from app.core.logging import get_logger, setup_logging


logger = get_logger(__name__)


# =========================================================
# Config / Paths
# =========================================================
@dataclass(frozen=True)
class Paths:
    project_root: Path
    config_path: Path
    synthetic_dir: Path
    output_dir: Path


def build_paths() -> Paths:
    project_root = Path(__file__).resolve().parents[1]
    return Paths(
        project_root=project_root,
        config_path=project_root / "configs" / "kafka_event_schema.yaml",
        synthetic_dir=project_root / "data" / "synthetic",
        output_dir=project_root / "data" / "exports" / "kafka_events",
    )


# =========================================================
# Constants
# =========================================================
SOURCE_FILES: Dict[str, str] = {
    "analytics.fact_orders": "fact_orders.csv",
    "analytics.fact_sales": "fact_sales.csv",
    "analytics.fact_stock_movements": "fact_stock_movements.csv",
    "analytics.fact_inventory_snapshot": "fact_inventory_snapshot.csv",
    "analytics.fact_inbound_shipments": "fact_inbound_shipments.csv",
    "analytics.fact_returns": "fact_returns.csv",
    "analytics.fact_demand_forecast": "fact_demand_forecast.csv",
    "analytics.fact_replenishment_recommendation": "fact_replenishment_recommendation.csv",
}

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
# Utility helpers
# =========================================================
def load_yaml_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Kafka schema config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("Kafka schema config must load as a dictionary.")

    return config


def ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


def load_csv_if_exists(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        logger.warning("Source file not found, returning empty DataFrame: %s", csv_path)
        return pd.DataFrame()

    df = pd.read_csv(csv_path)
    logger.info("Loaded %s rows from %s", len(df), csv_path.name)
    return df


def normalize_null(value: Any) -> Any:
    if pd.isna(value):
        return None
    return value


def safe_str(value: Any, default: str = "") -> str:
    value = normalize_null(value)
    if value is None:
        return default
    return str(value)


def safe_int(value: Any, default: int = 0) -> int:
    value = normalize_null(value)
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    value = normalize_null(value)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def find_first_existing(row: pd.Series, candidates: List[str], default: Any = None) -> Any:
    row_dict = row.to_dict()
    lower_map = {str(k).lower(): v for k, v in row_dict.items()}

    for candidate in candidates:
        if candidate in row_dict:
            return row_dict[candidate]
        lowered = candidate.lower()
        if lowered in lower_map:
            return lower_map[lowered]

    return default


def parse_timestamp(value: Any) -> str:
    value = normalize_null(value)

    if value is None or str(value).strip() == "":
        return datetime.now(timezone.utc).isoformat()

    text = str(value).strip()

    # Already looks ISO-like
    try:
        dt = pd.to_datetime(text, utc=True, errors="raise")
        return dt.isoformat()
    except Exception:
        logger.warning("Could not parse timestamp '%s'. Using current UTC time.", text)
        return datetime.now(timezone.utc).isoformat()


def build_event_id(topic: str, entity_id: str, row_index: int) -> str:
    compact_topic = topic.replace(".", "-")
    random_part = uuid.uuid4().hex[:8].upper()
    return f"EVT-{compact_topic}-{entity_id}-{row_index}-{random_part}"


def record_to_payload(row: pd.Series, excluded_fields: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    excluded = set(excluded_fields or [])
    payload: Dict[str, Any] = {}

    for key, value in row.to_dict().items():
        if key in excluded:
            continue
        payload[key] = normalize_null(value)

    return payload


def write_jsonl(output_path: Path, records: List[Dict[str, Any]]) -> None:
    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


# =========================================================
# Topic-specific row filters
# =========================================================
def filter_low_stock_alerts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    filtered_rows: List[Dict[str, Any]] = []

    for _, row in df.iterrows():
        available_qty = safe_float(
            find_first_existing(row, ["available_qty", "on_hand_qty", "ending_qty"], 0.0),
            default=0.0,
        )

        reorder_point = safe_float(
            find_first_existing(
                row,
                ["reorder_point_qty", "reorder_point", "reorder_point_default", "reorder_level", "min_stock_level"],
                0.0,
            ),
            default=0.0,
        )

        if reorder_point > 0 and available_qty <= reorder_point:
            filtered_rows.append(row.to_dict())

    result = pd.DataFrame(filtered_rows)
    logger.info("Filtered %s low-stock alert rows.", len(result))
    return result


def filter_delayed_shipments(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    filtered_rows: List[Dict[str, Any]] = []

    for _, row in df.iterrows():
        delay_days = safe_int(find_first_existing(row, ["delay_days"], 0), default=0)
        status_text = safe_str(
            find_first_existing(row, ["shipment_status", "status", "delivery_status"], ""),
            default="",
        ).lower()

        is_delayed = delay_days > 0 or "delay" in status_text
        if is_delayed:
            filtered_rows.append(row.to_dict())

    result = pd.DataFrame(filtered_rows)
    logger.info("Filtered %s delayed shipment rows.", len(result))
    return result


def filter_approved_replenishment(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    filtered_rows: List[Dict[str, Any]] = []

    for _, row in df.iterrows():
        status_text = safe_str(
            find_first_existing(row, ["decision_status", "approval_status", "recommendation_status", "status"], ""),
            default="",
        ).lower()

        approved_flag_raw = find_first_existing(row, ["approved_flag", "is_approved"], None)
        approved_flag = False
        if approved_flag_raw is not None:
            approved_flag = str(approved_flag_raw).strip().lower() in {"1", "true", "yes", "y"}

        is_approved = approved_flag or status_text in {"approved", "accepted", "confirmed"}
        if is_approved:
            filtered_rows.append(row.to_dict())

    result = pd.DataFrame(filtered_rows)
    logger.info("Filtered %s approved replenishment rows.", len(result))
    return result


# =========================================================
# Topic-specific envelope builders
# =========================================================
def build_sales_order_created_event(
    row: pd.Series,
    topic: str,
    entity_type: str,
    source_system: str,
    schema_version: str,
    row_index: int,
) -> Dict[str, Any]:
    order_id = safe_str(find_first_existing(row, ["order_id", "order_code", "order_number"], f"row-{row_index}"))
    region_id = safe_int(find_first_existing(row, ["region_id"], 0), default=0)
    timestamp = parse_timestamp(find_first_existing(row, ["order_timestamp", "order_date", "created_at"], None))

    payload = {
        "order_id": normalize_null(find_first_existing(row, ["order_id"])),
        "customer_id": normalize_null(find_first_existing(row, ["customer_id"])),
        "channel_id": normalize_null(find_first_existing(row, ["channel_id"])),
        "region_id": region_id,
        "order_value": normalize_null(find_first_existing(row, ["order_value", "order_total", "net_amount"])),
        "total_units": normalize_null(find_first_existing(row, ["total_units", "units_total", "quantity_total"])),
    }

    payload["raw_record"] = record_to_payload(row)

    return {
        "event_id": build_event_id(topic, order_id, row_index),
        "event_type": topic,
        "event_timestamp": timestamp,
        "source_system": source_system,
        "entity_type": entity_type,
        "entity_id": order_id,
        "region_id": region_id,
        "payload_json": payload,
        "schema_version": schema_version,
    }


def build_sales_order_completed_event(
    row: pd.Series,
    topic: str,
    entity_type: str,
    source_system: str,
    schema_version: str,
    row_index: int,
) -> Dict[str, Any]:
    sale_id = safe_str(find_first_existing(row, ["sale_id", "sales_id", "transaction_id"], f"row-{row_index}"))
    region_id = safe_int(find_first_existing(row, ["region_id"], 0), default=0)
    timestamp = parse_timestamp(find_first_existing(row, ["sale_timestamp", "sale_date", "transaction_date"], None))

    payload = {
        "sale_id": normalize_null(find_first_existing(row, ["sale_id", "sales_id", "transaction_id"])),
        "order_id": normalize_null(find_first_existing(row, ["order_id"])),
        "customer_id": normalize_null(find_first_existing(row, ["customer_id"])),
        "channel_id": normalize_null(find_first_existing(row, ["channel_id"])),
        "product_id": normalize_null(find_first_existing(row, ["product_id"])),
        "units_sold": normalize_null(find_first_existing(row, ["units_sold", "quantity_sold", "quantity"])),
        "sales_amount": normalize_null(find_first_existing(row, ["sales_amount", "net_sales_amount", "net_amount"])),
    }

    payload["raw_record"] = record_to_payload(row)

    return {
        "event_id": build_event_id(topic, sale_id, row_index),
        "event_type": topic,
        "event_timestamp": timestamp,
        "source_system": source_system,
        "entity_type": entity_type,
        "entity_id": sale_id,
        "region_id": region_id,
        "payload_json": payload,
        "schema_version": schema_version,
    }


def build_inventory_stock_updated_event(
    row: pd.Series,
    topic: str,
    entity_type: str,
    source_system: str,
    schema_version: str,
    row_index: int,
) -> Dict[str, Any]:
    movement_id = safe_str(
        find_first_existing(row, ["movement_id", "stock_movement_id", "reference_id"], f"row-{row_index}")
    )
    region_id = safe_int(find_first_existing(row, ["region_id"], 0), default=0)
    timestamp = parse_timestamp(find_first_existing(row, ["movement_timestamp", "movement_date", "created_at"], None))

    payload = {
        "product_id": normalize_null(find_first_existing(row, ["product_id"])),
        "location_type": normalize_null(find_first_existing(row, ["location_type"])),
        "location_id": normalize_null(find_first_existing(row, ["location_id", "warehouse_id", "store_id"])),
        "previous_qty": normalize_null(find_first_existing(row, ["previous_qty", "qty_before"])),
        "new_qty": normalize_null(find_first_existing(row, ["new_qty", "qty_after"])),
        "delta_qty": normalize_null(find_first_existing(row, ["delta_qty", "quantity_delta", "movement_qty"])),
        "reason_code": normalize_null(find_first_existing(row, ["reason_code", "movement_type"])),
    }

    payload["raw_record"] = record_to_payload(row)

    return {
        "event_id": build_event_id(topic, movement_id, row_index),
        "event_type": topic,
        "event_timestamp": timestamp,
        "source_system": source_system,
        "entity_type": entity_type,
        "entity_id": movement_id,
        "region_id": region_id,
        "payload_json": payload,
        "schema_version": schema_version,
    }


def build_inventory_low_stock_alert_event(
    row: pd.Series,
    topic: str,
    entity_type: str,
    source_system: str,
    schema_version: str,
    row_index: int,
) -> Dict[str, Any]:
    product_id = safe_str(find_first_existing(row, ["product_id", "sku_code"], f"row-{row_index}"))
    warehouse_id = safe_str(find_first_existing(row, ["warehouse_id", "location_id"], "unknown"))
    entity_id = f"{product_id}-{warehouse_id}"
    region_id = safe_int(find_first_existing(row, ["region_id"], 0), default=0)
    timestamp = parse_timestamp(find_first_existing(row, ["snapshot_date", "inventory_date", "created_at"], None))

    available_qty = safe_float(find_first_existing(row, ["available_qty", "on_hand_qty", "ending_qty"], 0.0), 0.0)
    reorder_point = safe_float(
        find_first_existing(row, ["reorder_point_qty", "reorder_point", "reorder_point_default", "reorder_level"], 0.0), 0.0)

    payload = {
        "product_id": normalize_null(find_first_existing(row, ["product_id"])),
        "sku_code": normalize_null(find_first_existing(row, ["sku_code"])),
        "warehouse_id": normalize_null(find_first_existing(row, ["warehouse_id"])),
        "store_id": normalize_null(find_first_existing(row, ["store_id"])),
        "available_qty": available_qty,
        "reorder_point": reorder_point,
        "safety_stock": normalize_null(find_first_existing(row, ["safety_stock", "safety_stock_default"])),
        "alert_reason": "available_qty_below_or_equal_reorder_point",
    }

    payload["raw_record"] = record_to_payload(row)

    return {
        "event_id": build_event_id(topic, entity_id, row_index),
        "event_type": topic,
        "event_timestamp": timestamp,
        "source_system": source_system,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "region_id": region_id,
        "payload_json": payload,
        "schema_version": schema_version,
    }


def build_logistics_shipment_delayed_event(
    row: pd.Series,
    topic: str,
    entity_type: str,
    source_system: str,
    schema_version: str,
    row_index: int,
) -> Dict[str, Any]:
    shipment_id = safe_str(find_first_existing(row, ["shipment_id", "inbound_shipment_id"], f"row-{row_index}"))
    region_id = safe_int(find_first_existing(row, ["region_id"], 0), default=0)
    timestamp = parse_timestamp(find_first_existing(row, ["updated_at", "shipment_date", "expected_date"], None))

    payload = {
        "shipment_id": normalize_null(find_first_existing(row, ["shipment_id", "inbound_shipment_id"])),
        "supplier_id": normalize_null(find_first_existing(row, ["supplier_id"])),
        "warehouse_id": normalize_null(find_first_existing(row, ["warehouse_id"])),
        "expected_date": normalize_null(find_first_existing(row, ["expected_date"])),
        "new_expected_date": normalize_null(find_first_existing(row, ["new_expected_date", "revised_expected_date"])),
        "delay_days": normalize_null(find_first_existing(row, ["delay_days"])),
        "impact_severity": normalize_null(find_first_existing(row, ["impact_severity", "severity"])),
    }

    payload["raw_record"] = record_to_payload(row)

    return {
        "event_id": build_event_id(topic, shipment_id, row_index),
        "event_type": topic,
        "event_timestamp": timestamp,
        "source_system": source_system,
        "entity_type": entity_type,
        "entity_id": shipment_id,
        "region_id": region_id,
        "payload_json": payload,
        "schema_version": schema_version,
    }


def build_returns_return_created_event(
    row: pd.Series,
    topic: str,
    entity_type: str,
    source_system: str,
    schema_version: str,
    row_index: int,
) -> Dict[str, Any]:
    return_id = safe_str(find_first_existing(row, ["return_id", "return_code"], f"row-{row_index}"))
    region_id = safe_int(find_first_existing(row, ["region_id"], 0), default=0)
    timestamp = parse_timestamp(find_first_existing(row, ["return_timestamp", "return_date", "created_at"], None))

    payload = {
        "return_id": normalize_null(find_first_existing(row, ["return_id"])),
        "order_id": normalize_null(find_first_existing(row, ["order_id"])),
        "sale_id": normalize_null(find_first_existing(row, ["sale_id"])),
        "product_id": normalize_null(find_first_existing(row, ["product_id"])),
        "return_qty": normalize_null(find_first_existing(row, ["return_qty", "quantity_returned"])),
        "restockable_flag": normalize_null(find_first_existing(row, ["restockable_flag"])),
        "damaged_flag": normalize_null(find_first_existing(row, ["damaged_flag"])),
        "return_reason": normalize_null(find_first_existing(row, ["return_reason", "reason_code"])),
    }

    payload["raw_record"] = record_to_payload(row)

    return {
        "event_id": build_event_id(topic, return_id, row_index),
        "event_type": topic,
        "event_timestamp": timestamp,
        "source_system": source_system,
        "entity_type": entity_type,
        "entity_id": return_id,
        "region_id": region_id,
        "payload_json": payload,
        "schema_version": schema_version,
    }


def build_planning_forecast_generated_event(
    row: pd.Series,
    topic: str,
    entity_type: str,
    source_system: str,
    schema_version: str,
    row_index: int,
) -> Dict[str, Any]:
    forecast_id = safe_str(find_first_existing(row, ["forecast_id", "forecast_run_id"], f"row-{row_index}"))
    region_id = safe_int(find_first_existing(row, ["region_id"], 0), default=0)
    timestamp = parse_timestamp(find_first_existing(row, ["generated_at", "forecast_date", "created_at"], None))

    payload = {
        "forecast_id": normalize_null(find_first_existing(row, ["forecast_id"])),
        "forecast_run_id": normalize_null(find_first_existing(row, ["forecast_run_id"])),
        "product_id": normalize_null(find_first_existing(row, ["product_id"])),
        "location_id": normalize_null(find_first_existing(row, ["location_id", "store_id", "warehouse_id"])),
        "forecast_date": normalize_null(find_first_existing(row, ["forecast_date"])),
        "forecast_qty": normalize_null(find_first_existing(row, ["forecast_qty", "predicted_demand_qty"])),
        "confidence_band": normalize_null(find_first_existing(row, ["confidence_band", "confidence_level"])),
        "model_name": normalize_null(find_first_existing(row, ["model_name", "best_model_name"])),
    }

    payload["raw_record"] = record_to_payload(row)

    return {
        "event_id": build_event_id(topic, forecast_id, row_index),
        "event_type": topic,
        "event_timestamp": timestamp,
        "source_system": source_system,
        "entity_type": entity_type,
        "entity_id": forecast_id,
        "region_id": region_id,
        "payload_json": payload,
        "schema_version": schema_version,
    }


def build_planning_replenishment_approved_event(
    row: pd.Series,
    topic: str,
    entity_type: str,
    source_system: str,
    schema_version: str,
    row_index: int,
) -> Dict[str, Any]:
    recommendation_id = safe_str(
        find_first_existing(row, ["recommendation_id", "replenishment_recommendation_id"], f"row-{row_index}")
    )
    region_id = safe_int(find_first_existing(row, ["region_id"], 0), default=0)
    timestamp = parse_timestamp(find_first_existing(row, ["decision_timestamp", "approved_at", "created_at"], None))

    payload = {
        "recommendation_id": normalize_null(find_first_existing(row, ["recommendation_id"])),
        "product_id": normalize_null(find_first_existing(row, ["product_id"])),
        "location_id": normalize_null(find_first_existing(row, ["location_id", "warehouse_id", "store_id"])),
        "recommended_qty": normalize_null(find_first_existing(row, ["recommended_qty", "order_qty_recommended"])),
        "approved_qty": normalize_null(find_first_existing(row, ["approved_qty", "final_qty"])),
        "approval_status": normalize_null(
            find_first_existing(row, ["decision_status", "approval_status", "recommendation_status", "status"])
        ),
        "planner_id": normalize_null(find_first_existing(row, ["planner_id", "user_id"])),
    }

    payload["raw_record"] = record_to_payload(row)

    return {
        "event_id": build_event_id(topic, recommendation_id, row_index),
        "event_type": topic,
        "event_timestamp": timestamp,
        "source_system": source_system,
        "entity_type": entity_type,
        "entity_id": recommendation_id,
        "region_id": region_id,
        "payload_json": payload,
        "schema_version": schema_version,
    }


EVENT_BUILDERS = {
    "sales.order.created": build_sales_order_created_event,
    "sales.order.completed": build_sales_order_completed_event,
    "inventory.stock.updated": build_inventory_stock_updated_event,
    "inventory.low_stock.alert": build_inventory_low_stock_alert_event,
    "logistics.shipment.delayed": build_logistics_shipment_delayed_event,
    "returns.return.created": build_returns_return_created_event,
    "planning.forecast.generated": build_planning_forecast_generated_event,
    "planning.replenishment.approved": build_planning_replenishment_approved_event,
}


def apply_topic_filter(topic: str, df: pd.DataFrame) -> pd.DataFrame:
    if topic == "inventory.low_stock.alert":
        return filter_low_stock_alerts(df)

    if topic == "logistics.shipment.delayed":
        return filter_delayed_shipments(df)

    if topic == "planning.replenishment.approved":
        return filter_approved_replenishment(df)

    return df


# =========================================================
# Main event generation logic
# =========================================================
def generate_topic_events(
    topic: str,
    topic_cfg: Dict[str, Any],
    df: pd.DataFrame,
    source_system: str,
    schema_version: str,
) -> List[Dict[str, Any]]:
    if df.empty:
        logger.warning("No rows available for topic: %s", topic)
        return []

    entity_type = safe_str(topic_cfg.get("entity_type"), default="unknown_entity")
    builder = EVENT_BUILDERS.get(topic)

    if builder is None:
        raise ValueError(f"No event builder registered for topic: {topic}")

    filtered_df = apply_topic_filter(topic, df)
    events: List[Dict[str, Any]] = []

    for row_index, (_, row) in enumerate(filtered_df.iterrows(), start=1):
        event = builder(
            row=row,
            topic=topic,
            entity_type=entity_type,
            source_system=source_system,
            schema_version=schema_version,
            row_index=row_index,
        )
        events.append(event)

    logger.info("Generated %s events for topic %s", len(events), topic)
    return events


def generate_all_events(paths: Paths, config: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    topics_cfg = config.get("topics", {})
    schema_version = safe_str(config.get("schema_version"), default="1.0")
    source_system = safe_str(config.get("source_system_default"), default="edip_phase_6_streaming_simulation")

    if not topics_cfg:
        raise ValueError("No topics found in kafka_event_schema.yaml")

    all_events: Dict[str, List[Dict[str, Any]]] = {}

    for topic, topic_cfg in topics_cfg.items():
        source_table = safe_str(topic_cfg.get("source_table"))
        source_file_name = SOURCE_FILES.get(source_table)

        if not source_file_name:
            logger.warning("No source CSV mapping found for table: %s", source_table)
            all_events[topic] = []
            continue

        source_csv_path = paths.synthetic_dir / source_file_name
        df = load_csv_if_exists(source_csv_path)

        events = generate_topic_events(
            topic=topic,
            topic_cfg=topic_cfg,
            df=df,
            source_system=source_system,
            schema_version=schema_version,
        )
        all_events[topic] = events

    return all_events


def save_topic_outputs(output_dir: Path, all_events: Dict[str, List[Dict[str, Any]]]) -> None:
    for topic, events in all_events.items():
        output_file_name = TOPIC_OUTPUT_FILES.get(topic, f"{topic}.jsonl")
        output_path = output_dir / output_file_name
        write_jsonl(output_path, events)
        logger.info("Wrote %s events to %s", len(events), output_path)


def print_summary(paths: Paths, all_events: Dict[str, List[Dict[str, Any]]]) -> None:
    logger.info("Phase 6 Kafka simulation completed successfully.")
    logger.info("Output folder: %s", paths.output_dir)

    for topic, events in all_events.items():
        output_file_name = TOPIC_OUTPUT_FILES.get(topic, f"{topic}.jsonl")
        logger.info("%s : %s", output_file_name, f"{len(events):,}")


def main() -> None:
    setup_logging()

    try:
        paths = build_paths()
        ensure_output_dir(paths.output_dir)

        config = load_yaml_config(paths.config_path)
        all_events = generate_all_events(paths, config)
        save_topic_outputs(paths.output_dir, all_events)
        print_summary(paths, all_events)

    except Exception as exc:
        logger.exception("Error during Phase 6 Kafka event generation: %s", exc)
        raise
    finally:
        logger.info("Phase 6 Kafka generator script finished.")


if __name__ == "__main__":
    main()
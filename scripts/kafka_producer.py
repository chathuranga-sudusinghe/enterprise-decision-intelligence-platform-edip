from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from kafka import KafkaProducer
from kafka.errors import KafkaError

from app.core.logging import get_logger, setup_logging


logger = get_logger(__name__)


# =========================================================
# Paths / Config
# =========================================================
@dataclass(frozen=True)
class Paths:
    project_root: Path
    kafka_events_dir: Path


def build_paths() -> Paths:
    project_root = Path(__file__).resolve().parents[1]
    return Paths(
        project_root=project_root,
        kafka_events_dir=project_root / "data" / "exports" / "kafka_events",
    )


TOPIC_FILES: Dict[str, str] = {
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
# Kafka helpers
# =========================================================
def build_kafka_producer() -> KafkaProducer:
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    client_id = os.getenv("KAFKA_CLIENT_ID", "edip-phase-6-producer")

    logger.info("Creating Kafka producer with bootstrap servers: %s", bootstrap_servers)

    try:
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers.split(","),
            client_id=client_id,
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k is not None else None,
            acks="all",
            retries=3,
            linger_ms=10,
            request_timeout_ms=30000,
            max_block_ms=30000,
        )
        return producer
    except Exception as exc:
        logger.exception("Failed to create Kafka producer: %s", exc)
        raise


def iter_jsonl_records(file_path: Path) -> Iterable[Dict]:
    if not file_path.exists():
        logger.warning("Kafka event file not found: %s", file_path)
        return

    with file_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            text = line.strip()
            if not text:
                continue

            try:
                yield json.loads(text)
            except json.JSONDecodeError as exc:
                logger.warning(
                    "Skipping invalid JSON at %s line %s: %s",
                    file_path.name,
                    line_number,
                    exc,
                )


def extract_message_key(record: Dict) -> Optional[str]:
    event_id = record.get("event_id")
    entity_id = record.get("entity_id")

    if event_id is not None:
        return str(event_id)

    if entity_id is not None:
        return str(entity_id)

    return None


def send_topic_file(
    producer: KafkaProducer,
    topic: str,
    file_path: Path,
    max_messages: Optional[int] = None,
) -> Tuple[int, int]:
    success_count = 0
    failure_count = 0

    if not file_path.exists():
        logger.warning("Skipping topic %s because file does not exist: %s", topic, file_path)
        return success_count, failure_count

    logger.info("Publishing topic file: %s -> %s", file_path.name, topic)

    for index, record in enumerate(iter_jsonl_records(file_path), start=1):
        if max_messages is not None and index > max_messages:
            logger.info(
                "Stopped early for topic %s due to max_messages=%s",
                topic,
                max_messages,
            )
            break

        message_key = extract_message_key(record)

        try:
            future = producer.send(topic, key=message_key, value=record)
            future.get(timeout=30) # unit is seconds
            success_count += 1

        except KafkaError as exc:
            failure_count += 1
            logger.exception(
                "Kafka send failed for topic=%s event_id=%s error=%s",
                topic,
                record.get("event_id"),
                exc,
            )
        except Exception as exc:
            failure_count += 1
            logger.exception(
                "Unexpected send error for topic=%s event_id=%s error=%s",
                topic,
                record.get("event_id"),
                exc,
            )

    logger.info(
        "Finished publishing %s | success=%s | failed=%s",
        topic,
        success_count, 
        failure_count,
    )
    return success_count, failure_count


def publish_all_topics(
    producer: KafkaProducer,
    paths: Paths,
    max_messages_per_topic: Optional[int] = None,
) -> Dict[str, Dict[str, int]]:
    summary: Dict[str, Dict[str, int]] = {}

    for topic, filename in TOPIC_FILES.items():
        file_path = paths.kafka_events_dir / filename
        success_count, failure_count = send_topic_file(
            producer=producer,
            topic=topic,
            file_path=file_path,
            max_messages=max_messages_per_topic,
        )
        summary[topic] = {
            "success": success_count,
            "failed": failure_count,
        }

    return summary


def log_summary(summary: Dict[str, Dict[str, int]]) -> None:
    logger.info("Kafka producer publishing summary:")
    total_success = 0
    total_failed = 0

    for topic, stats in summary.items():
        success_count = stats.get("success", 0)
        failure_count = stats.get("failed", 0)
        total_success += success_count
        total_failed += failure_count

        logger.info(
            "%s | success=%s | failed=%s",
            topic,
            success_count,
            failure_count,
        )

    logger.info("TOTAL | success=%s | failed=%s", total_success, total_failed)


def main() -> None:
    setup_logging()

    producer: Optional[KafkaProducer] = None

    try:
        paths = build_paths()

        if not paths.kafka_events_dir.exists():
            raise FileNotFoundError(
                f"Kafka events directory not found: {paths.kafka_events_dir}"
            )

        max_messages_raw = os.getenv("KAFKA_MAX_MESSAGES_PER_TOPIC", "").strip()
        max_messages_per_topic = int(max_messages_raw) if max_messages_raw else None

        producer = build_kafka_producer()

        summary = publish_all_topics(
            producer=producer,
            paths=paths,
            max_messages_per_topic=max_messages_per_topic,
        )

        producer.flush()
        log_summary(summary)

        logger.info("Kafka producer publishing completed successfully.")

    except Exception as exc:
        logger.exception("Kafka producer script failed: %s", exc)
        raise
    finally:
        if producer is not None:
            try:
                producer.flush()
                producer.close()
            except Exception:
                logger.warning("Kafka producer close encountered a non-fatal issue.")

        logger.info("Kafka producer script finished.")


if __name__ == "__main__":
    main()
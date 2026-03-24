from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from kafka import KafkaConsumer

from app.core.logging import get_logger, setup_logging
from app.services.event_processing_service import EventProcessingService


logger = get_logger(__name__)


# =========================================================
# Kafka Topic Definitions
# =========================================================
TOPICS: List[str] = [
    "sales.order.created",
    "sales.order.completed",
    "inventory.stock.updated",
    "inventory.low_stock.alert",
    "logistics.shipment.delayed",
    "returns.return.created",
    "planning.forecast.generated",
    "planning.replenishment.approved",
]


# =========================================================
# Summary model
# =========================================================
@dataclass
class ConsumerRunSummary:
    """Track Kafka consumption and event-processing results."""

    consumed_counts: Dict[str, int] = field(default_factory=dict)
    processed_counts: Dict[str, int] = field(default_factory=dict)
    ignored_counts: Dict[str, int] = field(default_factory=dict)
    error_counts: Dict[str, int] = field(default_factory=dict)

    def increment_consumed(self, topic: str) -> None:
        self.consumed_counts[topic] = self.consumed_counts.get(topic, 0) + 1

    def increment_processed(self, topic: str) -> None:
        self.processed_counts[topic] = self.processed_counts.get(topic, 0) + 1

    def increment_ignored(self, topic: str) -> None:
        self.ignored_counts[topic] = self.ignored_counts.get(topic, 0) + 1

    def increment_error(self, topic: str) -> None:
        self.error_counts[topic] = self.error_counts.get(topic, 0) + 1


# =========================================================
# Kafka Helpers
# =========================================================
def parse_topics_from_env(default_topics: List[str]) -> List[str]:
    """Parse consumer topics from environment or return defaults."""
    raw_topics = os.getenv("KAFKA_CONSUMER_TOPICS", "").strip()

    if not raw_topics:
        return default_topics

    parsed_topics = [topic.strip() for topic in raw_topics.split(",") if topic.strip()]
    return parsed_topics if parsed_topics else default_topics


def build_kafka_consumer() -> KafkaConsumer:
    """Create and return a configured Kafka consumer."""
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    client_id = os.getenv("KAFKA_CONSUMER_CLIENT_ID", "edip-phase-6-consumer")
    group_id = os.getenv("KAFKA_CONSUMER_GROUP_ID", "edip-phase-6-consumer-group")
    auto_offset_reset = os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest").strip().lower()
    enable_auto_commit = os.getenv("KAFKA_ENABLE_AUTO_COMMIT", "true").strip().lower() == "true"
    consumer_timeout_ms = int(os.getenv("KAFKA_CONSUMER_TIMEOUT_MS", "10000"))

    topics = parse_topics_from_env(TOPICS)

    logger.info("Creating Kafka consumer with bootstrap servers: %s", bootstrap_servers)
    logger.info("Consumer topics: %s", topics)
    logger.info(
        "Consumer group_id: %s | auto_offset_reset: %s",
        group_id,
        auto_offset_reset,
    )

    try:
        consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap_servers.split(","),
            client_id=client_id,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=enable_auto_commit,
            consumer_timeout_ms=consumer_timeout_ms,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            key_deserializer=lambda k: k.decode("utf-8") if k is not None else None,
        )
        return consumer
    except Exception as exc:
        logger.exception("Failed to create Kafka consumer: %s", exc)
        raise


def extract_event_id(payload: Dict[str, Any]) -> Optional[str]:
    """Extract event_id or fallback to entity_id."""
    event_id = payload.get("event_id")
    if event_id is not None:
        return str(event_id)

    entity_id = payload.get("entity_id")
    if entity_id is not None:
        return str(entity_id)

    return None


def build_event_processing_service() -> EventProcessingService:
    """
    Create the event-processing service.

    For now, this is created without extra dependencies.
    Later you can inject:
    - forecast_service
    - decision_log_writer
    """
    return EventProcessingService()


def process_single_message(
    *,
    topic: str,
    payload: Dict[str, Any],
    event_processing_service: EventProcessingService,
    summary: ConsumerRunSummary,
) -> None:
    """Process one Kafka event payload and update summary counters."""
    event_id = extract_event_id(payload)

    logger.info(
        "Received event for processing | topic=%s | event_id=%s",
        topic,
        event_id,
    )

    result = event_processing_service.process_event(payload)

    logger.info(
        "Processed event result | topic=%s | event_id=%s | status=%s | action_taken=%s | message=%s",
        topic,
        result.event_id,
        result.status,
        result.action_taken,
        result.message,
    )

    logger.info(
        "Processed decision payload | topic=%s | event_id=%s | payload=%s",
        topic,
        result.event_id,
        json.dumps(result.decision_payload, ensure_ascii=False, default=str),
    )

    if result.warnings:
        logger.warning(
            "Processing warnings | topic=%s | event_id=%s | warnings=%s",
            topic,
            result.event_id,
            result.warnings,
        )

    if result.status == "processed":
        summary.increment_processed(topic)
    elif result.status == "ignored":
        summary.increment_ignored(topic)
    else:
        summary.increment_error(topic)


def consume_messages(
    consumer: KafkaConsumer,
    event_processing_service: EventProcessingService,
    max_messages: Optional[int] = None,
) -> ConsumerRunSummary:
    """
    Consume Kafka messages, process each event, and return summary counts.
    """
    summary = ConsumerRunSummary()
    total_messages = 0

    logger.info("Starting Kafka consumption loop...")

    try:
        for message in consumer:
            topic = message.topic
            payload = message.value if isinstance(message.value, dict) else {}

            summary.increment_consumed(topic)
            total_messages += 1

            logger.info(
                "Consumed message | topic=%s | partition=%s | offset=%s | key=%s | event_id=%s",
                topic,
                message.partition,
                message.offset,
                message.key,
                extract_event_id(payload),
            )

            logger.info(
                "Consumed payload | topic=%s | payload=%s",
                topic,
                json.dumps(payload, ensure_ascii=False, default=str),
            )

            if not isinstance(payload, dict) or not payload:
                logger.error(
                    "Invalid or empty payload | topic=%s | partition=%s | offset=%s",
                    topic,
                    message.partition,
                    message.offset,
                )
                summary.increment_error(topic)

                if max_messages is not None and total_messages >= max_messages:
                    logger.info(
                        "Stopping early due to KAFKA_MAX_CONSUME_MESSAGES=%s",
                        max_messages,
                    )
                    break
                continue

            try:
                process_single_message(
                    topic=topic,
                    payload=payload,
                    event_processing_service=event_processing_service,
                    summary=summary,
                )
            except Exception as exc:
                logger.exception(
                    "Event processing failed | topic=%s | offset=%s | error=%s",
                    topic,
                    message.offset,
                    exc,
                )
                summary.increment_error(topic)

            if max_messages is not None and total_messages >= max_messages:
                logger.info(
                    "Stopping early due to KAFKA_MAX_CONSUME_MESSAGES=%s",
                    max_messages,
                )
                break

    except Exception as exc:
        logger.exception("Kafka consumption failed: %s", exc)
        raise

    logger.info("Kafka consumption loop finished.")
    return summary


def log_summary(summary: ConsumerRunSummary) -> None:
    """Log final Kafka consumer summary."""
    logger.info("Kafka consumer summary:")

    total_consumed = 0
    total_processed = 0
    total_ignored = 0
    total_errors = 0

    for topic in TOPICS:
        consumed = summary.consumed_counts.get(topic, 0)
        processed = summary.processed_counts.get(topic, 0)
        ignored = summary.ignored_counts.get(topic, 0)
        errors = summary.error_counts.get(topic, 0)

        total_consumed += consumed
        total_processed += processed
        total_ignored += ignored
        total_errors += errors

        logger.info(
            "%s | consumed=%s | processed=%s | ignored=%s | errors=%s",
            topic,
            consumed,
            processed,
            ignored,
            errors,
        )

    logger.info(
        "TOTAL | consumed=%s | processed=%s | ignored=%s | errors=%s",
        total_consumed,
        total_processed,
        total_ignored,
        total_errors,
    )


def main() -> None:
    """Entry point for Kafka consumer script."""
    setup_logging()

    consumer: KafkaConsumer | None = None

    try:
        max_messages_raw = os.getenv("KAFKA_MAX_CONSUME_MESSAGES", "").strip()
        max_messages = int(max_messages_raw) if max_messages_raw else None

        event_processing_service = build_event_processing_service()
        consumer = build_kafka_consumer()

        summary = consume_messages(
            consumer=consumer,
            event_processing_service=event_processing_service,
            max_messages=max_messages,
        )
        log_summary(summary)

        logger.info("Kafka consumer completed successfully.")

    except Exception as exc:
        logger.exception("Kafka consumer script failed: %s", exc)
        raise

    finally:
        if consumer is not None:
            try:
                consumer.close()
            except Exception:
                logger.warning("Kafka consumer close encountered a non-fatal issue.")

        logger.info("Kafka consumer script finished.")


if __name__ == "__main__":
    main()
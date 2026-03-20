from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from kafka import KafkaConsumer

from app.core.logging import get_logger, setup_logging


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
# Kafka Helpers
# =========================================================
def parse_topics_from_env(default_topics: List[str]) -> List[str]:
    raw_topics = os.getenv("KAFKA_CONSUMER_TOPICS", "").strip()

    if not raw_topics:
        return default_topics

    parsed_topics = [topic.strip() for topic in raw_topics.split(",") if topic.strip()]
    return parsed_topics if parsed_topics else default_topics


def build_kafka_consumer() -> KafkaConsumer:
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    client_id = os.getenv("KAFKA_CONSUMER_CLIENT_ID", "edip-phase-6-consumer")
    group_id = os.getenv("KAFKA_CONSUMER_GROUP_ID", "edip-phase-6-consumer-group")
    auto_offset_reset = os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest").strip().lower()
    enable_auto_commit = os.getenv("KAFKA_ENABLE_AUTO_COMMIT", "true").strip().lower() == "true"
    consumer_timeout_ms = int(os.getenv("KAFKA_CONSUMER_TIMEOUT_MS", "10000"))

    topics = parse_topics_from_env(TOPICS)

    logger.info("Creating Kafka consumer with bootstrap servers: %s", bootstrap_servers)
    logger.info("Consumer topics: %s", topics)
    logger.info("Consumer group_id: %s | auto_offset_reset: %s", group_id, auto_offset_reset)

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


def extract_event_id(payload: Dict) -> Optional[str]:
    event_id = payload.get("event_id")
    if event_id is not None:
        return str(event_id)

    entity_id = payload.get("entity_id")
    if entity_id is not None:
        return str(entity_id)

    return None


def consume_messages(consumer: KafkaConsumer, max_messages: Optional[int] = None) -> Dict[str, int]:
    topic_counts: Dict[str, int] = {}
    total_messages = 0

    logger.info("Starting Kafka consumption loop...")

    try:
        for message in consumer:
            payload = message.value if isinstance(message.value, dict) else {}
            event_id = extract_event_id(payload)

            topic_counts[message.topic] = topic_counts.get(message.topic, 0) + 1
            total_messages += 1

            logger.info(
                "Consumed message | topic=%s | partition=%s | offset=%s | key=%s | event_id=%s",
                message.topic,
                message.partition,
                message.offset,
                message.key,
                event_id,
            )

            logger.info(
                "Consumed payload | topic=%s | payload=%s",
                message.topic,
                json.dumps(payload, ensure_ascii=False),
            )

            if max_messages is not None and total_messages >= max_messages:
                logger.info("Stopping early due to KAFKA_MAX_CONSUME_MESSAGES=%s", max_messages)
                break

    except Exception as exc:
        logger.exception("Kafka consumption failed: %s", exc)
        raise

    logger.info("Kafka consumption loop finished.")
    return topic_counts


def log_summary(topic_counts: Dict[str, int]) -> None:
    logger.info("Kafka consumer summary:")

    total_messages = 0
    for topic in TOPICS:
        count = topic_counts.get(topic, 0)
        total_messages += count
        logger.info("%s | consumed=%s", topic, count)

    logger.info("TOTAL | consumed=%s", total_messages)


def main() -> None:
    setup_logging()

    consumer: KafkaConsumer | None = None

    try:
        max_messages_raw = os.getenv("KAFKA_MAX_CONSUME_MESSAGES", "").strip()
        max_messages = int(max_messages_raw) if max_messages_raw else None

        consumer = build_kafka_consumer()
        topic_counts = consume_messages(consumer=consumer, max_messages=max_messages)
        log_summary(topic_counts)

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
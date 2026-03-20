# scripts/init_kafka_topics.py

from __future__ import annotations

import os
import time
from typing import Dict, List

from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

from app.core.logging import get_logger, setup_logging


logger = get_logger(__name__)


# Official EDIP Kafka topics
TOPICS: Dict[str, Dict[str, int]] = {
    "sales.order.created": {"partitions": 3, "replication_factor": 1},
    "sales.order.completed": {"partitions": 3, "replication_factor": 1},
    "inventory.stock.updated": {"partitions": 3, "replication_factor": 1},
    "inventory.low_stock.alert": {"partitions": 3, "replication_factor": 1},
    "logistics.shipment.delayed": {"partitions": 3, "replication_factor": 1},
    "returns.return.created": {"partitions": 3, "replication_factor": 1},
    "planning.forecast.generated": {"partitions": 3, "replication_factor": 1},
    "planning.replenishment.approved": {"partitions": 3, "replication_factor": 1},
}


def build_admin_client() -> KafkaAdminClient:
    """
    Build Kafka admin client using environment variables.
    """
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    client_id = os.getenv("KAFKA_ADMIN_CLIENT_ID", "edip-kafka-topic-init")

    logger.info("Creating Kafka admin client with bootstrap servers: %s", bootstrap_servers)

    return KafkaAdminClient(
        bootstrap_servers=bootstrap_servers.split(","),
        client_id=client_id,
    )


def wait_for_kafka(max_attempts: int = 20, sleep_seconds: int = 3) -> KafkaAdminClient:
    """
    Retry until Kafka admin connection works.
    """
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            logger.info("Waiting for Kafka... attempt %s/%s", attempt, max_attempts)
            admin_client = build_admin_client()
            _ = admin_client.list_topics()
            logger.info("Kafka is reachable.")
            return admin_client
        except Exception as exc:
            last_error = exc
            logger.warning("Kafka not ready yet: %s", exc)
            time.sleep(sleep_seconds)

    raise RuntimeError("Kafka did not become ready in time.") from last_error


def build_new_topics() -> List[NewTopic]:
    """
    Convert TOPICS config into Kafka NewTopic objects.
    """
    new_topics: List[NewTopic] = []

    for topic_name, config in TOPICS.items():
        new_topics.append(
            NewTopic(
                name=topic_name,
                num_partitions=config["partitions"],
                replication_factor=config["replication_factor"],
            )
        )

    return new_topics


def create_topics(admin_client: KafkaAdminClient) -> None:
    """
    Create only missing topics.
    """
    existing_topics = set(admin_client.list_topics())
    logger.info("Existing Kafka topics: %s", sorted(existing_topics))

    topics_to_create = [
        topic
        for topic in build_new_topics()
        if topic.name not in existing_topics
    ]

    if not topics_to_create:
        logger.info("All required Kafka topics already exist. Nothing to create.")
        return

    logger.info(
        "Creating missing Kafka topics: %s",
        [topic.name for topic in topics_to_create],
    )

    try:
        admin_client.create_topics(
            new_topics=topics_to_create,
            validate_only=False,
        )
        logger.info("Kafka topics created successfully.")
    except TopicAlreadyExistsError:
        logger.warning("One or more topics already exist. Continuing safely.")
    except Exception as exc:
        logger.exception("Failed to create Kafka topics: %s", exc)
        raise

    final_topics = sorted(admin_client.list_topics())
    logger.info("Final Kafka topic list: %s", final_topics)


def main() -> None:
    """
    Entry point for one-time Kafka topic initialization.
    """
    setup_logging()

    admin_client: KafkaAdminClient | None = None

    try:
        admin_client = wait_for_kafka()
        create_topics(admin_client)
        logger.info("Kafka topic initialization completed successfully.")
    except Exception as exc:
        logger.exception("Kafka topic initialization script failed: %s", exc)
        raise
    finally:
        if admin_client is not None:
            try:
                admin_client.close()
            except Exception:
                logger.warning("Kafka admin client close encountered a non-fatal issue.")

        logger.info("Kafka topic initialization script finished.")


if __name__ == "__main__":
    main()
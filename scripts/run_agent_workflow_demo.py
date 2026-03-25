# scripts\run_agent_workflow_demo.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest import result
import warnings

from dotenv import load_dotenv

from app.core.logging import get_logger, setup_logging
from app.services.agent_workflow_service import (
    AgentWorkflowRequest,
    build_agent_workflow_service,
)
from app.services.forecast_service import build_forecast_service
from app.services.rag_query_service import build_rag_query_service


logger = get_logger(__name__)


# =========================================================
# Environment bootstrap
# =========================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)


# =========================================================
# Temporary adapters
# =========================================================
class RagRetrievalAdapter:
    """
    Temporary adapter to make the current RAG query service compatible with
    RetrievalServiceProtocol expected by RetrievalAgent.

    Why needed:
    - RetrievalAgent expects retrieve_context(...)
    - current RagQueryService may still expose answer_question(...) as the main entry
    - this adapter keeps the demo runnable while architecture is being finalized
    """

    def __init__(self, rag_query_service: Any) -> None:
        self.rag_query_service = rag_query_service

    def retrieve_context(
        self,
        question: str,
        *,
        top_k: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Return raw retrieval matches in the normalized format expected by the agent.

        Preferred path:
        - use native retrieve_context(...) if present

        Fallback path:
        - use answer_question(...)
        - convert returned sources into retrieval-like matches
        """
        logger.info("Retrieval debug | question=%s", question)
        logger.info("Retrieval debug | metadata_filter=%s", metadata_filter)
        logger.info("Retrieval debug | top_k=%s | min_score=%s", top_k, min_score)

        if hasattr(self.rag_query_service, "retrieve_context"):
            matches = self.rag_query_service.retrieve_context(
                question,
                top_k=top_k,
                metadata_filter=metadata_filter,
                min_score=min_score,
            )
            logger.info("Retrieval debug | native retrieve_context count=%s", len(matches))
            if matches:
                logger.info("Retrieval debug | first native match=%s", matches[0])

            return matches

        if hasattr(self.rag_query_service, "answer_question"):
            result = self.rag_query_service.answer_question(
                question,
                top_k=top_k,
                metadata_filter=metadata_filter,
                min_score=min_score,
            )

            normalized_matches: List[Dict[str, Any]] = []
            sources = getattr(result, "sources", []) or []

            for source in sources:
                metadata = {
                    "chunk_id": getattr(source, "chunk_id", None),
                    "document_id": getattr(source, "document_id", None),
                    "document_title": getattr(source, "document_title", None),
                    "source_path": getattr(source, "source_path", None),
                    "document_type": getattr(source, "document_type", None),
                    "business_domain": getattr(source, "business_domain", None),
                    "heading_path": getattr(source, "heading_path", None),
                    "topic": getattr(source, "topic", None),
                    "chunk_text": getattr(source, "text_preview", None),
                }

                normalized_matches.append(
                    {
                        "id": getattr(source, "chunk_id", None),
                        "score": float(getattr(source, "score", 0.0) or 0.0),
                        "metadata": metadata,
                    }
                )

            logger.info(
                "Retrieval debug | normalized answer_question match count=%s",
                len(normalized_matches)
            )
            if normalized_matches:
                logger.info(
                    "Retrieval debug | first normalized match=%s",
                normalized_matches[0],
            )
            return normalized_matches

        raise RuntimeError(
            "RAG service does not expose retrieve_context(...) or answer_question(...)."
        )


# =========================================================
# Main runner
# =========================================================
def print_compact_workflow_summary(result: dict) -> None:
    """
    Print a short, business-friendly workflow summary instead of the full JSON payload.
    """
    planner_plan = result.get("planner_plan", {})
    analytics_result = result.get("analytics_result", {})
    execution_result = result.get("execution_result", {})
    warnings = result.get("warnings", [])

    forecast_payload = analytics_result.get("forecast_payload", {})
    recommendation_payload = analytics_result.get("recommendation_payload", {})

    print("\n" + "=" * 80)
    print("EDIP AGENT WORKFLOW SUMMARY")
    print("=" * 80)
    print(f"Question: {result.get('question')}")
    print(f"Workflow trace: {result.get('workflow_trace', [])}")

    task_type = planner_plan.get("task_type")
    output_type = execution_result.get("output_type")
    status = execution_result.get("status")

    print(f"Task type: {getattr(task_type, 'value', task_type)}")
    print(f"Output type: {getattr(output_type, 'value', output_type)}")

    reasoning_result = result.get("reasoning_result", {})

    print("\n--- Why This Decision Was Made ---")
    print(f"Reasoning summary: {reasoning_result.get('reasoning_summary')}")

    rationale_points = reasoning_result.get("rationale_points", [])
    if rationale_points:
        for item in rationale_points:
            print(f"- {item}")
    else:
         print("No reasoning details available.")

    print(f"Final status: {getattr(status, 'value', status)}")
    print(f"Final message: {execution_result.get('final_message')}")

    print("\n--- Forecast Summary ---")
    print(f"Forecast units: {forecast_payload.get('forecast_units')}")
    print(f"Forecast lower bound: {forecast_payload.get('forecast_lower_bound')}")
    print(f"Forecast upper bound: {forecast_payload.get('forecast_upper_bound')}")
    print(f"Confidence score: {forecast_payload.get('confidence_score')}")

    print("\n--- Recommendation Summary ---")
    print(f"Recommended order qty: {recommendation_payload.get('recommended_order_qty')}")
    print(f"Recommended transfer qty: {recommendation_payload.get('recommended_transfer_qty')}")
    print(f"Priority level: {recommendation_payload.get('priority_level')}")
    print(f"Reason code: {recommendation_payload.get('reason_code')}")
    print(f"Expected stockout risk: {recommendation_payload.get('expected_stockout_risk')}")
    print(f"Expected service level: {recommendation_payload.get('expected_service_level')}")

    print("\n--- Warnings ---")
    if warnings:
        for item in warnings:
            print(f"- {item}")
    else:
        print("None")

    print("=" * 80 + "\n")

    # Also print the full reasoning result for debugging purposes, since it may contain additional fields not included in the compact summary.
    print("\nFull reasoning result for debugging:")
    print(reasoning_result) 

def main() -> None:
    """
    Run one end-to-end EDIP LangGraph workflow demo.
    """
    setup_logging()

    logger.info("Starting EDIP agent workflow demo.")

    # Build existing project services.
    rag_query_service = build_rag_query_service()
    forecast_service = build_forecast_service()

    # Adapt retrieval service to the RetrievalAgent protocol.
    retrieval_service = RagRetrievalAdapter(rag_query_service=rag_query_service)

    # Build workflow service.
    workflow_service = build_agent_workflow_service(
        retrieval_service=retrieval_service,
        forecast_service=forecast_service,
    )

    # One realistic demo request.
    request = AgentWorkflowRequest(
        question="Why was urgent replenishment recommended for SKU-100245?",
        user_role=None,
        region_scope=None,
        product_id=245,
        store_id=3,
        region_id=1,
        horizon_days=7,
        include_recommendations=True,
        require_approval=False,
        metadata={
            "channel": "demo_script",
            "request_origin": "local_runner",
        },
    )

    result = workflow_service.run_workflow(request)

    logger.info("EDIP agent workflow demo completed successfully.")
    logger.info("Workflow trace: %s", result.get("workflow_trace", []))
    logger.info("Warnings: %s", result.get("warnings", []))

    print_compact_workflow_summary(result)
    

if __name__ == "__main__":
    main()
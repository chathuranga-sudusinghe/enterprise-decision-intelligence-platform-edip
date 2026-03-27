from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
import os
import pytest

client = TestClient(app)


# =========================================================
# Official demo payloads
# =========================================================
URGENT_REPLENISHMENT_PAYLOAD = {
    "question": "Why was urgent replenishment recommended for SKU-100245 at store 210?",
    "user_role": "planner",
    "region_scope": "west",
    "product_id": 100245,
    "store_id": 210,
    "warehouse_id": 12,
    "region_id": 3,
    "horizon_days": 7,
    "include_recommendations": True,
    "require_approval": False,
    "metadata": {
        "source": "official_demo",
        "scenario": "urgent_replenishment",
        "channel": "frontend",
    },
}

STOCKOUT_RISK_PAYLOAD = {
    "question": "Is there a high stockout risk for SKU-100245 at store 210 next week?",
    "user_role": "planner",
    "region_scope": "west",
    "product_id": 100245,
    "store_id": 210,
    "warehouse_id": 12,
    "region_id": 3,
    "horizon_days": 7,
    "include_recommendations": True,
    "require_approval": False,
    "metadata": {
        "source": "official_demo",
        "scenario": "stockout_risk",
        "channel": "swagger",
    },
}

REORDER_VS_TRANSFER_PAYLOAD = {
    "question": "Should store 210 reorder SKU-100245 or transfer stock from another location?",
    "user_role": "planner",
    "region_scope": "west",
    "product_id": 100245,
    "store_id": 210,
    "warehouse_id": 12,
    "region_id": 3,
    "horizon_days": 7,
    "include_recommendations": True,
    "require_approval": False,
    "metadata": {
        "source": "official_demo",
        "scenario": "reorder_vs_transfer",
        "channel": "swagger",
    },
}


# =========================================================
# Small helpers
# =========================================================
def assert_common_workflow_response(data: dict) -> None:
    """Validate the common minimum structure of a successful workflow response."""
    assert "question" in data
    assert "business_answer" in data
    assert "decision_summary" in data
    assert "forecast_summary" in data
    assert "recommendation_summary" in data

    decision_summary = data["decision_summary"]
    forecast_summary = data["forecast_summary"]
    recommendation_summary = data["recommendation_summary"]

    assert decision_summary["status"] == "ready"
    assert decision_summary["output_type"] == "recommendation"
    assert isinstance(decision_summary.get("final_message"), str)
    assert decision_summary["final_message"].strip() != ""

    assert "forecast_units" in forecast_summary
    assert "forecast_lower_bound" in forecast_summary
    assert "forecast_upper_bound" in forecast_summary
    assert "confidence_score" in forecast_summary

    assert "recommended_order_qty" in recommendation_summary
    assert "recommended_transfer_qty" in recommendation_summary
    assert "priority_level" in recommendation_summary
    assert "reason_code" in recommendation_summary


# =========================================================
# Health test
# =========================================================
def test_agent_workflow_health() -> None:
    """Health endpoint should respond successfully."""
    response = client.get("/agents/workflow/health")

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)
    assert data


# =========================================================
# Official demo tests
# =========================================================
@pytest.mark.skipif(
    os.getenv("CI") == "true",
    reason="Skipped in GitHub Actions CI because it depends on external Pinecone access.",
)
def test_agent_workflow_urgent_replenishment_demo() -> None:
    """Official urgent replenishment demo should return a valid recommendation."""
    response = client.post(
        "/agents/workflow/run",
        json=URGENT_REPLENISHMENT_PAYLOAD,
    )

    assert response.status_code == 200

    data = response.json()
    assert_common_workflow_response(data)

    decision = data["business_answer"].get("decision")
    assert decision is not None
    assert "reorder" in decision.lower()

    assert data["recommendation_summary"]["recommended_order_qty"] is not None
    assert data["recommendation_summary"]["reason_code"] is not None


def test_agent_workflow_stockout_risk_demo() -> None:
    """Official stockout risk demo should return a valid risk-oriented recommendation."""
    response = client.post(
        "/agents/workflow/run",
        json=STOCKOUT_RISK_PAYLOAD,
    )

    assert response.status_code == 200

    data = response.json()
    assert_common_workflow_response(data)

    assert "stockout" in data["question"].lower()
    assert data["recommendation_summary"]["priority_level"] is not None
    assert data["recommendation_summary"]["reason_code"] is not None


def test_agent_workflow_reorder_vs_transfer_demo() -> None:
    """Official reorder-vs-transfer demo should return a clear action recommendation."""
    response = client.post(
        "/agents/workflow/run",
        json=REORDER_VS_TRANSFER_PAYLOAD,
    )

    assert response.status_code == 200

    data = response.json()
    assert_common_workflow_response(data)

    decision_text = data["business_answer"]["decision"].lower()
    final_message = data["decision_summary"]["final_message"].lower()

    assert "reorder" in decision_text or "transfer" in decision_text
    assert "reorder" in final_message or "transfer" in final_message

    assert data["recommendation_summary"]["recommended_order_qty"] is not None
    assert data["recommendation_summary"]["recommended_transfer_qty"] is not None
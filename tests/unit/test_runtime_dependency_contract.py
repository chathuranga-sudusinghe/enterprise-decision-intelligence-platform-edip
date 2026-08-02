from __future__ import annotations

from importlib import import_module
from typing import NoReturn

from langgraph.graph import END, StateGraph

from app.agents.langgraph_workflow import EDIPLangGraphWorkflow


class DeterministicAgentDouble:
    """Inert agent double used only to verify graph construction."""

    def __getattr__(self, name: str) -> NoReturn:
        raise AssertionError(f"Agent method must not run during construction: {name}")


def test_app_main_imports() -> None:
    app_main = import_module("app.main")

    assert app_main.app is not None


def test_langgraph_graph_contract_is_available() -> None:
    assert END is not None
    assert StateGraph is not None


def test_edip_langgraph_workflow_constructs_with_deterministic_doubles() -> None:
    agent = DeterministicAgentDouble()

    workflow = EDIPLangGraphWorkflow(
        planner_agent=agent,
        retrieval_agent=agent,
        reasoning_agent=agent,
        analytics_agent=agent,
        execution_agent=agent,
    )

    assert workflow.graph is not None
    assert workflow.planner_agent is agent
    assert workflow.retrieval_agent is agent
    assert workflow.reasoning_agent is agent
    assert workflow.analytics_agent is agent
    assert workflow.execution_agent is agent

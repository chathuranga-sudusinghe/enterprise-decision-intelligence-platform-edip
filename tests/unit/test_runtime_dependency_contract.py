from __future__ import annotations

from importlib import import_module

from langgraph.graph import END, StateGraph


def test_app_main_imports() -> None:
    app_main = import_module("app.main")

    assert app_main.app is not None


def test_langgraph_graph_contract_is_available() -> None:
    assert END is not None
    assert StateGraph is not None

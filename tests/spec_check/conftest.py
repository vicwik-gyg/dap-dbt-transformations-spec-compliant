"""Shared test fixtures for spec-check rules."""

from __future__ import annotations


def make_model_node(
    name: str,
    path: str = "",
    fqn: list[str] | None = None,
    columns: dict | None = None,
    description: str = "A test model",
    depends_on_nodes: list[str] | None = None,
    raw_code: str = "",
    tags: list[str] | None = None,
    unique_id: str = "",
) -> dict:
    """Create a synthetic model node for testing."""
    if not path:
        # Infer from fqn
        path = "/".join((fqn or ["project", "staging", name])[1:]) + f"/{name}.sql"
    if fqn is None:
        fqn = ["project", "staging", name]
    if columns is None:
        columns = {}
    if not unique_id:
        unique_id = f"model.project.{name}"

    return {
        "name": name,
        "unique_id": unique_id,
        "resource_type": "model",
        "package_name": "project",
        "path": path,
        "fqn": fqn,
        "config": {"materialized": "view"},
        "columns": columns,
        "description": description,
        "depends_on": {"nodes": depends_on_nodes or []},
        "raw_code": raw_code,
        "tags": tags or [],
        "schema": "test_schema",
        "meta": {},
    }


def make_test_node(
    model_unique_id: str,
    column_name: str = "",
    test_name: str = "not_null",
) -> dict:
    """Create a synthetic test node."""
    return {
        "name": f"{test_name}_{column_name}",
        "unique_id": f"test.project.{test_name}_{column_name}",
        "resource_type": "test",
        "column_name": column_name,
        "test_metadata": {"name": test_name},
        "depends_on": {"nodes": [model_unique_id]},
    }


def make_manifest(
    nodes: list[dict] | None = None,
    semantic_models: dict | None = None,
) -> dict:
    """Create a synthetic manifest for testing."""
    node_dict = {}
    for n in (nodes or []):
        node_dict[n["unique_id"]] = n

    return {
        "metadata": {"project_name": "project"},
        "nodes": node_dict,
        "sources": {},
        "semantic_models": semantic_models or {},
    }

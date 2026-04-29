"""Manifest loader: reads and indexes dbt manifest.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def load_manifest(manifest_path: Path | None = None) -> dict[str, Any]:
    """Load manifest.json and return the parsed dict.

    Looks in target/manifest.json relative to cwd if no path given.
    """
    if manifest_path is None:
        manifest_path = Path.cwd() / "target" / "manifest.json"

    if not manifest_path.exists():
        print(
            f"Error: manifest not found at {manifest_path}\n"
            "Run 'dbt parse' first to generate target/manifest.json",
            file=sys.stderr,
        )
        sys.exit(2)

    with manifest_path.open() as f:
        return json.load(f)


def get_model_nodes(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract all model nodes from manifest."""
    nodes = manifest.get("nodes", {})
    return [
        node
        for node in nodes.values()
        if node.get("resource_type") == "model"
        and node.get("package_name") == manifest["metadata"]["project_name"]
    ]


def get_test_nodes(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract all test nodes from manifest."""
    nodes = manifest.get("nodes", {})
    return [node for node in nodes.values() if node.get("resource_type") == "test"]


def get_semantic_models(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract semantic model definitions."""
    return list(manifest.get("semantic_models", {}).values())


def get_tests_for_model(
    model_unique_id: str, manifest: dict[str, Any]
) -> list[dict[str, Any]]:
    """Get all tests that depend on a specific model."""
    tests = get_test_nodes(manifest)
    return [
        t
        for t in tests
        if model_unique_id in t.get("depends_on", {}).get("nodes", [])
    ]


def get_layer(node: dict[str, Any]) -> str:
    """Determine model layer from fqn or path."""
    fqn = node.get("fqn", [])
    if len(fqn) >= 2:
        layer = fqn[1]
        if layer in ("staging", "intermediate", "marts", "semantic_models"):
            return layer
    path = node.get("path", "")
    for layer in ("staging", "intermediate", "marts", "semantic_models"):
        if path.startswith(f"{layer}/"):
            return layer
    return "unknown"


def get_model_prefix(node: dict[str, Any]) -> str:
    """Get the naming prefix (stg_, int_, fct_, dim_, agg_) from model name."""
    name = node.get("name", "")
    for prefix in ("stg_", "int_", "fct_", "dim_", "agg_"):
        if name.startswith(prefix):
            return prefix
    return ""


def is_rule_suppressed(node: dict[str, Any], rule_name: str) -> tuple[bool, str | None]:
    """Check if a rule is suppressed for a node via meta pragma.

    Looks for spec_check_suppress in model-level or column-level meta:
        meta:
          spec_check_suppress:
            - rule: "tests.accepted_values_on_enums"
              justification: "Open-domain column with unbounded values"

    Or the shorthand list form:
        meta:
          spec_check_suppress: ["tests.accepted_values_on_enums"]

    Returns (suppressed, justification) tuple.
    """
    meta = node.get("config", {}).get("meta", {})
    if not meta:
        meta = node.get("meta", {})

    suppressions = meta.get("spec_check_suppress", [])
    if not suppressions:
        return False, None

    for entry in suppressions:
        if isinstance(entry, str):
            if entry == rule_name:
                return True, None
        elif isinstance(entry, dict):
            if entry.get("rule") == rule_name:
                return True, entry.get("justification")

    return False, None


def is_column_rule_suppressed(
    node: dict[str, Any], column_name: str, rule_name: str
) -> tuple[bool, str | None]:
    """Check if a rule is suppressed for a specific column via column-level meta.

    Looks in the column's meta for spec_check_suppress pragma.
    """
    columns = node.get("columns", {})
    col_info = columns.get(column_name, {})
    meta = col_info.get("meta", {})

    suppressions = meta.get("spec_check_suppress", [])
    if not suppressions:
        return False, None

    for entry in suppressions:
        if isinstance(entry, str):
            if entry == rule_name:
                return True, None
        elif isinstance(entry, dict):
            if entry.get("rule") == rule_name:
                return True, entry.get("justification")

    return False, None


def model_exists_in_manifest(model_name: str, manifest: dict[str, Any]) -> bool:
    """Check if a model (by name) exists in the manifest."""
    nodes = manifest.get("nodes", {})
    for node in nodes.values():
        if node.get("resource_type") == "model" and node.get("name") == model_name:
            return True
    return False


# Models that are dbt-framework-required utilities, not user-authored content.
_FRAMEWORK_MODELS = frozenset({"metricflow_time_spine"})


def is_framework_model(node: dict[str, Any]) -> bool:
    """Check if a node is a dbt-framework utility model (not user content)."""
    return node.get("name", "") in _FRAMEWORK_MODELS



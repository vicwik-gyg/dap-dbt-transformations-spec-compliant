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

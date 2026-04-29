"""Naming convention rules."""

from __future__ import annotations

import re
from typing import Any

from ..manifest import get_layer, get_model_prefix
from ..models import Result, RuleResult
from ..registry import rule

SPEC_REF_NAMING = "04-target-state/conventions.md#naming"

LAYER_PREFIXES = {
    "staging": ["stg_"],
    "intermediate": ["int_"],
    "marts": ["fct_", "dim_", "agg_"],
}

SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")


@rule(
    name="naming.table_prefix",
    description="Model name uses correct layer prefix (stg_/int_/fct_/dim_/agg_)",
    applies_to=["staging", "intermediate", "marts"],
    spec_ref=SPEC_REF_NAMING,
)
def check_table_prefix(node: dict[str, Any], manifest: dict[str, Any]) -> RuleResult:
    name = node["name"]
    layer = get_layer(node)
    model_name = node["name"]

    allowed = LAYER_PREFIXES.get(layer, [])
    if not allowed:
        return RuleResult(
            model=model_name, rule="naming.table_prefix", result=Result.NA
        )

    prefix = get_model_prefix(node)
    if prefix in allowed:
        return RuleResult(
            model=model_name,
            rule="naming.table_prefix",
            result=Result.PASS,
            spec_ref=SPEC_REF_NAMING,
        )

    return RuleResult(
        model=model_name,
        rule="naming.table_prefix",
        result=Result.DEVIATES,
        finding=f"Expected prefix {allowed} for layer '{layer}', got '{name}'",
        spec_ref=SPEC_REF_NAMING,
    )


@rule(
    name="naming.column_snake_case",
    description="All columns use snake_case naming",
    applies_to=["all"],
    spec_ref=SPEC_REF_NAMING,
)
def check_column_snake_case(
    node: dict[str, Any], manifest: dict[str, Any]
) -> RuleResult:
    model_name = node["name"]
    columns = node.get("columns", {})

    if not columns:
        return RuleResult(
            model=model_name, rule="naming.column_snake_case", result=Result.NA
        )

    violations = []
    for col_name in columns:
        if not SNAKE_CASE_RE.match(col_name):
            violations.append(col_name)

    if violations:
        return RuleResult(
            model=model_name,
            rule="naming.column_snake_case",
            result=Result.DEVIATES,
            finding=f"Non-snake_case columns: {', '.join(violations[:5])}",
            spec_ref=SPEC_REF_NAMING,
        )

    return RuleResult(
        model=model_name,
        rule="naming.column_snake_case",
        result=Result.PASS,
        spec_ref=SPEC_REF_NAMING,
    )


@rule(
    name="naming.source_style",
    description="Source references follow stg_<source>__<entity> convention",
    applies_to=["staging"],
    spec_ref=SPEC_REF_NAMING,
)
def check_source_style(node: dict[str, Any], manifest: dict[str, Any]) -> RuleResult:
    model_name = node["name"]
    layer = get_layer(node)

    if layer != "staging":
        return RuleResult(
            model=model_name, rule="naming.source_style", result=Result.NA
        )

    # Staging models should follow stg_<source>__<entity> pattern
    # The double underscore separates source from entity
    if not model_name.startswith("stg_"):
        return RuleResult(
            model=model_name,
            rule="naming.source_style",
            result=Result.DEVIATES,
            finding=f"Staging model '{model_name}' missing stg_ prefix",
            spec_ref=SPEC_REF_NAMING,
        )

    # Check for double-underscore separator
    after_stg = model_name[4:]  # remove 'stg_'
    if "__" not in after_stg:
        return RuleResult(
            model=model_name,
            rule="naming.source_style",
            result=Result.DEVIATES,
            finding=f"Staging model '{model_name}' missing '__' separator (expected stg_<source>__<entity>)",
            spec_ref=SPEC_REF_NAMING,
        )

    return RuleResult(
        model=model_name,
        rule="naming.source_style",
        result=Result.PASS,
        spec_ref=SPEC_REF_NAMING,
    )

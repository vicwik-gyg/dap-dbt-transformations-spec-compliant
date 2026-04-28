"""Layering rules: model lives in the correct directory for its prefix."""

from __future__ import annotations

from typing import Any

from ..manifest import get_layer, get_model_prefix
from ..models import Result, RuleResult
from ..registry import rule

SPEC_REF_LAYERING = "04-target-state/conventions.md#layering"

PREFIX_TO_LAYER = {
    "stg_": "staging",
    "int_": "intermediate",
    "fct_": "marts",
    "dim_": "marts",
    "agg_": "marts",
}


@rule(
    name="layering.correct_layer",
    description="Model file lives in the directory matching its naming prefix",
    applies_to=["staging", "intermediate", "marts"],
    spec_ref=SPEC_REF_LAYERING,
)
def check_correct_layer(node: dict[str, Any], manifest: dict[str, Any]) -> RuleResult:
    model_name = node["name"]
    layer = get_layer(node)
    prefix = get_model_prefix(node)

    if not prefix:
        return RuleResult(
            model=model_name,
            rule="layering.correct_layer",
            result=Result.DEVIATES,
            finding=f"Model '{model_name}' has no recognized layer prefix",
            spec_ref=SPEC_REF_LAYERING,
        )

    expected_layer = PREFIX_TO_LAYER.get(prefix, "")
    if layer == expected_layer:
        return RuleResult(
            model=model_name,
            rule="layering.correct_layer",
            result=Result.PASS,
            spec_ref=SPEC_REF_LAYERING,
        )

    return RuleResult(
        model=model_name,
        rule="layering.correct_layer",
        result=Result.DEVIATES,
        finding=f"Model with prefix '{prefix}' in '{layer}/' but expected '{expected_layer}/'",
        spec_ref=SPEC_REF_LAYERING,
    )

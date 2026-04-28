"""Semantic layer rules."""

from __future__ import annotations

from typing import Any

from ..manifest import get_model_prefix
from ..models import Result, RuleResult
from ..registry import rule

SPEC_REF_SEMANTIC = "04-target-state/conventions.md#semantic-layer"


@rule(
    name="semantic.marts_have_semantic_model",
    description="Core mart models (fct_/dim_) have a corresponding semantic model",
    applies_to=["marts"],
    spec_ref=SPEC_REF_SEMANTIC,
)
def check_marts_have_semantic_model(
    node: dict[str, Any], manifest: dict[str, Any]
) -> RuleResult:
    model_name = node["name"]
    prefix = get_model_prefix(node)

    # Only core facts need semantic models; dims and aggs are optional
    if prefix != "fct_":
        return RuleResult(
            model=model_name,
            rule="semantic.marts_have_semantic_model",
            result=Result.NA,
        )

    # Skip snapshots — semantic models are on the base fact
    if "snapshot" in model_name:
        return RuleResult(
            model=model_name,
            rule="semantic.marts_have_semantic_model",
            result=Result.NA,
        )

    # Check if any semantic model references this model
    semantic_models = manifest.get("semantic_models", {})
    model_unique_id = node.get("unique_id", "")

    for sm in semantic_models.values():
        sm_deps = sm.get("depends_on", {}).get("nodes", [])
        if model_unique_id in sm_deps:
            return RuleResult(
                model=model_name,
                rule="semantic.marts_have_semantic_model",
                result=Result.PASS,
                spec_ref=SPEC_REF_SEMANTIC,
            )

        # Also check model ref string
        sm_model_ref = sm.get("model", "")
        if model_name in sm_model_ref:
            return RuleResult(
                model=model_name,
                rule="semantic.marts_have_semantic_model",
                result=Result.PASS,
                spec_ref=SPEC_REF_SEMANTIC,
            )

    return RuleResult(
        model=model_name,
        rule="semantic.marts_have_semantic_model",
        result=Result.DEVIATES,
        finding=f"No semantic model found for '{model_name}'",
        spec_ref=SPEC_REF_SEMANTIC,
    )

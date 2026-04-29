"""Documentation rules."""

from __future__ import annotations

from typing import Any

from ..models import Result, RuleResult
from ..registry import rule

SPEC_REF_DOCS = "04-target-state/conventions.md#documentation"


@rule(
    name="docs.model_description",
    description="Every model has a non-empty description",
    applies_to=["all"],
    spec_ref=SPEC_REF_DOCS,
)
def check_model_description(
    node: dict[str, Any], manifest: dict[str, Any]
) -> RuleResult:
    model_name = node["name"]
    description = node.get("description", "").strip()

    if not description:
        return RuleResult(
            model=model_name,
            rule="docs.model_description",
            result=Result.DEVIATES,
            finding="Model has no description",
            spec_ref=SPEC_REF_DOCS,
        )

    return RuleResult(
        model=model_name,
        rule="docs.model_description",
        result=Result.PASS,
        spec_ref=SPEC_REF_DOCS,
    )


@rule(
    name="docs.column_description",
    description="Every column has a non-empty description",
    applies_to=["all"],
    spec_ref=SPEC_REF_DOCS,
)
def check_column_description(
    node: dict[str, Any], manifest: dict[str, Any]
) -> RuleResult:
    model_name = node["name"]
    columns = node.get("columns", {})

    if not columns:
        return RuleResult(
            model=model_name, rule="docs.column_description", result=Result.NA
        )

    missing = []
    for col_name, col_info in columns.items():
        desc = col_info.get("description", "").strip()
        if not desc:
            missing.append(col_name)

    if missing:
        return RuleResult(
            model=model_name,
            rule="docs.column_description",
            result=Result.DEVIATES,
            finding=f"{len(missing)} columns without description: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}",
            spec_ref=SPEC_REF_DOCS,
        )

    return RuleResult(
        model=model_name,
        rule="docs.column_description",
        result=Result.PASS,
        spec_ref=SPEC_REF_DOCS,
    )

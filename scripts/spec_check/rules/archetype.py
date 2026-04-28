"""Archetype rules: model matches its entity template structure."""

from __future__ import annotations

import re
from typing import Any

from ..manifest import get_layer, get_model_prefix, get_tests_for_model
from ..models import Result, RuleResult
from ..registry import rule

SPEC_REF_ENTITIES = "04-target-state/entities"


@rule(
    name="archetype.staging",
    description="Staging model: one-to-one with source, no joins, minimal transforms",
    applies_to=["staging"],
    spec_ref=f"{SPEC_REF_ENTITIES}/staging-model.md",
)
def check_staging_archetype(
    node: dict[str, Any], manifest: dict[str, Any]
) -> RuleResult:
    model_name = node["name"]

    # Check: depends on exactly one source (no joins)
    deps = node.get("depends_on", {}).get("nodes", [])
    source_deps = [d for d in deps if d.startswith("source.")]
    model_deps = [d for d in deps if d.startswith("model.")]

    findings = []

    if len(source_deps) != 1:
        findings.append(
            f"Expected exactly 1 source dependency, got {len(source_deps)}"
        )

    if model_deps:
        findings.append(
            f"Staging model should not reference other models, refs: {len(model_deps)}"
        )

    # Check SQL for joins (basic heuristic)
    raw_code = node.get("raw_code", "")
    if re.search(r"\bjoin\b", raw_code, re.IGNORECASE):
        findings.append("Contains JOIN — staging models should not join")

    if findings:
        return RuleResult(
            model=model_name,
            rule="archetype.staging",
            result=Result.DEVIATES,
            finding="; ".join(findings),
            spec_ref=f"{SPEC_REF_ENTITIES}/staging-model.md",
        )

    return RuleResult(
        model=model_name,
        rule="archetype.staging",
        result=Result.PASS,
        spec_ref=f"{SPEC_REF_ENTITIES}/staging-model.md",
    )


@rule(
    name="archetype.fct_transaction",
    description="Fact transaction model: has event grain, timestamp columns, numeric measures",
    applies_to=["marts"],
    spec_ref=f"{SPEC_REF_ENTITIES}/fct-transaction.md",
)
def check_fct_transaction(
    node: dict[str, Any], manifest: dict[str, Any]
) -> RuleResult:
    model_name = node["name"]
    prefix = get_model_prefix(node)

    if prefix != "fct_":
        return RuleResult(
            model=model_name, rule="archetype.fct_transaction", result=Result.NA
        )

    # Skip snapshot models — they have their own archetype
    if "snapshot" in model_name or "accumulating" in model_name:
        return RuleResult(
            model=model_name, rule="archetype.fct_transaction", result=Result.NA
        )

    columns = node.get("columns", {})
    col_names = list(columns.keys())
    findings = []

    # Must have at least one _id column (grain)
    id_cols = [c for c in col_names if c.endswith("_id")]
    if not id_cols:
        findings.append("No _id column found (expected event grain PK)")

    # Must have at least one timestamp (_at) or date column
    time_cols = [c for c in col_names if c.endswith("_at") or c.endswith("_date")]
    if not time_cols:
        findings.append("No timestamp (_at) or date (_date) column found")

    if findings:
        return RuleResult(
            model=model_name,
            rule="archetype.fct_transaction",
            result=Result.DEVIATES,
            finding="; ".join(findings),
            spec_ref=f"{SPEC_REF_ENTITIES}/fct-transaction.md",
        )

    return RuleResult(
        model=model_name,
        rule="archetype.fct_transaction",
        result=Result.PASS,
        spec_ref=f"{SPEC_REF_ENTITIES}/fct-transaction.md",
    )


@rule(
    name="archetype.fct_periodic_snapshot",
    description="Periodic snapshot: has date_day grain column, snapshot-interval measures",
    applies_to=["marts"],
    spec_ref=f"{SPEC_REF_ENTITIES}/fct-periodic-snapshot.md",
)
def check_fct_periodic_snapshot(
    node: dict[str, Any], manifest: dict[str, Any]
) -> RuleResult:
    model_name = node["name"]
    prefix = get_model_prefix(node)

    if prefix != "fct_":
        return RuleResult(
            model=model_name, rule="archetype.fct_periodic_snapshot", result=Result.NA
        )

    # Only applies to models with "snapshot" in name but not "accumulating"
    if "snapshot" not in model_name or "accumulating" in model_name:
        return RuleResult(
            model=model_name, rule="archetype.fct_periodic_snapshot", result=Result.NA
        )

    columns = node.get("columns", {})
    col_names = list(columns.keys())
    findings = []

    # Must have a date grain column
    date_cols = [c for c in col_names if "date" in c or "day" in c]
    if not date_cols:
        findings.append("No date/day grain column found for periodic snapshot")

    if findings:
        return RuleResult(
            model=model_name,
            rule="archetype.fct_periodic_snapshot",
            result=Result.DEVIATES,
            finding="; ".join(findings),
            spec_ref=f"{SPEC_REF_ENTITIES}/fct-periodic-snapshot.md",
        )

    return RuleResult(
        model=model_name,
        rule="archetype.fct_periodic_snapshot",
        result=Result.PASS,
        spec_ref=f"{SPEC_REF_ENTITIES}/fct-periodic-snapshot.md",
    )


@rule(
    name="archetype.fct_accumulating_snapshot",
    description="Accumulating snapshot: has milestone timestamps showing process progression",
    applies_to=["marts"],
    spec_ref=f"{SPEC_REF_ENTITIES}/fct-accumulating-snapshot.md",
)
def check_fct_accumulating_snapshot(
    node: dict[str, Any], manifest: dict[str, Any]
) -> RuleResult:
    model_name = node["name"]
    prefix = get_model_prefix(node)

    if prefix != "fct_":
        return RuleResult(
            model=model_name,
            rule="archetype.fct_accumulating_snapshot",
            result=Result.NA,
        )

    # Only applies to accumulating snapshot models
    if "accumulating" not in model_name:
        return RuleResult(
            model=model_name,
            rule="archetype.fct_accumulating_snapshot",
            result=Result.NA,
        )

    columns = node.get("columns", {})
    col_names = list(columns.keys())
    findings = []

    # Must have multiple timestamp columns (milestones)
    at_cols = [c for c in col_names if c.endswith("_at")]
    if len(at_cols) < 2:
        findings.append(
            f"Expected multiple milestone timestamps (_at), found {len(at_cols)}"
        )

    if findings:
        return RuleResult(
            model=model_name,
            rule="archetype.fct_accumulating_snapshot",
            result=Result.DEVIATES,
            finding="; ".join(findings),
            spec_ref=f"{SPEC_REF_ENTITIES}/fct-accumulating-snapshot.md",
        )

    return RuleResult(
        model=model_name,
        rule="archetype.fct_accumulating_snapshot",
        result=Result.PASS,
        spec_ref=f"{SPEC_REF_ENTITIES}/fct-accumulating-snapshot.md",
    )


@rule(
    name="archetype.dim_conformed",
    description="Conformed dimension: has surrogate key, descriptive attributes, no measures",
    applies_to=["marts"],
    spec_ref=f"{SPEC_REF_ENTITIES}/dim-conformed.md",
)
def check_dim_conformed(node: dict[str, Any], manifest: dict[str, Any]) -> RuleResult:
    model_name = node["name"]
    prefix = get_model_prefix(node)

    if prefix != "dim_":
        return RuleResult(
            model=model_name, rule="archetype.dim_conformed", result=Result.NA
        )

    # Skip SCD Type 2 (has its own rule)
    if "history" in model_name or "scd" in model_name:
        return RuleResult(
            model=model_name, rule="archetype.dim_conformed", result=Result.NA
        )

    columns = node.get("columns", {})
    col_names = list(columns.keys())
    findings = []

    # Must have a primary key ending in _id
    id_cols = [c for c in col_names if c.endswith("_id")]
    if not id_cols:
        findings.append("No _id column found (expected surrogate/natural key)")

    if findings:
        return RuleResult(
            model=model_name,
            rule="archetype.dim_conformed",
            result=Result.DEVIATES,
            finding="; ".join(findings),
            spec_ref=f"{SPEC_REF_ENTITIES}/dim-conformed.md",
        )

    return RuleResult(
        model=model_name,
        rule="archetype.dim_conformed",
        result=Result.PASS,
        spec_ref=f"{SPEC_REF_ENTITIES}/dim-conformed.md",
    )


@rule(
    name="archetype.dim_scd_type_2",
    description="SCD Type 2 dimension: has valid_from/valid_to + surrogate key",
    applies_to=["marts"],
    spec_ref=f"{SPEC_REF_ENTITIES}/dim-scd-type-2.md",
)
def check_dim_scd_type_2(node: dict[str, Any], manifest: dict[str, Any]) -> RuleResult:
    model_name = node["name"]
    prefix = get_model_prefix(node)

    if prefix != "dim_":
        return RuleResult(
            model=model_name, rule="archetype.dim_scd_type_2", result=Result.NA
        )

    # Only applies to history/scd models
    if "history" not in model_name and "scd" not in model_name:
        return RuleResult(
            model=model_name, rule="archetype.dim_scd_type_2", result=Result.NA
        )

    columns = node.get("columns", {})
    col_names = list(columns.keys())
    findings = []

    # Must have valid_from and valid_to columns
    has_valid_from = any(
        "valid_from" in c or "effective_from" in c or "start_at" in c
        for c in col_names
    )
    has_valid_to = any(
        "valid_to" in c or "effective_to" in c or "end_at" in c for c in col_names
    )

    if not has_valid_from:
        findings.append("Missing valid_from/effective_from/start_at column")
    if not has_valid_to:
        findings.append("Missing valid_to/effective_to/end_at column")

    # Should have a surrogate key
    sk_cols = [c for c in col_names if c.endswith("_sk") or c.endswith("_key")]
    id_cols = [c for c in col_names if c.endswith("_id")]
    if not sk_cols and not id_cols:
        findings.append("No surrogate key (_sk/_key) or natural key (_id) found")

    if findings:
        return RuleResult(
            model=model_name,
            rule="archetype.dim_scd_type_2",
            result=Result.DEVIATES,
            finding="; ".join(findings),
            spec_ref=f"{SPEC_REF_ENTITIES}/dim-scd-type-2.md",
        )

    return RuleResult(
        model=model_name,
        rule="archetype.dim_scd_type_2",
        result=Result.PASS,
        spec_ref=f"{SPEC_REF_ENTITIES}/dim-scd-type-2.md",
    )


@rule(
    name="archetype.agg_mart",
    description="Aggregate mart: has grain columns + aggregated measures, references fact/dim",
    applies_to=["marts"],
    spec_ref=f"{SPEC_REF_ENTITIES}/agg-mart.md",
)
def check_agg_mart(node: dict[str, Any], manifest: dict[str, Any]) -> RuleResult:
    model_name = node["name"]
    prefix = get_model_prefix(node)

    if prefix != "agg_":
        return RuleResult(
            model=model_name, rule="archetype.agg_mart", result=Result.NA
        )

    columns = node.get("columns", {})
    col_names = list(columns.keys())
    findings = []

    # Must have grain columns (date, id, or dimension attributes)
    grain_cols = [
        c
        for c in col_names
        if c.endswith("_date") or c.endswith("_id") or c.endswith("_name")
    ]
    if not grain_cols:
        findings.append("No obvious grain columns found (expected _date, _id, or _name)")

    # Must reference at least one upstream model
    deps = node.get("depends_on", {}).get("nodes", [])
    model_deps = [d for d in deps if d.startswith("model.")]
    if not model_deps:
        findings.append("No model dependencies — aggregates should reference facts/dims")

    if findings:
        return RuleResult(
            model=model_name,
            rule="archetype.agg_mart",
            result=Result.DEVIATES,
            finding="; ".join(findings),
            spec_ref=f"{SPEC_REF_ENTITIES}/agg-mart.md",
        )

    return RuleResult(
        model=model_name,
        rule="archetype.agg_mart",
        result=Result.PASS,
        spec_ref=f"{SPEC_REF_ENTITIES}/agg-mart.md",
    )


@rule(
    name="archetype.semantic_model",
    description="Semantic model exists with entities + dimensions + measures",
    applies_to=["marts"],
    spec_ref=f"{SPEC_REF_ENTITIES}/semantic-model.md",
)
def check_semantic_model(node: dict[str, Any], manifest: dict[str, Any]) -> RuleResult:
    """Check if a mart model that should have a semantic model actually does."""
    model_name = node["name"]
    prefix = get_model_prefix(node)

    # Only fact and dimension models in marts need semantic models
    if prefix not in ("fct_", "dim_", "agg_"):
        return RuleResult(
            model=model_name, rule="archetype.semantic_model", result=Result.NA
        )

    # Check if there's a semantic model referencing this model
    semantic_models = manifest.get("semantic_models", {})
    model_unique_id = node.get("unique_id", "")

    has_semantic = False
    for sm in semantic_models.values():
        # semantic model references via 'model' field (ref string)
        sm_model_ref = sm.get("model", "")
        if model_name in sm_model_ref or model_unique_id in str(
            sm.get("depends_on", {}).get("nodes", [])
        ):
            has_semantic = True
            # Validate structure
            entities = sm.get("entities", [])
            dimensions = sm.get("dimensions", [])
            measures = sm.get("measures", [])
            findings = []
            if not entities:
                findings.append("Semantic model has no entities defined")
            if not dimensions:
                findings.append("Semantic model has no dimensions defined")
            if not measures:
                findings.append("Semantic model has no measures defined")
            if findings:
                return RuleResult(
                    model=model_name,
                    rule="archetype.semantic_model",
                    result=Result.DEVIATES,
                    finding="; ".join(findings),
                    spec_ref=f"{SPEC_REF_ENTITIES}/semantic-model.md",
                )
            break

    if not has_semantic:
        # NA for models that don't need semantic models (like snapshots, intermediates)
        # Only core transaction facts strictly need them
        if "snapshot" in model_name or "history" in model_name:
            return RuleResult(
                model=model_name, rule="archetype.semantic_model", result=Result.NA
            )
        return RuleResult(
            model=model_name, rule="archetype.semantic_model", result=Result.NA
        )

    return RuleResult(
        model=model_name,
        rule="archetype.semantic_model",
        result=Result.PASS,
        spec_ref=f"{SPEC_REF_ENTITIES}/semantic-model.md",
    )

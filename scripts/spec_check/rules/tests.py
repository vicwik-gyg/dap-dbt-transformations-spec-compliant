"""Testing convention rules."""

from __future__ import annotations

from typing import Any

from ..manifest import (
    get_layer,
    get_model_prefix,
    get_tests_for_model,
    is_column_rule_suppressed,
    model_exists_in_manifest,
)
from ..models import Result, RuleResult
from ..registry import rule

SPEC_REF_TESTING = "04-target-state/conventions.md#testing"


def _get_generic_tests_for_column(
    model_unique_id: str, column_name: str, manifest: dict[str, Any]
) -> list[dict[str, Any]]:
    """Get generic (schema) tests for a specific column on a model."""
    tests = get_tests_for_model(model_unique_id, manifest)
    return [
        t
        for t in tests
        if t.get("column_name") == column_name and t.get("test_metadata")
    ]


def _get_pk_columns(node: dict[str, Any]) -> list[str]:
    """Identify primary key columns from the model."""
    columns = node.get("columns", {})
    # Use primary_key field if available
    pk = node.get("primary_key")
    if pk:
        if isinstance(pk, list):
            return pk
        return [pk]

    # Heuristic: first _id column, or columns with PK in description/meta
    col_names = list(columns.keys())
    name = node["name"]

    # For staging: the entity's natural key
    # For facts: the first _id that matches the entity name
    # General heuristic: first _id column
    id_cols = [c for c in col_names if c.endswith("_id")]
    if id_cols:
        # Prefer the one matching the model's entity name
        for c in id_cols:
            entity = name.replace("stg_", "").replace("fct_", "").replace("dim_", "").replace("agg_", "").replace("int_", "")
            # Remove source prefix for staging
            if "__" in entity:
                entity = entity.split("__")[-1]
            # Singularize rough match
            entity_stem = entity.rstrip("s")
            if entity_stem in c:
                return [c]
        return [id_cols[0]]

    return []


@rule(
    name="tests.not_null_on_pk",
    description="Primary key column has not_null test",
    applies_to=["all"],
    spec_ref=SPEC_REF_TESTING,
)
def check_not_null_on_pk(node: dict[str, Any], manifest: dict[str, Any]) -> RuleResult:
    model_name = node["name"]
    model_uid = node["unique_id"]
    pk_cols = _get_pk_columns(node)

    if not pk_cols:
        return RuleResult(
            model=model_name, rule="tests.not_null_on_pk", result=Result.NA
        )

    all_tests = get_tests_for_model(model_uid, manifest)
    findings = []

    for pk_col in pk_cols:
        has_not_null = any(
            t.get("column_name") == pk_col
            and t.get("test_metadata", {}).get("name") == "not_null"
            for t in all_tests
        )
        if not has_not_null:
            findings.append(f"PK column '{pk_col}' missing not_null test")

    if findings:
        return RuleResult(
            model=model_name,
            rule="tests.not_null_on_pk",
            result=Result.DEVIATES,
            finding="; ".join(findings),
            spec_ref=SPEC_REF_TESTING,
        )

    return RuleResult(
        model=model_name,
        rule="tests.not_null_on_pk",
        result=Result.PASS,
        spec_ref=SPEC_REF_TESTING,
    )


@rule(
    name="tests.unique_on_pk",
    description="Primary key column has unique test",
    applies_to=["all"],
    spec_ref=SPEC_REF_TESTING,
)
def check_unique_on_pk(node: dict[str, Any], manifest: dict[str, Any]) -> RuleResult:
    model_name = node["name"]
    model_uid = node["unique_id"]
    pk_cols = _get_pk_columns(node)

    if not pk_cols:
        return RuleResult(
            model=model_name, rule="tests.unique_on_pk", result=Result.NA
        )

    all_tests = get_tests_for_model(model_uid, manifest)
    findings = []

    for pk_col in pk_cols:
        has_unique = any(
            t.get("column_name") == pk_col
            and t.get("test_metadata", {}).get("name") == "unique"
            for t in all_tests
        )
        if not has_unique:
            findings.append(f"PK column '{pk_col}' missing unique test")

    if findings:
        return RuleResult(
            model=model_name,
            rule="tests.unique_on_pk",
            result=Result.DEVIATES,
            finding="; ".join(findings),
            spec_ref=SPEC_REF_TESTING,
        )

    return RuleResult(
        model=model_name,
        rule="tests.unique_on_pk",
        result=Result.PASS,
        spec_ref=SPEC_REF_TESTING,
    )


@rule(
    name="tests.accepted_values_on_enums",
    description="Enum/status columns have accepted_values test",
    applies_to=["all"],
    spec_ref=SPEC_REF_TESTING,
)
def check_accepted_values_on_enums(
    node: dict[str, Any], manifest: dict[str, Any]
) -> RuleResult:
    model_name = node["name"]
    model_uid = node["unique_id"]
    columns = node.get("columns", {})

    # Identify enum-like columns by naming convention
    enum_indicators = ("status", "type", "category", "priority", "level", "tier")
    enum_cols = [
        c
        for c in columns
        if any(ind in c for ind in enum_indicators)
        and not c.endswith("_id")
        and not c.endswith("_at")
        and not c.endswith("_date")
    ]

    if not enum_cols:
        return RuleResult(
            model=model_name, rule="tests.accepted_values_on_enums", result=Result.NA
        )

    all_tests = get_tests_for_model(model_uid, manifest)
    findings = []
    suppressed = []

    for col in enum_cols:
        # Check column-level suppression
        is_suppressed, justification = is_column_rule_suppressed(
            node, col, "tests.accepted_values_on_enums"
        )
        if is_suppressed:
            reason = justification or "no justification provided"
            suppressed.append(f"{col} (suppressed: {reason})")
            continue

        has_accepted = any(
            t.get("column_name") == col
            and t.get("test_metadata", {}).get("name") == "accepted_values"
            for t in all_tests
        )
        if not has_accepted:
            findings.append(f"Enum column '{col}' missing accepted_values test")

    # If all enum columns are suppressed, return SUPPRESSED
    if not findings and suppressed:
        return RuleResult(
            model=model_name,
            rule="tests.accepted_values_on_enums",
            result=Result.SUPPRESSED,
            finding=f"Suppressed: {'; '.join(suppressed)}",
        )

    if findings:
        return RuleResult(
            model=model_name,
            rule="tests.accepted_values_on_enums",
            result=Result.DEVIATES,
            finding="; ".join(findings),
            spec_ref=SPEC_REF_TESTING,
        )

    return RuleResult(
        model=model_name,
        rule="tests.accepted_values_on_enums",
        result=Result.PASS,
        spec_ref=SPEC_REF_TESTING,
    )


def _fk_target_exists(column_name: str, source_node: dict[str, Any], manifest: dict[str, Any]) -> tuple[bool, str | None]:
    """Check if any conventional FK target model exists in the manifest.

    Checks (in order): dim_<entity>s, dim_<entity>, stg_<source>__<entity>s.
    Returns (exists, checked_target_name) where checked_target_name is the
    primary candidate that was looked up.
    """
    if not column_name.endswith("_id"):
        return True, None
    entity = column_name[:-3]  # strip _id

    # Check dim variants
    candidates = [f"dim_{entity}s", f"dim_{entity}"]

    # For staging models, also check sibling staging model
    layer = get_layer(source_node)
    if layer == "staging":
        source_name = source_node.get("name", "")
        if "__" in source_name:
            source_prefix = source_name.split("__")[0]
            candidates.append(f"{source_prefix}__{entity}s")
            candidates.append(f"{source_prefix}__{entity}")

    for candidate in candidates:
        if model_exists_in_manifest(candidate, manifest):
            return True, candidate

    return False, candidates[0]


@rule(
    name="tests.relationships_on_fks",
    description="FK columns have relationships test",
    applies_to=["all"],
    spec_ref=SPEC_REF_TESTING,
)
def check_relationships_on_fks(
    node: dict[str, Any], manifest: dict[str, Any]
) -> RuleResult:
    model_name = node["name"]
    model_uid = node["unique_id"]
    columns = node.get("columns", {})

    # Identify FK columns: _id columns that aren't the PK
    pk_cols = set(_get_pk_columns(node))
    fk_cols = [
        c for c in columns if c.endswith("_id") and c not in pk_cols
    ]

    if not fk_cols:
        return RuleResult(
            model=model_name, rule="tests.relationships_on_fks", result=Result.NA
        )

    all_tests = get_tests_for_model(model_uid, manifest)
    findings = []
    unverifiable = []

    for col in fk_cols:
        has_relationship = any(
            t.get("column_name") == col
            and t.get("test_metadata", {}).get("name") == "relationships"
            for t in all_tests
        )
        if has_relationship:
            continue

        # Check if any conventional target model exists in the manifest
        target_exists, target_name = _fk_target_exists(col, node, manifest)
        if not target_exists:
            unverifiable.append(
                f"FK column '{col}' — target {target_name} not in project"
            )
        else:
            findings.append(f"FK column '{col}' missing relationships test")

    # If all FK columns are unverifiable (target not in manifest), return NA
    if not findings and unverifiable:
        return RuleResult(
            model=model_name,
            rule="tests.relationships_on_fks",
            result=Result.NA,
            finding="; ".join(unverifiable),
        )

    if findings:
        return RuleResult(
            model=model_name,
            rule="tests.relationships_on_fks",
            result=Result.DEVIATES,
            finding="; ".join(findings),
            spec_ref=SPEC_REF_TESTING,
        )

    return RuleResult(
        model=model_name,
        rule="tests.relationships_on_fks",
        result=Result.PASS,
        spec_ref=SPEC_REF_TESTING,
    )

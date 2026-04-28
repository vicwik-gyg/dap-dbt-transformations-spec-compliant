"""Testing convention rules."""

from __future__ import annotations

from typing import Any

from ..manifest import get_layer, get_model_prefix, get_tests_for_model
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

    for col in enum_cols:
        has_accepted = any(
            t.get("column_name") == col
            and t.get("test_metadata", {}).get("name") == "accepted_values"
            for t in all_tests
        )
        if not has_accepted:
            findings.append(f"Enum column '{col}' missing accepted_values test")

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

    for col in fk_cols:
        has_relationship = any(
            t.get("column_name") == col
            and t.get("test_metadata", {}).get("name") == "relationships"
            for t in all_tests
        )
        if not has_relationship:
            findings.append(f"FK column '{col}' missing relationships test")

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

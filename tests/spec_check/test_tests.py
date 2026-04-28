"""Tests for testing-convention rules."""

from scripts.spec_check.models import Result
from scripts.spec_check.rules.tests import (
    check_accepted_values_on_enums,
    check_not_null_on_pk,
    check_relationships_on_fks,
    check_unique_on_pk,
)

from .conftest import make_manifest, make_model_node, make_test_node


def test_not_null_on_pk_pass():
    model = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        columns={"order_id": {"name": "order_id", "description": "PK"}},
    )
    test = make_test_node(model["unique_id"], "order_id", "not_null")
    manifest = make_manifest(nodes=[model, test])
    result = check_not_null_on_pk(model, manifest)
    assert result.result == Result.PASS


def test_not_null_on_pk_deviates():
    model = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        columns={"order_id": {"name": "order_id", "description": "PK"}},
    )
    manifest = make_manifest(nodes=[model])
    result = check_not_null_on_pk(model, manifest)
    assert result.result == Result.DEVIATES


def test_unique_on_pk_pass():
    model = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        columns={"order_id": {"name": "order_id", "description": "PK"}},
    )
    test = make_test_node(model["unique_id"], "order_id", "unique")
    manifest = make_manifest(nodes=[model, test])
    result = check_unique_on_pk(model, manifest)
    assert result.result == Result.PASS


def test_unique_on_pk_deviates():
    model = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        columns={"order_id": {"name": "order_id", "description": "PK"}},
    )
    manifest = make_manifest(nodes=[model])
    result = check_unique_on_pk(model, manifest)
    assert result.result == Result.DEVIATES


def test_accepted_values_pass():
    model = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        columns={
            "order_id": {"name": "order_id", "description": "PK"},
            "order_status": {"name": "order_status", "description": "enum"},
        },
    )
    test = make_test_node(model["unique_id"], "order_status", "accepted_values")
    manifest = make_manifest(nodes=[model, test])
    result = check_accepted_values_on_enums(model, manifest)
    assert result.result == Result.PASS


def test_accepted_values_deviates():
    model = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        columns={
            "order_id": {"name": "order_id", "description": "PK"},
            "order_status": {"name": "order_status", "description": "enum"},
        },
    )
    manifest = make_manifest(nodes=[model])
    result = check_accepted_values_on_enums(model, manifest)
    assert result.result == Result.DEVIATES


def test_relationships_on_fks_pass():
    model = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        columns={
            "order_id": {"name": "order_id", "description": "PK"},
            "customer_id": {"name": "customer_id", "description": "FK"},
        },
    )
    test = make_test_node(model["unique_id"], "customer_id", "relationships")
    manifest = make_manifest(nodes=[model, test])
    result = check_relationships_on_fks(model, manifest)
    assert result.result == Result.PASS


def test_relationships_on_fks_deviates():
    model = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        columns={
            "order_id": {"name": "order_id", "description": "PK"},
            "customer_id": {"name": "customer_id", "description": "FK"},
        },
    )
    manifest = make_manifest(nodes=[model])
    result = check_relationships_on_fks(model, manifest)
    assert result.result == Result.DEVIATES

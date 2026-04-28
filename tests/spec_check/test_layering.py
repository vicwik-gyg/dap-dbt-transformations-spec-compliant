"""Tests for layering rules."""

from scripts.spec_check.models import Result
from scripts.spec_check.rules.layering import check_correct_layer

from .conftest import make_manifest, make_model_node


def test_correct_layer_staging():
    node = make_model_node(
        "stg_source__orders",
        fqn=["project", "staging", "stg_source__orders"],
        path="staging/stg_source__orders.sql",
    )
    result = check_correct_layer(node, make_manifest())
    assert result.result == Result.PASS


def test_correct_layer_fact_in_marts():
    node = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        path="marts/fct_orders.sql",
    )
    result = check_correct_layer(node, make_manifest())
    assert result.result == Result.PASS


def test_wrong_layer_staging_in_marts():
    node = make_model_node(
        "stg_source__orders",
        fqn=["project", "marts", "stg_source__orders"],
        path="marts/stg_source__orders.sql",
    )
    result = check_correct_layer(node, make_manifest())
    assert result.result == Result.DEVIATES


def test_no_prefix_deviates():
    node = make_model_node(
        "orders",
        fqn=["project", "marts", "orders"],
        path="marts/orders.sql",
    )
    result = check_correct_layer(node, make_manifest())
    assert result.result == Result.DEVIATES

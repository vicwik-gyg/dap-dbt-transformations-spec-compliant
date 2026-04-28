"""Tests for naming rules."""

from scripts.spec_check.models import Result
from scripts.spec_check.rules.naming import (
    check_column_snake_case,
    check_source_style,
    check_table_prefix,
)

from .conftest import make_manifest, make_model_node


def test_table_prefix_pass_staging():
    node = make_model_node(
        "stg_source__orders",
        fqn=["project", "staging", "stg_source__orders"],
        path="staging/stg_source__orders.sql",
    )
    result = check_table_prefix(node, make_manifest())
    assert result.result == Result.PASS


def test_table_prefix_pass_fact():
    node = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        path="marts/fct_orders.sql",
    )
    result = check_table_prefix(node, make_manifest())
    assert result.result == Result.PASS


def test_table_prefix_deviates():
    node = make_model_node(
        "orders",  # no prefix
        fqn=["project", "marts", "orders"],
        path="marts/orders.sql",
    )
    result = check_table_prefix(node, make_manifest())
    assert result.result == Result.DEVIATES


def test_column_snake_case_pass():
    node = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        columns={
            "order_id": {"name": "order_id", "description": "PK"},
            "created_at": {"name": "created_at", "description": "ts"},
        },
    )
    result = check_column_snake_case(node, make_manifest())
    assert result.result == Result.PASS


def test_column_snake_case_deviates():
    node = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        columns={
            "OrderId": {"name": "OrderId", "description": "PK"},
            "created_at": {"name": "created_at", "description": "ts"},
        },
    )
    result = check_column_snake_case(node, make_manifest())
    assert result.result == Result.DEVIATES
    assert "OrderId" in result.finding


def test_source_style_pass():
    node = make_model_node(
        "stg_source_data__bookings",
        fqn=["project", "staging", "stg_source_data__bookings"],
        path="staging/stg_source_data__bookings.sql",
    )
    result = check_source_style(node, make_manifest())
    assert result.result == Result.PASS


def test_source_style_deviates_no_separator():
    node = make_model_node(
        "stg_bookings",  # missing __ separator
        fqn=["project", "staging", "stg_bookings"],
        path="staging/stg_bookings.sql",
    )
    result = check_source_style(node, make_manifest())
    assert result.result == Result.DEVIATES

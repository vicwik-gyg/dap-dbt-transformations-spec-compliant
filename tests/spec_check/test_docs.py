"""Tests for documentation rules."""

from scripts.spec_check.models import Result
from scripts.spec_check.rules.docs import check_column_description, check_model_description

from .conftest import make_manifest, make_model_node


def test_model_description_pass():
    node = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        description="Orders fact table tracking all transactions.",
    )
    result = check_model_description(node, make_manifest())
    assert result.result == Result.PASS


def test_model_description_deviates():
    node = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        description="",
    )
    result = check_model_description(node, make_manifest())
    assert result.result == Result.DEVIATES


def test_column_description_pass():
    node = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        columns={
            "order_id": {"name": "order_id", "description": "Unique order identifier"},
            "amount": {"name": "amount", "description": "Order total in cents"},
        },
    )
    result = check_column_description(node, make_manifest())
    assert result.result == Result.PASS


def test_column_description_deviates():
    node = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        columns={
            "order_id": {"name": "order_id", "description": "PK"},
            "amount": {"name": "amount", "description": ""},
        },
    )
    result = check_column_description(node, make_manifest())
    assert result.result == Result.DEVIATES
    assert "amount" in result.finding

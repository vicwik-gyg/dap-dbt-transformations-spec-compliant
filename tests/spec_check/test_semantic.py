"""Tests for semantic layer rules."""

from scripts.spec_check.models import Result
from scripts.spec_check.rules.semantic import check_marts_have_semantic_model

from .conftest import make_manifest, make_model_node


def test_semantic_model_pass():
    model = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        columns={"order_id": {"name": "order_id", "description": "PK"}},
    )
    manifest = make_manifest(
        nodes=[model],
        semantic_models={
            "semantic_model.project.sem_orders": {
                "name": "sem_orders",
                "model": "ref('fct_orders')",
                "depends_on": {"nodes": ["model.project.fct_orders"]},
                "entities": [{"name": "order", "type": "primary"}],
                "dimensions": [{"name": "order_date"}],
                "measures": [{"name": "order_count"}],
            }
        },
    )
    result = check_marts_have_semantic_model(model, manifest)
    assert result.result == Result.PASS


def test_semantic_model_na_for_snapshot():
    model = make_model_node(
        "fct_orders_snapshot",
        fqn=["project", "marts", "fct_orders_snapshot"],
        columns={"order_id": {"name": "order_id", "description": "PK"}},
    )
    manifest = make_manifest(nodes=[model])
    result = check_marts_have_semantic_model(model, manifest)
    assert result.result == Result.NA


def test_semantic_model_na_for_dim():
    model = make_model_node(
        "dim_customers",
        fqn=["project", "marts", "dim_customers"],
        columns={"customer_id": {"name": "customer_id", "description": "PK"}},
    )
    manifest = make_manifest(nodes=[model])
    result = check_marts_have_semantic_model(model, manifest)
    assert result.result == Result.NA

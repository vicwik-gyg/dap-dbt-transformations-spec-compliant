"""Tests for archetype rules."""

from scripts.spec_check.models import Result
from scripts.spec_check.rules.archetype import (
    check_agg_mart,
    check_dim_conformed,
    check_dim_scd_type_2,
    check_fct_accumulating_snapshot,
    check_fct_periodic_snapshot,
    check_fct_transaction,
    check_staging_archetype,
)

from .conftest import make_manifest, make_model_node


def test_staging_pass():
    node = make_model_node(
        "stg_source__orders",
        fqn=["project", "staging", "stg_source__orders"],
        depends_on_nodes=["source.project.source_data.orders"],
        raw_code="select * from {{ source('source_data', 'orders') }}",
    )
    result = check_staging_archetype(node, make_manifest())
    assert result.result == Result.PASS


def test_staging_deviates_join():
    node = make_model_node(
        "stg_source__orders",
        fqn=["project", "staging", "stg_source__orders"],
        depends_on_nodes=["source.project.source_data.orders"],
        raw_code="select * from {{ source('source_data', 'orders') }} join other",
    )
    result = check_staging_archetype(node, make_manifest())
    assert result.result == Result.DEVIATES
    assert "JOIN" in result.finding


def test_staging_deviates_multiple_sources():
    node = make_model_node(
        "stg_source__orders",
        fqn=["project", "staging", "stg_source__orders"],
        depends_on_nodes=[
            "source.project.source_data.orders",
            "source.project.source_data.customers",
        ],
    )
    result = check_staging_archetype(node, make_manifest())
    assert result.result == Result.DEVIATES


def test_fct_transaction_pass():
    node = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        columns={
            "order_id": {"name": "order_id", "description": "PK"},
            "created_at": {"name": "created_at", "description": "ts"},
            "amount": {"name": "amount", "description": "val"},
        },
    )
    result = check_fct_transaction(node, make_manifest())
    assert result.result == Result.PASS


def test_fct_transaction_deviates_no_timestamp():
    node = make_model_node(
        "fct_orders",
        fqn=["project", "marts", "fct_orders"],
        columns={
            "order_id": {"name": "order_id", "description": "PK"},
            "amount": {"name": "amount", "description": "val"},
        },
    )
    result = check_fct_transaction(node, make_manifest())
    assert result.result == Result.DEVIATES


def test_fct_periodic_snapshot_pass():
    node = make_model_node(
        "fct_inventory_snapshot",
        fqn=["project", "marts", "fct_inventory_snapshot"],
        columns={
            "item_id": {"name": "item_id", "description": "PK"},
            "snapshot_date": {"name": "snapshot_date", "description": "grain"},
            "quantity": {"name": "quantity", "description": "measure"},
        },
    )
    result = check_fct_periodic_snapshot(node, make_manifest())
    assert result.result == Result.PASS


def test_fct_accumulating_pass():
    node = make_model_node(
        "fct_orders_accumulating_snapshot",
        fqn=["project", "marts", "fct_orders_accumulating_snapshot"],
        columns={
            "order_id": {"name": "order_id", "description": "PK"},
            "created_at": {"name": "created_at", "description": "m1"},
            "shipped_at": {"name": "shipped_at", "description": "m2"},
            "delivered_at": {"name": "delivered_at", "description": "m3"},
        },
    )
    result = check_fct_accumulating_snapshot(node, make_manifest())
    assert result.result == Result.PASS


def test_fct_accumulating_deviates_few_milestones():
    node = make_model_node(
        "fct_orders_accumulating_snapshot",
        fqn=["project", "marts", "fct_orders_accumulating_snapshot"],
        columns={
            "order_id": {"name": "order_id", "description": "PK"},
            "created_at": {"name": "created_at", "description": "only one"},
        },
    )
    result = check_fct_accumulating_snapshot(node, make_manifest())
    assert result.result == Result.DEVIATES


def test_dim_conformed_pass():
    node = make_model_node(
        "dim_customers",
        fqn=["project", "marts", "dim_customers"],
        columns={
            "customer_id": {"name": "customer_id", "description": "PK"},
            "name": {"name": "name", "description": "attr"},
        },
    )
    result = check_dim_conformed(node, make_manifest())
    assert result.result == Result.PASS


def test_dim_scd2_pass():
    node = make_model_node(
        "dim_suppliers_history",
        fqn=["project", "marts", "dim_suppliers_history"],
        columns={
            "supplier_id": {"name": "supplier_id", "description": "NK"},
            "valid_from": {"name": "valid_from", "description": "SCD start"},
            "valid_to": {"name": "valid_to", "description": "SCD end"},
            "name": {"name": "name", "description": "attr"},
        },
    )
    result = check_dim_scd_type_2(node, make_manifest())
    assert result.result == Result.PASS


def test_dim_scd2_deviates_missing_valid_to():
    node = make_model_node(
        "dim_suppliers_history",
        fqn=["project", "marts", "dim_suppliers_history"],
        columns={
            "supplier_id": {"name": "supplier_id", "description": "NK"},
            "valid_from": {"name": "valid_from", "description": "SCD start"},
        },
    )
    result = check_dim_scd_type_2(node, make_manifest())
    assert result.result == Result.DEVIATES


def test_agg_mart_pass():
    node = make_model_node(
        "agg_orders_daily",
        fqn=["project", "marts", "agg_orders_daily"],
        columns={
            "order_date": {"name": "order_date", "description": "grain"},
            "total_orders": {"name": "total_orders", "description": "measure"},
        },
        depends_on_nodes=["model.project.fct_orders"],
    )
    result = check_agg_mart(node, make_manifest())
    assert result.result == Result.PASS


def test_agg_mart_deviates_no_deps():
    node = make_model_node(
        "agg_orders_daily",
        fqn=["project", "marts", "agg_orders_daily"],
        columns={
            "order_date": {"name": "order_date", "description": "grain"},
        },
        depends_on_nodes=[],
    )
    result = check_agg_mart(node, make_manifest())
    assert result.result == Result.DEVIATES

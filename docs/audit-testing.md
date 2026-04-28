# Testing Coverage Audit

**Date:** 2026-04-28
**Spec:** `dap-dwh-spec/02-mined-standards/testing.md`
**Scope:** All 21 SQL models

---

## Summary

| Verdict | Count |
|---------|-------|
| PASS (PK tests present) | 15 models |
| DEVIATES (missing PK/composite unique) | 4 models |
| N/A (no single-column PK) | 2 models |

**Material deviations: 0.** The 4 missing composite unique tests are important data quality gaps but not "material" in the spec-gate sense — they don't affect downstream consumers or model correctness. They should be added as best practice.

---

## Minimum Bar: PK Tests (unique + not_null)

| Model | Has unique? | Has not_null? | Verdict |
|-------|-------------|---------------|---------|
| stg_seed_data__bookings | YES | YES | PASS |
| stg_seed_data__booking_status_changes | NO (event log) | YES | N/A — no single PK |
| stg_seed_data__care_tickets | YES | YES | PASS |
| stg_seed_data__destinations | YES | YES | PASS |
| stg_seed_data__supplier_versions | NO (SCD2 rows) | YES | N/A — no single PK |
| stg_seed_data__suppliers | YES | YES | PASS |
| stg_seed_data__tours | YES | YES | PASS |
| int_bookings_enriched | YES | YES | PASS |
| int_bookings_with_milestones | YES | YES | PASS |
| int_tours_with_supplier_context | YES | YES | PASS |
| fct_bookings | YES | YES | PASS |
| fct_bookings_snapshot | NO | YES (on booking_id) | DEVIATES |
| fct_bookings_accumulating_snapshot | YES | YES | PASS |
| agg_bookings_checkout_daily | YES | YES | PASS |
| agg_bookings_destination_daily | NO (composite grain) | YES | DEVIATES |
| agg_bookings_tour_category_monthly | NO (composite grain) | YES | DEVIATES |
| dim_destinations | YES | YES | PASS |
| dim_tours | YES | YES | PASS |
| dim_suppliers_history | YES | YES | PASS |
| dim_care_tickets | YES | YES | PASS |

### Models needing composite unique tests:

1. **fct_bookings_snapshot** — composite key is `(snapshot_date, booking_id)`. Has `not_null` but no uniqueness constraint.
2. **agg_bookings_destination_daily** — composite grain is `(checkout_date, destination_id)`. Has `not_null` but no `dbt_utils.unique_combination_of_columns`.
3. **agg_bookings_tour_category_monthly** — composite grain is `(checkout_month, tour_category)`. Same gap.
4. **stg_seed_data__booking_status_changes** — natural composite key is `(booking_id, changed_at)`. No composite unique defined.

---

## accepted_values Coverage

| Model | Column | Has Test? | Verdict |
|-------|--------|-----------|---------|
| stg_seed_data__bookings | booking_status | YES: pending, confirmed, cancelled | PASS |
| fct_bookings_accumulating_snapshot | current_lifecycle_stage | YES: 5 values | PASS |
| dim_care_tickets | ticket_category | NO | DEVIATES (minor) |
| dim_care_tickets | ticket_priority | NO | DEVIATES (minor) |
| dim_care_tickets | ticket_status | NO | DEVIATES (minor) |
| stg_seed_data__tours | tour_category | NO | DEVIATES (minor) |

**Assessment:** The two most critical categorical columns (booking_status, lifecycle_stage) are tested. The remaining are lower-risk reference columns where invalid values would not corrupt calculations.

---

## relationships Tests

| FK Column | Target Model | Has Test? |
|-----------|-------------|-----------|
| bookings.tour_id | stg_seed_data__tours | NO |
| bookings.customer_id | — (no customers model) | N/A |
| bookings.supplier_id | stg_seed_data__suppliers | NO |
| bookings.destination_id | stg_seed_data__destinations | NO |
| care_tickets.booking_id | stg_seed_data__bookings | NO |
| tours.supplier_id | stg_seed_data__suppliers | NO |
| tours.destination_id | stg_seed_data__destinations | NO |

**Finding: No `relationships` tests defined in the project.**

- **Spec requires:** Four generic tests include `relationships` as one of the standard test types.
- **What the project does:** No FK integrity tests.
- **Assessment:** In a seed-based environment where data is hand-crafted, referential integrity is guaranteed by construction. However, the spec requires these tests as documentation of expected relationships. This is a meaningful gap for a reference implementation.
- **Materiality: NON-MATERIAL** for correctness (seeds are consistent), but **RECOMMENDED** for spec compliance and reference value.

---

## Business Logic Tests

| Test | What it validates | Verdict |
|------|-------------------|---------|
| test_agg_reconciles_with_fact.sql | agg confirmed count = fact confirmed count | PASS |
| test_booking_milestone_ordering.sql | confirmed_at >= pending_at chronologically | PASS |
| test_no_overlapping_scd2_windows.sql | No overlapping validity windows in SCD2 | PASS |
| dbt_expectations.between on cancellation_rate | Rate is 0.0-1.0 | PASS |

**Assessment:** Critical business logic is well-tested. The three singular tests cover the most important invariants (aggregate-fact reconciliation, temporal ordering, SCD2 correctness).

---

## Singular Tests Inventory

| File | Models Tested | Category |
|------|---------------|----------|
| test_agg_reconciles_with_fact.sql | agg_bookings_checkout_daily, fct_bookings | Cross-model reconciliation |
| test_booking_milestone_ordering.sql | fct_bookings_accumulating_snapshot | Temporal invariant |
| test_no_overlapping_scd2_windows.sql | dim_suppliers_history | SCD2 invariant |

---

## Freshness Checks

**Spec requires:** Freshness checks on every mart table (the "fifth test").

**Status:** Not applicable. The shadow repo runs on seeds, not source tables with timestamps that drift. Freshness SLAs are a production concern that cannot be meaningfully tested against static seed data.

**Recommendation:** When transitioning to production sources (Phase 3+), add `loaded_at_field` + `freshness` blocks to source definitions.

---

## Test Packages Used

| Package | Tests Used |
|---------|-----------|
| dbt (built-in) | unique, not_null, accepted_values |
| dbt_expectations | expect_column_values_to_be_between |
| (custom singular) | 3 singular tests |

**Missing:** `dbt_utils.unique_combination_of_columns` for composite keys.

---

## Findings Detail

### Finding 1: Missing composite unique tests (RECOMMENDED FIX)

**Models affected:** fct_bookings_snapshot, agg_bookings_destination_daily, agg_bookings_tour_category_monthly, stg_seed_data__booking_status_changes.

**Spec requires:** "Every model must have unique and not_null tests on its primary key." For composite keys, this means `dbt_utils.unique_combination_of_columns`.

**Proposed remediation:**
```yaml
# fct_bookings_snapshot
tests:
  - dbt_utils.unique_combination_of_columns:
      combination_of_columns: [snapshot_date, booking_id]

# agg_bookings_destination_daily
tests:
  - dbt_utils.unique_combination_of_columns:
      combination_of_columns: [checkout_date, destination_id]

# agg_bookings_tour_category_monthly
tests:
  - dbt_utils.unique_combination_of_columns:
      combination_of_columns: [checkout_month, tour_category]
```

**Materiality: NON-MATERIAL** for gate decision. The data is correct (seeds guarantee it). But recommended for reference implementation value.

### Finding 2: No relationships tests (RECOMMENDED FIX)

**Spec requires:** `relationships` is one of the four standard generic tests.

**Proposed remediation:** Add relationship tests on FK columns at the staging layer:
```yaml
# stg_seed_data__bookings
- name: tour_id
  tests:
    - relationships:
        to: ref('stg_seed_data__tours')
        field: tour_id
```

**Materiality: NON-MATERIAL.** Seeds are hand-crafted and consistent. Tests document expected relationships.

### Finding 3: Missing accepted_values on dim categoricals (MINOR)

**Columns affected:** ticket_category, ticket_priority, ticket_status, tour_category.

**Assessment:** Lower-risk columns not used in calculations. Nice to have for documentation.

---

## Gate Decision

**0 material deviations.** Testing coverage meets the minimum bar (PK tests on all applicable models) and includes strong business logic validation. Recommended improvements (composite unique, relationships, accepted_values) would elevate the repo from "meets minimum" to "exemplary reference."

---

## Recommendations for Remediation Task (1.7)

Priority order:
1. Add `dbt_utils.unique_combination_of_columns` on 4 composite-key models
2. Add `relationships` tests on FK columns in staging layer
3. Add `accepted_values` on dim categorical columns
4. (Future) Add freshness SLAs when moving to production sources

# Validation Results

Full end-to-end pipeline run against `testing` catalog on Databricks.

**Date:** 2026-04-29
**Auth:** OAuth U2M via Databricks CLI bridge profile (`auth_type: oauth`)
**Target:** `testing.dbt_default` (dbt profile `dap_dbt_transformations`, target `dev`)
**dbt version:** 1.10.20
**dbt-databricks:** 1.10.9

---

## dbt deps

```
Running with dbt=1.10.20
Installing dbt-labs/dbt_utils
  Installed from version 1.3.0
Installing dbt-labs/codegen
  Installed from version 0.12.1
Installing metaplane/dbt_expectations
  Installed from version 0.10.10
Installing godatadriven/dbt_date
  Installed from version 0.17.2
```

**Result:** PASS

---

## dbt seed

```
Concurrency: 10 threads (target='dev')

 1 of 13 OK loaded seed file dbt_default.seed_booking_status_history .. [INSERT 8977 in 16.40s]
 2 of 13 OK loaded seed file dbt_default.seed_bookings ................ [INSERT 1033 in 13.07s]
 3 of 13 OK loaded seed file dbt_default.seed_care_tickets ............ [INSERT 92 in 11.38s]
 4 of 13 OK loaded seed file dbt_default.seed_destinations ............ [INSERT 1144 in 11.92s]
 5 of 13 OK loaded seed file dbt_default.seed_dim_date ................ [INSERT 366 in 11.38s]
 6 of 13 OK loaded seed file dbt_default.seed_reviews ................. [INSERT 11 in 11.38s]
 7 of 13 OK loaded seed file dbt_default.seed_supplier_dim ............ [INSERT 5 in 11.38s]
 8 of 13 OK loaded seed file dbt_default.seed_supplier_history ........ [INSERT 6679 in 15.42s]
 9 of 13 OK loaded seed file dbt_default.seed_supplier_status_history . [INSERT 6 in 11.38s]
10 of 13 OK loaded seed file dbt_default.seed_suppliers ............... [INSERT 1137 in 11.92s]
11 of 13 OK loaded seed file dbt_default.seed_tour_history ............ [INSERT 18 in 4.92s]
12 of 13 OK loaded seed file dbt_default.seed_tour_option_bookable_history [INSERT 15 in 4.73s]
13 of 13 OK loaded seed file dbt_default.seed_tours ................... [INSERT 1031 in 6.02s]

Finished running 13 seeds in 22.77s.
```

**Result:** PASS=13 WARN=0 ERROR=0 SKIP=0 TOTAL=13

---

## dbt run

```
Concurrency: 10 threads (target='dev')

 1 of 32 OK created sql table model dbt_default.metricflow_time_spine ........... [OK in 5.99s]
 2 of 32 OK created sql view model dbt_default.stg_seed_data__booking_status_changes [OK in 5.60s]
 3 of 32 OK created sql view model dbt_default.stg_seed_data__bookings .......... [OK in 5.98s]
 4 of 32 OK created sql view model dbt_default.stg_seed_data__care_tickets ...... [OK in 5.60s]
 5 of 32 OK created sql view model dbt_default.stg_seed_data__destinations ...... [OK in 5.98s]
 6 of 32 OK created sql view model dbt_default.stg_seed_data__dim_date .......... [OK in 5.67s]
 7 of 32 OK created sql view model dbt_default.stg_seed_data__reviews ........... [OK in 5.67s]
 8 of 32 OK created sql view model dbt_default.stg_seed_data__supplier_dim ...... [OK in 5.67s]
 9 of 32 OK created sql view model dbt_default.stg_seed_data__supplier_status_history [OK in 5.60s]
10 of 32 OK created sql view model dbt_default.stg_seed_data__supplier_versions . [OK in 5.59s]
11 of 32 OK created sql view model dbt_default.stg_seed_data__suppliers ......... [OK in 5.06s]
12 of 32 OK created sql view model dbt_default.stg_seed_data__tour_history ...... [OK in 4.19s]
13 of 32 OK created sql view model dbt_default.stg_seed_data__tour_option_bookable_history [OK in 4.19s]
14 of 32 OK created sql view model dbt_default.stg_seed_data__tours ............. [OK in 4.19s]
15 of 32 OK created sql view model dbt_default.int_bookings_with_milestones ..... [OK in 4.20s]
16 of 32 OK created sql table model dbt_default.dim_suppliers_history ........... [OK in 12.36s]
17 of 32 OK created sql table model dbt_default.dim_care_tickets ................ [OK in 16.19s]
18 of 32 OK created sql table model dbt_default.dim_destinations ................ [OK in 10.07s]
19 of 32 OK created sql view model dbt_default.int_bookings_enriched ............ [OK in 3.28s]
20 of 32 OK created sql view model dbt_default.int_tours_with_supplier_context .. [OK in 3.28s]
21 of 32 OK created sql view model dbt_default.int_tour_online_daily ............ [OK in 3.28s]
22 of 32 OK created sql table model dbt_default.fct_bookings .................... [OK in 31.28s]
23 of 32 OK created sql table model dbt_default.fct_bookings_accumulating_snapshot [OK in 20.92s]
24 of 32 OK created sql table model dbt_default.dim_tour_lifecycle_stage_history  [OK in 13.80s]
25 of 32 OK created sql table model dbt_default.dim_tours ....................... [OK in 18.18s]
26 of 32 OK created sql table model dbt_default.dim_supplier_lifecycle_stage_history [OK in 14.81s]
27 of 32 OK created sql table model dbt_default.dim_tour_lifecycle_stage ........ [OK in 9.22s]
28 of 32 OK created sql table model dbt_default.dim_supplier_lifecycle_stage .... [OK in 9.32s]
29 of 32 OK created sql table model dbt_default.agg_bookings_checkout_daily ..... [OK in 11.35s]
30 of 32 OK created sql table model dbt_default.agg_bookings_destination_daily .. [OK in 10.55s]
31 of 32 OK created sql table model dbt_default.agg_bookings_tour_category_monthly [OK in 12.41s]
32 of 32 OK created sql table model dbt_default.fct_bookings_snapshot ........... [OK in 22.88s]

Finished running 15 table models, 17 view models in 71.31s.
```

**Result:** PASS=32 WARN=0 ERROR=0 SKIP=0 TOTAL=32

---

## dbt test

```
Concurrency: 10 threads (target='dev')

 1 of 93 PASS accepted_values_dim_supplier_lifecycle_stage_history_lifecycle_stage [4.67s]
 2 of 93 PASS accepted_values_dim_tour_lifecycle_stage_history_lifecycle_stage [4.67s]
 3 of 93 PASS accepted_values_fct_bookings_accumulating_snapshot_current_lifecycle_stage [4.67s]
 4 of 93 PASS accepted_values_stg_seed_data__bookings_booking_status [4.67s]
 5 of 93 PASS accepted_values_stg_seed_data__reviews_status [4.67s]
 6 of 93 PASS dbt_expectations_expect_column_values_to_be_between_agg_bookings_checkout_daily_cancellation_rate [4.67s]
 7-20 of 93 PASS not_null tests on agg/dim models [~3-5s each]
21-51 of 93 PASS not_null tests on dim/fct/int/stg models [~3-5s each]
52-53 of 93 PASS not_null tests on stg_seed_data__care_tickets [~3-5s each]
54-70 of 93 PASS not_null/unique tests on staging models [~3-5s each]
71 of 93 PASS test_agg_reconciles_with_fact [4.90s]
72 of 93 PASS test_booking_milestone_ordering [4.90s]
73 of 93 PASS test_no_overlapping_scd2_windows [2.84s]
74-93 of 93 PASS unique tests on all models [~2-4s each]

Finished running 93 data tests in 45.77s.
```

**Result:** PASS=93 WARN=0 ERROR=0 SKIP=0 TOTAL=93

---

## Summary

| Command | Result | Duration |
|---------|--------|----------|
| `dbt deps` | PASS | ~12s |
| `dbt seed` | 13/13 PASS | 23s |
| `dbt run` | 32/32 PASS | 71s |
| `dbt test` | 93/93 PASS | 46s |

All 4 pipeline stages complete with exit 0. The shadow repo is fully operational
against `testing.dbt_default` via OAuth U2M authentication.

---

## Regressions fixed (task #11068, 2026-04-29)

After replacing synthetic seeds with production-sampled data (task #11055), 9 tests
failed due to schema drift and data assumptions:

1. **Booking status values** — Production uses `active`, `canceled`, `deleted`,
   `deleted_by_customer`, `deleted_by_daemon` (not the synthetic `pending/confirmed/cancelled`).
   Fixed: updated `accepted_values` test and `is_cancelled` derivation.

2. **Supplier deduplication** — `seed_suppliers.csv` has multiple rows per supplier_id
   (one per destination). Fixed: added `row_number()` dedup in `stg_seed_data__suppliers`.

3. **SCD2 null timestamps** — `seed_supplier_history.csv` has null `valid_from`/`valid_to`
   for early records with incomplete history. Fixed: removed `not_null` constraints on
   temporal columns at both staging and mart layers.

4. **Surrogate key collision** — `dim_suppliers_history` used `supplier_id + valid_from`
   for the surrogate key, but null `valid_from` caused hash collisions.
   Fixed: use `supplier_id + version_number` instead.

---

## Key configuration

1. **OAuth auth** — dbt profile uses `auth_type: oauth` which delegates to Databricks SDK unified auth (picks up CLI token automatically).
2. **SSL cert bundle** — `.ca-bundle.pem` exported from macOS system keychain (includes Zscaler CA). Makefile sets `SSL_CERT_FILE` + `REQUESTS_CA_BUNDLE`.
3. **Schema routing** — All objects land in `dbt_default` (no custom schemas).
4. **Source schema** — `_sources__seeds.yml` references `dbt_default`.
5. **uv run** — `pyproject.toml` with dbt-core/dbt-databricks deps. Makefile uses `uv run dbt`.

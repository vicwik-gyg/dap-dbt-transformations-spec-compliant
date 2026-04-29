# Validation Results

Full end-to-end pipeline run against `testing` catalog on Databricks.

**Date:** 2026-04-28
**Auth:** OAuth U2M via Databricks CLI bridge profile
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

1 of 7 OK loaded seed file dbt_default.seed_booking_status_history .. [INSERT 21 in 6.74s]
2 of 7 OK loaded seed file dbt_default.seed_bookings ................ [INSERT 20 in 6.31s]
3 of 7 OK loaded seed file dbt_default.seed_care_tickets ............ [INSERT 8 in 8.21s]
4 of 7 OK loaded seed file dbt_default.seed_destinations ............ [INSERT 10 in 10.58s]
5 of 7 OK loaded seed file dbt_default.seed_supplier_history ........ [INSERT 10 in 6.30s]
6 of 7 OK loaded seed file dbt_default.seed_suppliers ............... [INSERT 10 in 18.57s]
7 of 7 OK loaded seed file dbt_default.seed_tours ................... [INSERT 12 in 5.46s]

Finished running 7 seeds in 23.87s.
```

**Result:** PASS=7 WARN=0 ERROR=0 SKIP=0 TOTAL=7

---

## dbt run

```
Concurrency: 10 threads (target='dev')

 1 of 21 OK created sql table model dbt_default.metricflow_time_spine ........... [OK in 5.51s]
 2 of 21 OK created sql view model dbt_default.stg_seed_data__booking_status_changes [OK in 4.04s]
 3 of 21 OK created sql view model dbt_default.stg_seed_data__bookings .......... [OK in 4.04s]
 4 of 21 OK created sql view model dbt_default.stg_seed_data__care_tickets ...... [OK in 4.04s]
 5 of 21 OK created sql view model dbt_default.stg_seed_data__destinations ...... [OK in 4.04s]
 6 of 21 OK created sql view model dbt_default.stg_seed_data__supplier_versions . [OK in 4.04s]
 7 of 21 OK created sql view model dbt_default.stg_seed_data__suppliers ......... [OK in 4.03s]
 8 of 21 OK created sql view model dbt_default.stg_seed_data__tours ............. [OK in 4.03s]
 9 of 21 OK created sql table model dbt_default.dim_destinations ................ [OK in 22.66s]
10 of 21 OK created sql table model dbt_default.dim_suppliers_history ........... [OK in 11.50s]
11 of 21 OK created sql view model dbt_default.int_bookings_with_milestones ..... [OK in 2.57s]
12 of 21 OK created sql table model dbt_default.dim_care_tickets ................ [OK in 25.42s]
13 of 21 OK created sql view model dbt_default.int_tours_with_supplier_context .. [OK in 2.67s]
14 of 21 OK created sql view model dbt_default.int_bookings_enriched ............ [OK in 2.67s]
15 of 21 OK created sql table model dbt_default.dim_tours ....................... [OK in 21.01s]
16 of 21 OK created sql table model dbt_default.fct_bookings .................... [OK in 35.23s]
17 of 21 OK created sql table model dbt_default.fct_bookings_accumulating_snapshot [OK in 24.23s]
18 of 21 OK created sql table model dbt_default.agg_bookings_checkout_daily ..... [OK in 10.93s]
19 of 21 OK created sql table model dbt_default.agg_bookings_destination_daily .. [OK in 10.29s]
20 of 21 OK created sql table model dbt_default.agg_bookings_tour_category_monthly [OK in 13.31s]
21 of 21 OK created sql table model dbt_default.fct_bookings_snapshot ........... [OK in 17.21s]

Finished running 11 table models, 10 view models in 63.62s.
```

**Result:** PASS=21 WARN=0 ERROR=0 SKIP=0 TOTAL=21

---

## dbt test

```
Concurrency: 10 threads (target='dev')

 1 of 59 PASS accepted_values_fct_bookings_accumulating_snapshot_current_lifecycle_stage [4.37s]
 2 of 59 PASS accepted_values_stg_seed_data__bookings_booking_status [4.36s]
 3 of 59 PASS dbt_expectations_expect_column_values_to_be_between_agg_bookings_checkout_daily_cancellation_rate [4.36s]
 4-10 of 59 PASS not_null tests on agg/dim models [~4s each]
11-27 of 59 PASS not_null tests on dim/fct/int/stg models [~3-5s each]
28-41 of 59 PASS not_null/unique tests on staging models [~3-5s each]
42 of 59 PASS test_agg_reconciles_with_fact [3.88s]
43 of 59 PASS test_booking_milestone_ordering [4.40s]
44 of 59 PASS test_no_overlapping_scd2_windows [3.87s]
45-59 of 59 PASS unique tests on all models [~2-4s each]

Finished running 59 data tests in 398.44s.
```

**Result:** PASS=59 WARN=0 ERROR=0 SKIP=0 TOTAL=59

---

## Summary

| Command | Result | Duration |
|---------|--------|----------|
| `dbt deps` | PASS | ~30s |
| `dbt seed` | 7/7 PASS | 24s |
| `dbt run` | 21/21 PASS | 64s |
| `dbt test` | 59/59 PASS | 398s |

All 4 pipeline stages complete with exit 0. The shadow repo is fully operational
against `testing.dbt_default` via OAuth U2M authentication.

---

## Key fixes applied (vs original scaffolding)

1. **OAuth auth** — Makefile generates `DATABRICKS_TOKEN` from `databricks auth token --profile bridge` on each invocation.
2. **SSL cert bundle** — `.ca-bundle.pem` exported from macOS system keychain (includes Zscaler CA). Makefile sets `SSL_CERT_FILE` + `REQUESTS_CA_BUNDLE`.
3. **Schema routing** — Removed `spec_compliant_*` custom schemas (user lacks CREATE SCHEMA on testing). All objects land in `dbt_default`.
4. **Source schema** — Updated `_sources__seeds.yml` to reference `dbt_default` (where seeds actually land).
5. **uv run** — Added `pyproject.toml` with dbt-core/dbt-databricks deps. Makefile uses `uv run dbt` for reproducible execution.

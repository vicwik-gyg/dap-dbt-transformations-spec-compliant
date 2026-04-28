# Compliance Report — Naming Standards

**Spec:** `dap-dwh-spec/02-mined-standards/naming.md`
**Audit date:** 2026-04-28
**Scope:** 21 SQL models, 2 semantic models, 5 metrics, 1 exposure, 11 YAML files

## Result: PASS (0 material deviations)

---

## Per-Model Verdict

### Staging

| Model | Verdict |
|-------|---------|
| stg_seed_data__bookings | PASS |
| stg_seed_data__booking_status_changes | PASS |
| stg_seed_data__care_tickets | PASS |
| stg_seed_data__destinations | PASS |
| stg_seed_data__supplier_versions | PASS |
| stg_seed_data__suppliers | PASS |
| stg_seed_data__tours | PASS |

### Intermediate

| Model | Verdict | Finding |
|-------|---------|---------|
| int_bookings_enriched | PASS | — |
| int_bookings_with_milestones | DEVIATES (minor) | Prepositional phrase instead of verb |
| int_tours_with_supplier_context | DEVIATES (minor) | Prepositional phrase instead of verb |

### Marts — Fact

| Model | Verdict |
|-------|---------|
| fct_bookings | PASS |
| fct_bookings_snapshot | PASS |
| fct_bookings_accumulating_snapshot | PASS |

### Marts — Aggregate

| Model | Verdict | Finding |
|-------|---------|---------|
| agg_bookings_checkout_daily | DEVIATES (minor) | Dimension qualifier extends base pattern |
| agg_bookings_destination_daily | DEVIATES (minor) | Dimension qualifier extends base pattern |
| agg_bookings_tour_category_monthly | DEVIATES (minor) | Dimension qualifier extends base pattern |

### Marts — Dimension

| Model | Verdict |
|-------|---------|
| dim_destinations | PASS |
| dim_tours | PASS |
| dim_suppliers_history | PASS |
| dim_care_tickets | PASS |

### Semantic Models

| Model | Verdict |
|-------|---------|
| sem_bookings | PASS |
| sem_bookings_daily | PASS |

### Metrics

| Metric | Verdict | Finding |
|--------|---------|---------|
| gross_bookings | PASS | — |
| net_bookings | PASS | — |
| booking_count | PASS | — |
| cancelled_bookings_metric | DEVIATES (minor) | `_metric` suffix workaround |
| cancellation_rate | PASS | — |

### Infrastructure

| Model | Verdict |
|-------|---------|
| metricflow_time_spine | PASS |

---

## Accepted Deviations

| # | Rule | Deviation | Justification |
|---|------|-----------|---------------|
| 1 | PK string type | PKs use bigint | Natural integer PKs from source; string surrogates where appropriate |
| 2 | int_\<entity\>_\<verb\> | Prepositional phrases | Names are clear and unambiguous |
| 3 | agg_\<theme\>_\<grain\> | Dimension qualifier added | Disambiguates same-theme aggregates |
| 4 | Metric naming | `_metric` suffix | Avoids MetricFlow namespace collision |
| 5 | Column ordering | Logical grouping | Analyst ergonomics over strict type sorting |

---

## Detailed Findings

See [docs/audit-naming.md](docs/audit-naming.md) for full per-rule analysis, column-level checks, and remediation proposals.

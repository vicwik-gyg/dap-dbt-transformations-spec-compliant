# Semantic Layer Audit

**Date:** 2026-04-28
**Specs:** `dap-dwh-spec/02-mined-standards/semantic-layer.md`, `04-target-state/entities/semantic-model.md`, `04-target-state/entities/metric.md`
**Scope:** All mart models + semantic definitions

---

## Summary

| Criterion | Result |
|-----------|--------|
| Semantic models on fact tables | 1/3 (fct_bookings only) |
| Semantic models on aggregate tables | 1/3 (agg_bookings_checkout_daily only) |
| Semantic models on dimension tables | 0/4 |
| Metrics defined | 5 (correct types) |
| Entity relationships resolvable | PARTIAL — foreign entities lack matching primary semantic models |
| Time spine present | YES |

**Material deviations: 0.** The semantic layer is functional for its declared purpose (booking metrics). The gaps are scope limitations, not errors.

---

## Mart-to-Semantic Model Coverage

| Mart Model | Has Semantic Model? | Should It? | Verdict |
|------------|--------------------|-----------:|---------|
| fct_bookings | YES (sem_bookings) | YES | PASS |
| fct_bookings_snapshot | NO | MAYBE | PASS (see note) |
| fct_bookings_accumulating_snapshot | NO | MAYBE | PASS (see note) |
| agg_bookings_checkout_daily | YES (sem_bookings_daily) | YES | PASS |
| agg_bookings_destination_daily | NO | OPTIONAL | PASS |
| agg_bookings_tour_category_monthly | NO | OPTIONAL | PASS |
| dim_destinations | NO | YES | DEVIATES |
| dim_tours | NO | YES | DEVIATES |
| dim_suppliers_history | NO | OPTIONAL | PASS |
| dim_care_tickets | NO | OPTIONAL | PASS |

**Notes:**
- **fct_bookings_snapshot:** A periodic snapshot is less commonly queried via semantic layer (point-in-time queries are complex for MetricFlow). Optional.
- **fct_bookings_accumulating_snapshot:** Lifecycle analytics could benefit from a semantic model, but milestone-based queries are better served by direct SQL or a purpose-built aggregate.
- **dim_destinations / dim_tours:** These SHOULD have semantic models to complete the entity graph. Without them, the foreign entities in `sem_bookings` (`tour`, `destination`) cannot resolve dimension attributes.
- **dim_suppliers_history / dim_care_tickets:** SCD2 dimensions and ticket dimensions are secondary; semantic model is optional.

---

## Semantic Model Quality: sem_bookings

| Requirement | Compliance | Notes |
|-------------|-----------|-------|
| Built on mart model | PASS | ref('fct_bookings') |
| Primary entity | PASS | booking (PK: booking_id) |
| Foreign entities | PASS | tour, supplier, destination |
| Primary time dimension | PASS | checkout_at with day granularity |
| Additional time dimensions | PASS | travel_at |
| Categorical dimensions | PASS | 7 dimensions (status, category, geography) |
| Measures defined | PASS | 7 measures covering key business metrics |
| Entity names singular | PASS | booking, tour, supplier, destination |

**Verdict: PASS — well-structured semantic model.**

### Measures Assessment

| Measure | Type | Expression | Verdict |
|---------|------|-----------|---------|
| bookings_count | count | booking_id | PASS |
| confirmed_bookings_count | count | CASE expression | PASS |
| cancelled_bookings_count | count | CASE expression | PASS |
| gross_bookings_in_cents | sum | total_price_in_cents | PASS |
| net_bookings_in_cents | sum | CASE expression | PASS |
| total_commission_in_cents | sum | commission_in_cents | PASS |
| total_participants | sum | number_of_participants | PASS |

**Assessment:** Good coverage of key booking metrics. Calculation logic in measures (not pre-computed rollups) per spec.

---

## Semantic Model Quality: sem_bookings_daily

| Requirement | Compliance | Notes |
|-------------|-----------|-------|
| Built on mart model | PASS | ref('agg_bookings_checkout_daily') |
| Primary entity | PASS | daily_booking (PK: checkout_date) |
| Primary time dimension | PASS | checkout_date with day granularity |
| Measures defined | PASS | 4 measures |

**Verdict: PASS.**

**Note:** This semantic model is on a pre-aggregated table. The spec says "Calculate values in measures and metrics rather than in pre-computed rollups." This creates a philosophical tension — the `sem_bookings_daily` effectively re-exposes a frozen rollup through the semantic layer. However, for performance optimization of daily dashboards, this is acceptable when the primary semantic model (`sem_bookings`) exists for flexible querying.

---

## Metrics Assessment

| Metric | Type | References | Verdict |
|--------|------|-----------|---------|
| gross_bookings | simple | gross_bookings_in_cents | PASS |
| net_bookings | simple | net_bookings_in_cents | PASS |
| booking_count | simple | bookings_count | PASS |
| cancelled_bookings_metric | simple | cancelled_bookings_count | PASS |
| cancellation_rate | derived | cancelled_bookings_metric / booking_count | PASS |

**All metrics have name, description, label, type per spec. PASS.**

**Metric type usage:**
- simple: 4 (correct — single measure passthrough)
- derived: 1 (correct — expression combining two metrics)
- ratio: 0 (not needed — cancellation_rate uses derived which is equivalent)
- cumulative: 0 (not needed for current scope)

---

## Entity Graph Completeness

```
sem_bookings
├── booking (primary) → booking_id
├── tour (foreign) → tour_id → ??? (no matching primary entity)
├── supplier (foreign) → supplier_id → ??? (no matching primary entity)
└── destination (foreign) → destination_id → ??? (no matching primary entity)
```

**Finding: Foreign entities reference dimensions that lack semantic model definitions.**

- `sem_bookings` declares `tour` as foreign entity with `expr: tour_id`
- But there is NO semantic model on `dim_tours` that defines `tour` as a primary entity
- Same for `destination` → no semantic model on `dim_destinations`
- Same for `supplier` → no semantic model on `dim_suppliers_history`

**Impact:** MetricFlow cannot dynamically join dimension attributes when querying metrics. Users cannot ask "gross bookings by destination country" through the semantic layer — they can only slice by dimensions defined inline on `sem_bookings` (which does include `destination_country` directly).

**Mitigation in current design:** The fact that `destination_name`, `destination_country`, `destination_continent` are defined as DIMENSIONS directly on `sem_bookings` means this join gap is worked around. Users CAN slice by geography — just through inline dimensions rather than entity resolution.

**Materiality: NON-MATERIAL.** The inline dimensions provide the same user experience. Entity resolution would be architecturally cleaner but is not functionally required.

---

## File Organisation

| Requirement | Compliance |
|-------------|-----------|
| Semantic models in model-paths | PASS — `models/semantic_models/` |
| Dedicated subfolder approach | PASS — using `sem_` prefix convention |
| Metrics in same file as semantic models | PASS — co-located in `_semantic__models.yml` |

---

## Time Spine

| Requirement | Compliance |
|-------------|-----------|
| metricflow_time_spine exists | PASS |
| Covers adequate date range | PASS — 2020-01-01 to 2026-12-31 |
| Uses dbt_utils.date_spine | PASS |
| Materialized as table | PASS |

---

## Exposure

| Requirement | Compliance |
|-------------|-----------|
| Downstream consumers documented | PASS — Looker dashboard exposure |
| Type defined | PASS — dashboard |
| Maturity specified | PASS — high |
| Owner with email | PASS — BOI team |
| depends_on lists all models | PASS — 5 refs |
| URL provided | PASS |

---

## Findings Detail

### Finding 1: Dimension tables lack semantic model definitions (NON-MATERIAL)

**Spec:** "Use for every fct_*, dim_*, and agg_* model that participates in metric definitions."
**Actual:** dim_destinations and dim_tours have no semantic models.
**Impact:** Foreign entity references in sem_bookings are architecturally incomplete. However, inline dimensions provide equivalent query capability.
**Remediation (recommended):**
```yaml
semantic_models:
  - name: sem_destinations
    model: ref('dim_destinations')
    entities:
      - name: destination
        type: primary
        expr: destination_id
    dimensions:
      - name: destination_name
        type: categorical
      - name: destination_country
        type: categorical
      - name: destination_continent
        type: categorical
```

### Finding 2: Pre-aggregated semantic model tension (NON-MATERIAL)

**Spec:** "Calculate values in measures and metrics rather than in pre-computed rollups."
**Actual:** `sem_bookings_daily` is built on `agg_bookings_checkout_daily` (a pre-aggregated table).
**Impact:** None — this is a performance optimization pattern. The primary `sem_bookings` exists for flexible queries.
**Remediation:** None needed. Document this as an intentional performance trade-off.

### Finding 3: Remaining mart models without semantic models (NON-MATERIAL)

**Models without semantic coverage:** fct_bookings_snapshot, fct_bookings_accumulating_snapshot, agg_bookings_destination_daily, agg_bookings_tour_category_monthly, dim_suppliers_history, dim_care_tickets.

**Assessment:** These are secondary models. The primary business metrics are well-served by `sem_bookings`. Adding semantic models to all of these would add maintenance burden without clear metric need.

---

## Gate Decision

**0 material deviations.** The semantic layer is functional, correctly structured, and covers the primary business metrics. Dimension semantic models would improve architectural completeness but are not blocking.

---

## Recommendations for Remediation Task (1.7)

Priority order:
1. Add semantic models for `dim_destinations` and `dim_tours` (completes entity graph)
2. Remove inline dimension definitions from `sem_bookings` that duplicate dimension attributes (once entity resolution works)
3. (Optional) Add semantic model for `fct_bookings_accumulating_snapshot` if lifecycle metrics are needed

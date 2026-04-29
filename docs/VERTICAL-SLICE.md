# Vertical Slice: Supplier Lifecycle Stage

## 3.1 Target Selection

**Chosen mart**: `dim_supplier_lifecycle_stage` (supply domain)

**Rationale**:
- Not in the shadow repo's existing 25 models (shadow has `dim_suppliers_history` SCD2, but no lifecycle funnel)
- Lineage depth = 5 layers (source → staging → intermediate → mart tier 1 → mart tier 2 → current-state view)
- Business-critical: supplier lifecycle funnel drives account management, sales targeting, and churn prevention reporting
- Self-contained: doesn't depend on massive cross-domain models like `fact_booking`
- Exercises key spec patterns: date spine, CDC processing, SCD2, window functions, stage detection, current-state views

**Candidates considered**:
| Candidate | Depth | Why rejected |
|-----------|-------|--------------|
| `agg_supply_demand_delta` | 4 | Too many external deps (fact_booking, dim_tour_option, agg_sellout) |
| `fact_care_ticket` (vault) | 4 | 2277 LOC of intermediates, 15+ external deps |
| `dim_contact_reason` | 2 | Too shallow (source → int → mart) |
| `connectivity/fact_system_integration_state` | 2 | No intermediates, trivial lineage |

## 3.2 Lineage Map

```
seed_dim_date ─────────────────────────────────────┐
seed_tour_option_bookable_history ─────────────────┤
seed_tour_history ─────────────────────────────────┤
                                                   ▼
                              ┌─────────────────────────────────┐
                              │ stg_seed_data__dim_date          │
                              │ stg_seed_data__tour_history      │  Layer: Staging (views)
                              │ stg_seed_data__tour_option_...   │
                              │ stg_seed_data__reviews           │
                              │ stg_seed_data__supplier_dim      │
                              │ stg_seed_data__supplier_status_  │
                              │   _history                       │
                              └──────────────┬──────────────────┘
                                             │
                                             ▼
                              ┌─────────────────────────────────┐
                              │ int_tour_online_daily            │  Layer: Intermediate (view)
                              │   Combines bookable CDC +       │
                              │   tour history into daily grain  │
                              └──────────────┬──────────────────┘
                                             │
                                             ▼
                              ┌─────────────────────────────────┐
                              │ dim_tour_lifecycle_stage_history │  Layer: Mart (table, SCD2)
                              │   Stage per tour per day,       │
                              │   collapsed into runs           │
                              └──────────────┬──────────────────┘
                                             │
                              ┌──────────────┼──────────────────┐
                              ▼                                  ▼
               ┌──────────────────────┐          ┌──────────────────────────────┐
               │ dim_tour_lifecycle_   │          │ dim_supplier_lifecycle_stage_ │
               │   stage              │          │   history                     │ Mart (table)
               │ (current-state view) │          │ Aggregates tour stages to     │
               └──────────────────────┘          │ supplier level + deactivation │
                                                 └───────────────┬──────────────┘
                                                                 │
                                                                 ▼
                                                 ┌──────────────────────────────┐
                                                 │ dim_supplier_lifecycle_stage  │
                                                 │ (current-state view)          │ Mart (table)
                                                 └──────────────────────────────┘
```

**Model inventory** (11 new models + 6 new seeds):

| Model | Layer | Materialization | New seed required |
|-------|-------|-----------------|-------------------|
| `stg_seed_data__dim_date` | staging | view | `seed_dim_date` (366 rows) |
| `stg_seed_data__tour_history` | staging | view | `seed_tour_history` (18 rows) |
| `stg_seed_data__tour_option_bookable_history` | staging | view | `seed_tour_option_bookable_history` (15 rows) |
| `stg_seed_data__reviews` | staging | view | `seed_reviews` (11 rows) |
| `stg_seed_data__supplier_dim` | staging | view | `seed_supplier_dim` (5 rows) |
| `stg_seed_data__supplier_status_history` | staging | view | `seed_supplier_status_history` (6 rows) |
| `int_tour_online_daily` | intermediate | view | — |
| `dim_tour_lifecycle_stage_history` | mart | table | — |
| `dim_tour_lifecycle_stage` | mart | table | — |
| `dim_supplier_lifecycle_stage_history` | mart | table | — |
| `dim_supplier_lifecycle_stage` | mart | table | — |

## 3.5 Validation Results

Full `dbt build` (seed + run + test) on 2026-04-29:

```
dbt seed:  PASS=13 (6 new + 7 existing)
dbt run:   PASS=32 (11 new + 21 existing)
dbt test:  PASS=97 (38 new + 59 existing)
Total:     PASS=138 WARN=0 ERROR=0 SKIP=0
```

Target: `testing.dbt_default` via Databricks OAuth U2M.

## 3.6 Retrospective

### What conventions worked as-is
- **Naming**: `stg_<source>__<entity>`, `int_<entity>_<verb>`, `dim_<entity>` all fit naturally
- **Layering**: staging (view, no joins) → intermediate (view, transforms) → mart (table) progression was clear
- **SCD2 pattern**: the shadow repo already had `dim_suppliers_history` as precedent; lifecycle history followed same structure
- **Testing**: unique/not_null on keys, accepted_values on enums — covered all important contracts
- **Schema YAML**: `_<domain>__models.yml` file-per-directory pattern scaled cleanly

### Conventions that had gaps
1. **Incremental strategy not exercisable**: Production `int_tour_online_daily` uses `incremental` with `replace_where`. Seeds are too small to meaningfully test incremental behavior. The spec should note that vertical slices may use `table` or `view` where production uses `incremental`, with a separate incremental-specific test harness.

2. **`sampled_ref` vs `ref`**: Production uses custom macros (`sampled_ref`, `sampled_source`, `sampled_vault_ref`, `sampled_prod_ref`) that don't exist in the shadow repo. The spec doesn't address how to handle cross-catalog references or sampled vs full table selectors. Recommendation: add a spec section on macro abstraction for source resolution.

3. **Vault vs non-vault layering**: Production care domain splits models between `models/vault/care/` and `models/marts/care/`. The lifecycle models live in non-vault `models/marts/supply/`. The spec doesn't define when vault layering applies. This didn't block the slice (supply domain is non-vault) but would matter for care domain vertical slices.

4. **Date spine ownership**: The date spine (`dim_date_v3`) is a cross-cutting utility owned by DWH, referenced by many domains. The spec doesn't address shared reference tables vs domain-owned staging. In the shadow repo, each domain brings its own staging; sharing a single `stg_seed_data__dim_date` across domains would need a shared staging layer.

### What was harder than expected
- Designing seed data that exercises all 5 lifecycle stages (Created, Pre-Activated, Activated, Dormant, Churned) plus deactivation overrides required careful planning of temporal relationships
- The `count_if()` function used in supplier aggregation is Databricks-specific SQL; portability wasn't an issue since we target Databricks, but it's worth noting in the spec

### What's missing from the spec
1. **Cross-domain reference strategy**: How to share date spines, currency rates, and other utility models across domains without circular deps
2. **Incremental testing guidance**: How to validate incremental models against seeds (which are inherently full-refresh)
3. **CDC processing pattern**: The spec covers archetypes but not the common pattern of "binlog → validity periods → daily expansion"
4. **Multi-tier marts**: The spec's layer hierarchy is staging → intermediate → mart, but this slice has mart → mart dependencies (tour lifecycle feeds supplier lifecycle). Clarify whether intermediate-to-intermediate and mart-to-mart refs are acceptable

# Slice Selection

This document describes the ~25 models selected for the reference implementation,
covering all 11 entity archetypes from the dap-dwh-spec.

## Selection criteria

1. Cover all 11 archetypes defined in the spec
2. Prefer booking/supply/care domains — GYG's core business
3. Keep dependencies self-contained (seed-based sources)
4. Each model demonstrates multiple rules simultaneously
5. Real-repo inspiration cited where applicable

## Archetype coverage

| # | Archetype | Models | Real-repo inspiration |
|---|-----------|--------|----------------------|
| 1 | Staging (DB source) | `stg_seed_data__bookings`, `stg_seed_data__suppliers`, `stg_seed_data__destinations`, `stg_seed_data__tours` | `stg_country_corridor_mapping`, `stg_supplier_campaigns_conversion` |
| 2 | Staging (Kafka/event) | `stg_seed_data__booking_status_changes`, `stg_seed_data__supplier_versions`, `stg_seed_data__care_tickets` | Kafka topic patterns in braze/care staging |
| 3 | Intermediate | `int_bookings_enriched`, `int_bookings_with_milestones`, `int_tours_with_supplier_context` | `int_booking_cancellation_category`, `int_supplier_email_campaign_conversion` |
| 4 | Conformed Dimension | `dim_destinations`, `dim_tours`, `dim_care_tickets` | `dim_location`, `dim_activity_config`, `dim_agent_activity` |
| 5 | SCD Type 2 | `dim_suppliers_history` | `dim_supplier_history`, `dim_booking_history` |
| 6 | Transaction Fact | `fct_bookings` | `fact_booking` (473 LOC) |
| 7 | Periodic Snapshot | `fct_bookings_snapshot` | `fact_booking_snapshot` |
| 8 | Accumulating Snapshot | `fct_bookings_accumulating_snapshot` | No direct equivalent — built from `seed_booking_status_history` |
| 9 | Aggregate Mart | `agg_bookings_checkout_daily`, `agg_bookings_destination_daily`, `agg_bookings_tour_category_monthly` | `agg_bookings_checkout_date_daily`, `agg_bookings_tour_checkout_daily` |
| 10 | Semantic Model | `sem_bookings`, `sem_bookings_daily` | No MetricFlow models exist in real repo (gap identified) |
| 11 | Metrics | `gross_bookings`, `net_bookings`, `booking_count`, `cancellation_rate`, `total_bookings`, `cancelled_bookings` | No metrics exist in real repo (gap identified) |
| 12 | Exposure | `looker_booking_performance_dashboard` | No exposures exist in real repo (gap identified) |

## Model inventory (25 models)

### Staging layer (7 models)
| Model | Source | Rationale |
|-------|--------|-----------|
| `stg_seed_data__bookings` | `seed_bookings` | Core transaction staging — demonstrates N01, L01, L02 |
| `stg_seed_data__booking_status_changes` | `seed_booking_status_history` | Event/Kafka pattern — feeds accumulating snapshot |
| `stg_seed_data__suppliers` | `seed_suppliers` | Current-state entity staging |
| `stg_seed_data__supplier_versions` | `seed_supplier_history` | SCD2 source staging — feeds dim_suppliers_history |
| `stg_seed_data__destinations` | `seed_destinations` | Reference data staging |
| `stg_seed_data__tours` | `seed_tours` | Catalog staging — mid-complexity entity |
| `stg_seed_data__care_tickets` | `seed_care_tickets` | Cross-domain (care) staging |

### Intermediate layer (3 models)
| Model | Dependencies | Rationale |
|-------|-------------|-----------|
| `int_bookings_enriched` | stg bookings + tours + destinations | Multi-table enrichment with derivations |
| `int_bookings_with_milestones` | stg booking_status_changes | Pivot/aggregation pattern for accumulating snapshot |
| `int_tours_with_supplier_context` | stg tours + suppliers + destinations | Denormalization pattern for dim consumption |

### Mart layer — Dimensions (4 models)
| Model | Archetype | Rationale |
|-------|-----------|-----------|
| `dim_destinations` | Conformed dimension | Simple reference dimension |
| `dim_tours` | Conformed dimension | Entity dimension with supplier context |
| `dim_suppliers_history` | SCD Type 2 | History tracking with surrogate key and version numbering |
| `dim_care_tickets` | Conformed dimension | Cross-domain dimension with derived metrics |

### Mart layer — Facts (3 models)
| Model | Archetype | Rationale |
|-------|-----------|-----------|
| `fct_bookings` | Transaction fact | Core transaction table |
| `fct_bookings_snapshot` | Periodic snapshot | Point-in-time capture of confirmed bookings |
| `fct_bookings_accumulating_snapshot` | Accumulating snapshot | Lifecycle milestone tracking |

### Mart layer — Aggregates (3 models)
| Model | Grain | Rationale |
|-------|-------|-----------|
| `agg_bookings_checkout_daily` | checkout_date | Daily business review grain |
| `agg_bookings_destination_daily` | checkout_date × destination | Geographic performance |
| `agg_bookings_tour_category_monthly` | checkout_month × category | Strategic category review |

### Semantic layer (5 items)
| Item | Type | Rationale |
|------|------|-----------|
| `sem_bookings` | Semantic model | Full MetricFlow model on fct_bookings |
| `sem_bookings_daily` | Semantic model | Pre-aggregated model on agg_bookings_checkout_daily |
| `gross_bookings`, `net_bookings`, `booking_count`, `cancellation_rate`, `total_bookings`, `cancelled_bookings` | Metrics | Covers simple + derived metric types |
| `looker_booking_performance_dashboard` | Exposure | Links models to downstream dashboard |

## Gaps identified in real repo

1. **No MetricFlow semantic models** — the real repo has no `semantic_models:` YAML blocks
2. **No metrics** — no `metrics:` definitions anywhere in the codebase
3. **No exposures** — no `exposures:` definitions linking to downstream consumers
4. **No accumulating snapshot** — the closest pattern is `fact_booking_snapshot` (periodic only)
5. **Staging naming inconsistency** — real repo has `stg_*` without consistent `stg_<source>__<entity>` convention

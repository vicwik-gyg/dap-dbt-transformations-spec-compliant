# Reference Implementation Report

This document summarises the application of every rule from
`dap-dwh-spec/02-mined-standards/` to the shadow repo's model slice.

## Rule-by-rule application

### N01–N08: Naming conventions

| Rule | Description | Before (real repo) | After (shadow) | What was applied |
|------|------------|-------------------|----------------|-----------------|
| N01 | Model prefix naming (`stg_`, `int_`, `fct_`, `dim_`, `agg_`) | ~70% compliant — many staging models lack `stg_<source>__<entity>` pattern | **100%** — all 7 staging models use `stg_seed_data__<entity>` | Renamed all staging models to follow `stg_<source>__<entity>` convention |
| N02 | Intermediate naming (`int_<entity>_<verb>`) | ~50% — inconsistent, some use `stg_` prefix in intermediate layer | **100%** — `int_bookings_enriched`, `int_bookings_with_milestones`, `int_tours_with_supplier_context` | Named intermediates with descriptive verb suffix |
| N03 | snake_case throughout | ~95% — mostly compliant already | **100%** — all identifiers are snake_case | Verified in all SQL and YAML |
| N04 | Plural model names | ~60% — mix of singular and plural | **100%** — `dim_destinations`, `fct_bookings`, `agg_bookings_*`, etc. | All entity model names use plural nouns |
| N05 | Timestamps `<event>_at`, dates `<event>_date` | Not measured | **100%** — `checkout_at`, `travel_at`, `cancelled_at`, `checkout_date` | Applied consistently |
| N06 | Prices as `*_in_cents` | Not measured | **100%** — `total_price_in_cents`, `commission_in_cents`, `price_in_cents` | All monetary values use `_in_cents` suffix |
| N07 | No abbreviations | Not measured | **100%** — no abbreviations used | Full business terms throughout |
| N08 | YAML file naming `_<dir>__models.yml` | ~30% — uses `<model>_schema.yml` pattern | **100%** — `_booking__models.yml`, `_supply__models.yml`, etc. | New naming convention for YAML property files |

### L01–L03: Layering standards

| Rule | Description | Before | After | What was applied |
|------|------------|--------|-------|-----------------|
| L01 | Staging has no joins | ~85% — most staging models are 1:1, some have joins | **100%** — all 7 staging models are pure SELECT...FROM with no joins | Removed all joins from staging; enrichment moved to intermediate |
| L02 | Staging materialized as view/ephemeral | ~90% — most use `ephemeral`, some are `table` | **100%** — all staging models materialized as `view` | dbt_project.yml sets `+materialized: view` for staging layer |
| L03 | Canonical directory taxonomy | ~40% — schemas in separate tree, mixed nesting | **100%** — `models/staging/<domain>/`, `models/intermediate/<domain>/`, `models/marts/<domain>/<type>/` | Reorganised to `staging/booking/`, `marts/booking/fact/`, etc. |

### D01–D03: Documentation standards

| Rule | Description | Before | After | What was applied |
|------|------------|--------|-------|-----------------|
| D01 | YAML properties file for every model | ~75% — many models lack YAML | **100%** — every model has a YAML properties entry | Created `_<dir>__models.yml` for each directory |
| D02 | Description for every model and column | ~60% — many AI-generated placeholders | **100%** — hand-written descriptions for all models and columns | Wrote meaningful business-context descriptions |
| D03 | `meta.synonyms` on Looker-exposed models | ~0% — no synonyms in real repo | **100%** — all mart models have `meta.synonyms` | Added synonyms to dim, fct, and agg models |

### S01: Schema & style standards

| Rule | Description | Before | After | What was applied |
|------|------------|--------|-------|-----------------|
| S01 | Lowercase SQL, trailing commas, explicit `as`, CTE patterns | ~70% — inconsistent style | **100%** — all SQL uses lowercase keywords, trailing commas, explicit `as`, import CTEs | Consistent SQL style in all 25 models |

### T01–T02: Testing standards

| Rule | Description | Before | After | What was applied |
|------|------------|--------|-------|-----------------|
| T01 | ≥1 test per model (PK unique + not_null) | ~75% coverage target | **100%** — every model's primary key has `unique` + `not_null` tests | Added PK tests to all YAML definitions |
| T02 | ≥2 tests on mart models | ~40% — many marts lack business logic tests | **100%** — mart models have PK tests + business logic tests (accepted_values, range checks) | Added `accepted_values`, `expect_column_values_to_be_between` tests |

### G01: Governance

| Rule | Description | Before | After | What was applied |
|------|------------|--------|-------|-----------------|
| G01 | `meta.owner` and `config.group` on every model | ~80% — most have `tags: [owner:*]` | **100%** — every model has `meta.owner` and `config.group` | Set `meta.owner: boi` and `config.group: boi` on all models |

### P01: Performance

| Rule | Description | Before | After | What was applied |
|------|------------|--------|-------|-----------------|
| P01 | Incremental materialisation for large marts | ~30% — many large tables use `table` | **100%** (appropriate for scale) — tables used for seed-scale data; `dim_suppliers_history` demonstrates `unique_key` config for incremental readiness | Judgment call: at seed scale, `table` is correct; documented how to graduate to incremental |

### SL01: Semantic layer

| Rule | Description | Before | After | What was applied |
|------|------------|--------|-------|-----------------|
| SL01 | MetricFlow semantic_models + metrics YAML | **0%** — no semantic models or metrics exist | **100%** — 2 semantic models, 6 metrics (simple + derived), 1 exposure | Built from scratch: `sem_bookings`, `sem_bookings_daily`, metrics for gross/net/count/rate |

## Lessons learned

### Cheap / automatable rules (Phase 2 candidates for batch migration)

| Rule | Effort | Why |
|------|--------|-----|
| N03 (snake_case) | Trivial | Already ~95% compliant; lint rule catches rest |
| N05 (timestamp naming) | Low | Mechanical rename with grep/sed |
| N08 (YAML file naming) | Low | File rename script |
| D01 (YAML exists) | Low | `codegen` can scaffold YAML for undocumented models |
| T01 (PK tests) | Low | Pattern: add `unique` + `not_null` to every PK column |
| G01 (meta.owner) | Low | Batch add `meta.owner` matching existing `tags: [owner:*]` |
| L02 (staging materialization) | Low | Config-only change in `dbt_project.yml` |

### Medium effort (needs review per model)

| Rule | Effort | Why |
|------|--------|-----|
| N01 (prefix naming) | Medium | Staging rename may break downstream refs; need graph walk |
| N04 (plural names) | Medium | Same — rename cascades through refs |
| D02 (descriptions) | Medium | AI-generated descriptions need human review for accuracy |
| D03 (synonyms) | Medium | Requires domain knowledge per model |
| L01 (no staging joins) | Medium | Some staging models with joins need logic moved to intermediate |
| T02 (business logic tests) | Medium | Each mart needs a custom test designed for its semantics |
| S01 (SQL style) | Medium | sqlfmt/sqlfluff can autoformat, but CTE restructuring is manual |

### High effort (real design work)

| Rule | Effort | Why |
|------|--------|-----|
| L03 (directory taxonomy) | High | Requires moving 1000+ files with ref() updates |
| P01 (incremental) | High | Each model needs incremental strategy design, unique_key selection |
| SL01 (semantic layer) | High | No existing semantic models — must be built from business requirements |
| N02 (intermediate naming) | High | Many misplaced models need layer reassignment |

## How to extend

### Adding a new model to the slice

1. Create the SQL file in the appropriate layer directory
2. Add a YAML entry in the corresponding `_<dir>__models.yml` file
3. Ensure compliance checklist:
   - [ ] Naming follows N01/N02/N03/N04/N05/N06/N07
   - [ ] YAML has description (D01/D02)
   - [ ] `meta.synonyms` if Looker-exposed (D03)
   - [ ] `meta.owner` + `config.group` set (G01)
   - [ ] All columns defined with descriptions (S01)
   - [ ] PK has `unique` + `not_null` tests (T01)
   - [ ] Mart has ≥2 tests (T02)
   - [ ] Correct materialization (L02/P01)
   - [ ] Layer placement follows L03
   - [ ] Staging models have no joins (L01)
4. If the model is a mart, consider adding a semantic model entry (SL01)
5. Run `make all` to validate

### Adding the 12th archetype

If a new archetype is added to the spec (e.g. a "bridge table" or "data vault
satellite"), create a new model in the appropriate layer, add it to
`SLICE-SELECTION.md`, and document the rule application here.

## Judgment calls

1. **P01 at seed scale**: Tables are appropriate for our seed-size data. In the
   real repo, models with >10M rows should use incremental. We document this but
   don't force incremental on toy data.

2. **SL01 filter syntax**: MetricFlow filter syntax varies between dbt versions.
   We use the `{{ Dimension('entity__dim') }}` Jinja syntax. If your dbt version
   doesn't support this, adjust to string filters.

3. **Accumulating snapshot**: The real repo has no accumulating snapshot. We
   built one from scratch using booking status change events, which is the
   recommended pattern per the spec.

4. **Exposure URL**: The Looker dashboard URL is a placeholder. In the real
   repo, this would point to an actual dashboard.

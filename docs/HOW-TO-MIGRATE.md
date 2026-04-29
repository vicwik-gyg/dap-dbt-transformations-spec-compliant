# How to Migrate a Model

Step-by-step procedure for migrating one model from `dap-dbt-transformations` (source repo) into this shadow repo such that `shadow-spec-check` reports PASS and `dbt build` succeeds.

**One model at a time. Do not batch.**

For the full conventions reference (what a compliant model looks like), see the [MIGRATION-PLAYBOOK in dap-dwh-spec](https://github.com/vicwik-gyg/dap-dwh-spec/blob/main/04-target-state/MIGRATION-PLAYBOOK.md).

---

## Prerequisites

- This repo cloned and building (`make all` passes) — see [HOW-TO-RUN.md](../HOW-TO-RUN.md)
- Source repo (`dap-dbt-transformations`) cloned alongside for reference
- Familiarity with dbt models, YAML schema files, and SQL

---

## End-to-end procedure

### 1. Identify the source model

Pick the model to migrate. Record:
- Its path in `dap-dbt-transformations` (e.g., `models/staging/booking/stg_bookings.sql`)
- Its current name
- The source table(s) it reads from

### 2. Determine the archetype

Match by prefix/path — first match wins:

| Prefix / path | Archetype | Template |
|---------------|-----------|----------|
| `stg_` or `staging/` | staging | `stg___source__entities.sql` |
| `int_` | intermediate | `int___domain__entity.sql` |
| `dim_` + has `valid_from`/`is_current` | dim-scd-type-2 | `dim_entity.sql` |
| `dim_` | dim-conformed | `dim_entity.sql` |
| `fct_` + one row per event | fct-transaction | `fct_event.sql` |
| `fct_` + periodic grain | fct-periodic-snapshot | `fct_event.sql` |
| `fct_` + milestone accumulation | fct-accumulating-snapshot | `fct_event.sql` |
| `agg_` | agg-mart | `agg_theme_grain.sql` |

For the full decision tree, see [MIGRATION-PLAYBOOK §2](https://github.com/vicwik-gyg/dap-dwh-spec/blob/main/04-target-state/MIGRATION-PLAYBOOK.md#2-identify-archetype-decision-tree).

### 3. Create the compliant model name

Apply naming conventions:
- **Staging:** `stg_<source>__<entities>` (plural)
- **Intermediate:** `int_<entity>_<verb>`
- **Dimension:** `dim_<entities>`
- **Fact:** `fct_<events>`
- **Aggregate:** `agg_<theme>_<grain>`

All names: snake_case, no abbreviations, no `core_` prefix.

### 4. Scaffold

```bash
# Create the model file
touch models/<layer>/<domain>/<model_name>.sql

# Create or append to the YAML properties file
# Convention: models/<layer>/<domain>/_<domain>__models.yml
```

Copy the appropriate template from [dap-dwh-spec/04-target-state/templates/](https://github.com/vicwik-gyg/dap-dwh-spec/tree/main/04-target-state/templates) and perform substitutions.

### 5. Port the SQL logic

Copy the SELECT body from the source model. Apply layering constraints:

| Layer | Allowed | Not allowed |
|-------|---------|-------------|
| Staging | Rename, cast, booleans, categorise | Joins, aggregations, window functions |
| Intermediate | Joins, filters, enrichment | Direct source reads (must ref staging) |
| Marts | Business logic, joins to int/stg | Raw source reads |
| Aggregate | GROUP BY from facts/dims | Re-implementing upstream logic |

If the source model violates these constraints, split it across layers.

### 6. Write the YAML schema

In `_<domain>__models.yml`, add the model entry with:

```yaml
models:
  - name: <model_name>
    description: >
      One-paragraph business description. No blanks. No TODOs.
    config:
      materialized: <table|view|incremental>
    columns:
      - name: <pk_column>
        description: "Primary key — unique identifier for ..."
        data_type: string
        tests:
          - unique
          - not_null
      - name: <fk_column>
        description: "Foreign key to ..."
        data_type: string
        tests:
          - relationships:
              to: ref('<target_model>')
              field: <target_pk>
      - name: <enum_column>
        description: "Status of the ... Valid values: x, y, z."
        data_type: string
        tests:
          - accepted_values:
              values: ['x', 'y', 'z']
      # ... every column must have name + description + data_type
```

**Required tests:**
- `unique` + `not_null` on every primary key (always)
- `relationships` on every FK whose target model exists in this project
- `accepted_values` on enum columns with bounded, known domains

**If an enum is open-valued**, suppress with justification:
```yaml
      - name: tour_category
        description: "Open classification from source."
        meta:
          spec_check_suppress:
            - rule: "tests.accepted_values_on_enums"
              justification: "Unbounded domain — values from external source"
```

### 7. Parse and validate

```bash
# Must exit 0
make parse

# Must show PASS on all rules for your model
python -m scripts.spec_check.cli model <model_name>
```

If any rule shows DEVIATES: read the finding, look up the rule in [conventions.md](https://github.com/vicwik-gyg/dap-dwh-spec/blob/main/04-target-state/conventions.md), fix, re-run. Repeat until all PASS.

### 8. Build and test

```bash
dbt build --select <model_name>+1 --target dev
```

This builds the model + its immediate dependents and runs all schema tests.

Exit criteria: build succeeds, all tests pass.

### 9. Commit and open PR

```bash
git checkout -b migrate/<domain>/<model_name>
git add models/<layer>/<domain>/<model_name>.sql
git add models/<layer>/<domain>/_<domain>__models.yml
git commit -m "migrate(<domain>): <model_name> as <archetype>"
git push -u origin migrate/<domain>/<model_name>
```

PR body template:
```markdown
## Archetype
<archetype> — per dap-dwh-spec entities/<archetype>.md

## Source model
<link to source file in dap-dbt-transformations>

## Spec-check output
<paste output of: python -m scripts.spec_check.cli model <model_name>>

## Build output
<paste summary of: dbt build --select <model_name>+1>
```

---

## Worked example: `stg_seed_data__bookings`

```bash
# 1. Source: models/staging/booking/stg_bookings.sql in dap-dbt-transformations
# 2. Archetype: staging (prefix stg_, under staging/)
# 3. Compliant name: stg_seed_data__bookings (source=seed_data, entity=bookings, plural)
# 4. Scaffold: models/staging/booking/stg_seed_data__bookings.sql
# 5. Logic: SELECT with rename + cast only (no joins) ✓
# 6. YAML: unique + not_null on booking_id, description on all 15 columns
# 7. Parse + validate:
make parse
python -m scripts.spec_check.cli model stg_seed_data__bookings
# → 10 PASS / 0 DEVIATES / 8 NA ✓
# 8. Build:
dbt build --select stg_seed_data__bookings+1 --target dev
# → model OK, all tests pass ✓
# 9. Commit + PR
```

---

## Further reading

- [MIGRATION-PLAYBOOK (dap-dwh-spec)](https://github.com/vicwik-gyg/dap-dwh-spec/blob/main/04-target-state/MIGRATION-PLAYBOOK.md) — the full conventions reference (what compliant looks like)
- [HOW-TO-AUDIT.md](HOW-TO-AUDIT.md) — how to run and interpret the spec-check output
- [HOW-TO-RUN.md](../HOW-TO-RUN.md) — environment setup and build commands

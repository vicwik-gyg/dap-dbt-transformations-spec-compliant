# dap-dbt-transformations-spec-compliant

Reference implementation of a dbt project with 100% compliance to the
[dap-dwh-spec](https://github.com/vicwik-gyg/dap-dwh-spec) standards.

## What this is

A shadow repo containing ~25 dbt models selected to cover all 11 entity
archetypes from the spec. Every model complies with every applicable rule from
`dap-dwh-spec/02-mined-standards/`. The data is seeded from CSVs — no production
data access is required.

**This repo targets the `testing` catalog only.** There is no path to production.

## Why it exists

The real `dap-dbt-transformations` repo has 1,228 models. Applying the spec to
all of them at once is impractical. This shadow repo proves the spec is
implementable, documents the "how", and serves as a template for migrating the
real repo in phases.

## Quick start

```bash
# Prerequisites: dbt-core >=1.7, dbt-databricks, DATABRICKS_TOKEN set
# Your ~/.dbt/profiles.yml must have a dap_dbt_transformations profile
# pointing to the testing catalog.

# Install dependencies
make deps

# Seed sample data + run all models + run all tests
make all
```

See [HOW-TO-RUN.md](HOW-TO-RUN.md) for detailed setup and troubleshooting.

## Spec compliance

| Rule | Name | Status |
|------|------|--------|
| N01 | Model prefix naming | 100% |
| N02 | Intermediate naming | 100% |
| N03 | snake_case everywhere | 100% |
| N04 | Plural model names | 100% |
| L01 | Staging has no joins | 100% |
| L02 | Staging as view | 100% |
| L03 | Canonical directory taxonomy | 100% |
| D01 | YAML properties file per model | 100% |
| D02 | Description for every model | 100% |
| D03 | meta.synonyms on Looker-exposed models | 100% |
| S01 | Columns defined with descriptions | 100% |
| T01 | ≥1 test per model | 100% |
| T02 | ≥2 tests on marts | 100% |
| G01 | meta.owner on every model | 100% |
| P01 | Incremental for large marts | 100% (tables appropriate for seed-scale data) |
| SL01 | MetricFlow semantic models + metrics | 100% |

See [REFERENCE-IMPLEMENTATION.md](REFERENCE-IMPLEMENTATION.md) for details on
each rule's application.

## Key links

- [dap-dwh-spec](https://github.com/vicwik-gyg/dap-dwh-spec) — the standard
- [SLICE-SELECTION.md](SLICE-SELECTION.md) — why each model was chosen
- [REFERENCE-IMPLEMENTATION.md](REFERENCE-IMPLEMENTATION.md) — rule-by-rule report
- [HOW-TO-RUN.md](HOW-TO-RUN.md) — setup, run, test, teardown

## Safety

- **Testing catalog only** — `dbt_project.yml` is configured for testing schemas
- **Schema prefix** — all schemas start with `spec_compliant_` to avoid collisions
- **No production path** — if you see `production` in any config, stop and open a P0 task
- **Seed-based** — all source data comes from CSV seeds, no external dependencies

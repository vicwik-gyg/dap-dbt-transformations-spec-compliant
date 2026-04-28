# How to Run

## Prerequisites

- **dbt-core** >= 1.7.0
- **dbt-databricks** adapter
- **Databricks testing-catalog token** — stored as `DATABRICKS_TOKEN` env var
- **~/.dbt/profiles.yml** with the `dap_dbt_transformations` profile pointing to testing catalog

## Profile setup

Your `~/.dbt/profiles.yml` should have an entry like:

```yaml
dap_dbt_transformations:
  target: dev
  outputs:
    dev:
      type: databricks
      catalog: testing
      host: dbc-d10db17d-b6c4.cloud.databricks.com
      http_path: /sql/1.0/warehouses/92ba47e2f2dd7a60
      schema: dbt_default
      threads: 10
      token: "{{ env_var('DATABRICKS_TOKEN') }}"
```

**Never set `catalog: production` in this project's context.** The schemas are
prefixed with `spec_compliant_` to isolate from other dev work.

## Commands

### Install dependencies
```bash
dbt deps
# or
make deps
```

### Parse (validate project structure)
```bash
dbt parse
# or
make parse
```
Expected: exit code 0, no errors.

### Compile (generate SQL without executing)
```bash
dbt compile --target dev
# or
make compile
```
Expected: exit code 0, compiled SQL in `target/compiled/`.

### Seed sample data
```bash
dbt seed --target dev
# or
make seed
```
Expected: 7 seed tables created in `testing.spec_compliant_seeds`.

### Run models
```bash
dbt run --target dev
# or
make run  # (runs seed first automatically)
```
Expected: all ~25 models created across `spec_compliant_*` schemas.

### Run tests
```bash
dbt test --target dev
# or
make test
```
Expected: all tests pass (unique, not_null, accepted_values, business logic).

### Full pipeline
```bash
make all  # deps + seed + run + test
```

### Semantic layer queries (requires MetricFlow)
```bash
# List available metrics
dbt sl list metrics

# Query a metric
dbt sl query --metrics gross_bookings --group-by metric_time__day
dbt sl query --metrics cancellation_rate --group-by destination_name
```

## Teardown

To clean up testing-catalog schemas created by this project:

```bash
make clean-testing
```

This prints the SQL statements to run in the Databricks SQL editor. The schemas
all match `spec_compliant_*`, so there's no risk of affecting other dev work.

To clean local build artifacts:
```bash
make clean
```

## Troubleshooting

### "Permission denied" on Databricks
Ensure your `DATABRICKS_TOKEN` is valid and has access to the `testing` catalog.
Check with:
```bash
databricks sql-cli -e "SELECT current_catalog()"
```

### "Schema not found"
dbt creates schemas automatically on first run. If you see this on `dbt test`
before `dbt run`, run `make run` first.

### "Seed file too large"
All seeds are <100 rows by design. If you're hitting limits, ensure you're not
accidentally pointing at a different seed directory.

### "PII guard" errors
This project contains no PII — all seed data is synthetic. If you see PII-related
errors, check that your Databricks workspace doesn't have overly strict governance
policies on the testing catalog.

### stale compiled SQL
```bash
make clean && make all
```

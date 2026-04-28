# How to Run

## Prerequisites

- **Python** >= 3.12
- **uv** — Python package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **Databricks CLI** with OAuth login configured (see below)
- **~/.dbt/profiles.yml** with the `dap_dbt_transformations` profile (see below)

## One-time setup

### 1. Databricks OAuth (replaces PATs)

PATs are deprecated. Use OAuth U2M (user-to-machine) via the Databricks CLI:

```bash
databricks auth login \
  --host https://dbc-d10db17d-b6c4.cloud.databricks.com/ \
  --profile bridge
```

This opens a browser for OAuth consent. After login, verify:

```bash
databricks auth token --profile bridge
# Should print a JSON object with access_token
```

### 2. SSL certificate bundle

GYG's network proxy (Zscaler) intercepts TLS with a corporate CA. Python's bundled
certifi doesn't trust it. Export system certs once:

```bash
security find-certificate -a -p /Library/Keychains/System.keychain > .ca-bundle.pem
security find-certificate -a -p /System/Library/Keychains/SystemRootCertificates.keychain >> .ca-bundle.pem
```

The Makefile sets `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` automatically.

### 3. Python environment

```bash
uv sync
```

### 4. dbt profile

Your `~/.dbt/profiles.yml` should have:

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

The `DATABRICKS_TOKEN` env var is set automatically by the Makefile using the
OAuth bridge profile. You do NOT need to export it manually.

**Never set `catalog: production` in this project's context.**

## Commands

The Makefile handles OAuth token generation and SSL configuration. Use `make`:

### Install dependencies
```bash
make deps
```

### Seed sample data
```bash
make seed
```
Expected: 7 seed tables created in `testing.dbt_default`.

### Run models
```bash
make run  # (runs seed first automatically)
```
Expected: 21 models (11 tables, 10 views) created in `testing.dbt_default`.

### Run tests
```bash
make test
```
Expected: 59 tests pass (unique, not_null, accepted_values, business logic).

### Full pipeline
```bash
make all  # deps + seed + run + test
```

### Parse / Compile (no Databricks connection needed)
```bash
make parse
make compile
```

## Teardown

All objects land in `testing.dbt_default` schema. To clean up:

```sql
-- In Databricks SQL editor, drop tables/views prefixed with seed_, stg_, int_, dim_, fct_, agg_, metricflow_
-- Example:
DROP TABLE IF EXISTS testing.dbt_default.seed_bookings;
DROP VIEW IF EXISTS testing.dbt_default.stg_seed_data__bookings;
-- etc.
```

To clean local build artifacts:
```bash
make clean
```

## Troubleshooting

### "Invalid access token" / 403
Your OAuth token expired (1-hour lifetime). The Makefile refreshes it on every
invocation, but if running dbt directly you need:

```bash
export DATABRICKS_TOKEN=$(databricks auth token --profile bridge | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

If the bridge profile itself is expired, re-login:
```bash
databricks auth login --host https://dbc-d10db17d-b6c4.cloud.databricks.com/ --profile bridge
```

### SSL "self-signed certificate in certificate chain"
Regenerate the CA bundle:
```bash
security find-certificate -a -p /Library/Keychains/System.keychain > .ca-bundle.pem
security find-certificate -a -p /System/Library/Keychains/SystemRootCertificates.keychain >> .ca-bundle.pem
```

### "PERMISSION_DENIED: User does not have CREATE SCHEMA"
This is expected — the project routes all objects to `dbt_default` schema.
If you see this error, the `generate_schema_name` macro may have been reverted.

### "Schema not found" / TABLE_OR_VIEW_NOT_FOUND
Run `make seed` before `make run`. Seeds create the base tables that staging
models reference via `source()`.

### stale compiled SQL
```bash
make clean && make all
```

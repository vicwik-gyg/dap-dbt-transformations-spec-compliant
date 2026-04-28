.PHONY: deps parse compile run test seed clean-testing all token

# ─── Configuration ──────────────────────────────────────────
DBT_TARGET ?= dev
DBT_PROFILE ?= dap_dbt_transformations
REPO_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

# ─── Auth: OAuth via Databricks CLI bridge profile ──────────
# Generates a short-lived OAuth token from the 'bridge' profile.
# Requires: `databricks auth login --host https://dbc-d10db17d-b6c4.cloud.databricks.com/ --profile bridge`
export DATABRICKS_TOKEN := $(shell databricks auth token --profile bridge 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

# ─── SSL: Use system trust store (includes Zscaler CA) ──────
export SSL_CERT_FILE := $(REPO_DIR).ca-bundle.pem
export REQUESTS_CA_BUNDLE := $(REPO_DIR).ca-bundle.pem

# ─── Dependencies ───────────────────────────────────────────
deps:
	uv run dbt deps --target $(DBT_TARGET) --profile $(DBT_PROFILE)

# ─── Build pipeline ────────────────────────────────────────
seed:
	uv run dbt seed --target $(DBT_TARGET) --profile $(DBT_PROFILE)

parse:
	uv run dbt parse --target $(DBT_TARGET) --profile $(DBT_PROFILE)

compile:
	uv run dbt compile --target $(DBT_TARGET) --profile $(DBT_PROFILE)

run: seed
	uv run dbt run --target $(DBT_TARGET) --profile $(DBT_PROFILE)

test:
	uv run dbt test --target $(DBT_TARGET) --profile $(DBT_PROFILE)

# ─── Full pipeline ──────────────────────────────────────────
all: deps seed run test
	@echo "Full pipeline completed successfully."

# ─── Cleanup ────────────────────────────────────────────────
# Drops all schemas created by this project in the testing catalog.
# SAFETY: only drops schemas matching the spec_compliant_ prefix.
clean-testing:
	@echo "Dropping spec_compliant_* schemas from testing catalog..."
	@echo "Run the following SQL in Databricks SQL editor:"
	@echo ""
	@echo "  DROP SCHEMA IF EXISTS testing.spec_compliant_staging CASCADE;"
	@echo "  DROP SCHEMA IF EXISTS testing.spec_compliant_intermediate CASCADE;"
	@echo "  DROP SCHEMA IF EXISTS testing.spec_compliant_marts CASCADE;"
	@echo "  DROP SCHEMA IF EXISTS testing.spec_compliant_semantic CASCADE;"
	@echo "  DROP SCHEMA IF EXISTS testing.spec_compliant_seeds CASCADE;"
	@echo ""
	@echo "Or use the Databricks CLI:"
	@echo "  databricks sql-cli -e \"DROP SCHEMA IF EXISTS testing.spec_compliant_staging CASCADE;\""
	@echo "  databricks sql-cli -e \"DROP SCHEMA IF EXISTS testing.spec_compliant_intermediate CASCADE;\""
	@echo "  databricks sql-cli -e \"DROP SCHEMA IF EXISTS testing.spec_compliant_marts CASCADE;\""
	@echo "  databricks sql-cli -e \"DROP SCHEMA IF EXISTS testing.spec_compliant_semantic CASCADE;\""
	@echo "  databricks sql-cli -e \"DROP SCHEMA IF EXISTS testing.spec_compliant_seeds CASCADE;\""

clean:
	uv run dbt clean

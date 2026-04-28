.PHONY: deps parse compile run test seed clean-testing all

# ─── Configuration ──────────────────────────────────────────
DBT_TARGET ?= dev
DBT_PROFILE ?= dap_dbt_transformations

# ─── Dependencies ───────────────────────────────────────────
deps:
	dbt deps --target $(DBT_TARGET) --profile $(DBT_PROFILE)

# ─── Build pipeline ────────────────────────────────────────
seed:
	dbt seed --target $(DBT_TARGET) --profile $(DBT_PROFILE)

parse:
	dbt parse --target $(DBT_TARGET) --profile $(DBT_PROFILE)

compile:
	dbt compile --target $(DBT_TARGET) --profile $(DBT_PROFILE)

run: seed
	dbt run --target $(DBT_TARGET) --profile $(DBT_PROFILE)

test:
	dbt test --target $(DBT_TARGET) --profile $(DBT_PROFILE)

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
	dbt clean

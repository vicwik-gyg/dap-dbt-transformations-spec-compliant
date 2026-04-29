# shadow-spec-check

Deterministic CLI that programmatically verifies dbt spec conventions against
the project manifest. Produces a compliance matrix mechanically rather than by
hand.

## Quick Start

```bash
# Parse the project (generates target/manifest.json)
dbt parse

# Run all checks
python -m scripts.spec_check.cli all

# Check a single model
python -m scripts.spec_check.cli model fct_bookings

# List available rules
python -m scripts.spec_check.cli rules
```

## CLI Reference

```bash
# Human-readable table (default)
shadow-spec-check all

# JSON output for tooling
shadow-spec-check all --format json > matrix.json

# Markdown output for COMPLIANCE-AUTO.md
shadow-spec-check all --format markdown > docs/COMPLIANCE-AUTO.md

# Matrix view (model x rule grid)
shadow-spec-check all --format matrix

# Filter by rule
shadow-spec-check all --rule naming.table_prefix

# Filter by layer
shadow-spec-check all --layer staging

# Custom manifest path
shadow-spec-check --manifest path/to/manifest.json all
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks pass (or only N/A) |
| 1 | At least one DEVIATES finding |
| 2 | Tool error (manifest missing, rule crash) |

## Output Formats

- **human** — Readable table sorted by result (deviates first), with summary
- **json** — Array of `{model, rule, result, finding, spec_ref}` objects
- **markdown** — Full compliance report with summary, scorecard, and findings
- **matrix** — Model-vs-rule grid showing PASS/DEVIATES/-

## Rules

19 rules across 6 categories:

| Category | Rules |
|----------|-------|
| naming | `table_prefix`, `column_snake_case`, `source_style` |
| layering | `correct_layer` |
| archetype | `staging`, `fct_transaction`, `fct_periodic_snapshot`, `fct_accumulating_snapshot`, `dim_conformed`, `dim_scd_type_2`, `agg_mart`, `semantic_model` |
| tests | `not_null_on_pk`, `unique_on_pk`, `accepted_values_on_enums`, `relationships_on_fks` |
| docs | `model_description`, `column_description` |
| semantic | `marts_have_semantic_model` |

## Adding a New Rule

1. Choose the appropriate category file in `scripts/spec_check/rules/`.
2. Add a function decorated with `@rule`:

```python
from ..registry import rule
from ..models import Result, RuleResult

@rule(
    name="category.rule_name",
    description="What this rule checks",
    applies_to=["staging", "intermediate", "marts"],  # or ["all"]
    spec_ref="04-target-state/conventions.md#section",
)
def check_my_rule(node: dict, manifest: dict) -> RuleResult:
    model_name = node["name"]

    # Your check logic here
    if violation:
        return RuleResult(
            model=model_name,
            rule="category.rule_name",
            result=Result.DEVIATES,
            finding="Description of what's wrong",
            spec_ref="04-target-state/conventions.md#section",
        )

    return RuleResult(
        model=model_name,
        rule="category.rule_name",
        result=Result.PASS,
        spec_ref="04-target-state/conventions.md#section",
    )
```

3. If you created a new category file, import it in `scripts/spec_check/rules/__init__.py`.
4. Add a unit test in `tests/spec_check/test_<category>.py`.
5. Run `python -m pytest tests/spec_check/ -v` to verify.

## Rule Result Types

- **PASS** — Model complies with this rule
- **DEVIATES** — Model violates the spec (includes a `finding` description)
- **NA** — Rule doesn't apply to this model (e.g., staging rule on a marts model)

## Makefile Targets

```bash
make spec-check         # Run spec-check (parses first)
make compliance-report  # Regenerate docs/COMPLIANCE-AUTO.md
```

## CI Integration

The GitHub Actions workflow (`.github/workflows/spec-check.yml`) runs on every
PR. It:
1. Parses the dbt project
2. Runs `shadow-spec-check all`
3. Posts the compliance report as a PR comment
4. Fails the check if any deviations are found

## Architecture

```
scripts/spec_check/
├── __init__.py          # Package marker
├── cli.py              # CLI entrypoint (argparse)
├── manifest.py         # Manifest loader + node extractors
├── models.py           # RuleResult dataclass, Result enum
├── registry.py         # @rule decorator + rule registry
├── formatters/
│   ├── human.py        # Human-readable table
│   ├── json_fmt.py     # JSON array
│   ├── markdown.py     # COMPLIANCE-AUTO.md format
│   └── matrix.py       # Model x rule grid
└── rules/
    ├── naming.py       # Naming convention rules
    ├── layering.py     # Directory/layer rules
    ├── archetype.py    # Entity archetype rules
    ├── tests.py        # Testing convention rules
    ├── docs.py         # Documentation rules
    └── semantic.py     # Semantic layer rules
```

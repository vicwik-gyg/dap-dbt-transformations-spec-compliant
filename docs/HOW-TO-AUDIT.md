# How to Audit a Model

Run `shadow-spec-check` to programmatically verify whether a model complies with the [dap-dwh-spec](https://github.com/vicwik-gyg/dap-dwh-spec) conventions.

---

## Prerequisites

1. Python >= 3.12 and [uv](https://docs.astral.sh/uv/) installed
2. Clone this repo and run `uv sync`
3. Generate the manifest (no Databricks connection needed):
   ```bash
   make parse
   ```

---

## Audit a single model

```bash
python -m scripts.spec_check.cli model <model_name>
```

Example:

```bash
$ python -m scripts.spec_check.cli model fct_bookings

MODEL                  RULE                             RESULT     FINDING
---------------------------------------------------------------------------
fct_bookings           archetype.fct_transaction        PASS       -
fct_bookings           docs.model_description           PASS       -
fct_bookings           docs.column_description          PASS       -
fct_bookings           naming.table_prefix              PASS       -
fct_bookings           naming.column_snake_case         PASS       -
fct_bookings           tests.not_null_on_pk             PASS       -
fct_bookings           tests.unique_on_pk               PASS       -
fct_bookings           tests.relationships_on_fks       DEVIATES   FK column 'tour_id' missing relationships test
fct_bookings           tests.accepted_values_on_enums   DEVIATES   Enum column 'booking_status' missing accepted_values test

Summary: 7 PASS / 2 DEVIATES / 8 NA / 0 SUPPRESSED
```

---

## Audit all models

```bash
python -m scripts.spec_check.cli all
```

Or use the Makefile shortcut:

```bash
make spec-check
```

---

## Understanding the output

Each row is one **(model, rule)** pair. The result is one of:

| Result | Meaning | Action |
|--------|---------|--------|
| **PASS** | Model complies with this rule | None |
| **DEVIATES** | Model violates the spec | Fix the model or YAML (see finding text) |
| **N/A** | Rule does not apply to this model | None (e.g., a staging-only rule on a mart) |
| **SUPPRESSED** | Rule was explicitly opted-out via `meta.spec_check_suppress` | None — justification visible in report |

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | All applicable rules pass |
| 1 | At least one DEVIATES |
| 2 | Tool error (manifest missing, invalid rule name) |

---

## Regenerate the compliance report

The full markdown report lives at `docs/COMPLIANCE-AUTO.md`. To regenerate:

```bash
make compliance-report
```

This produces a compliance matrix (model × rule grid), summary statistics, findings list, and suppressions section.

---

## Output formats

```bash
# Human-readable table (default)
python -m scripts.spec_check.cli all

# Markdown (for docs/COMPLIANCE-AUTO.md)
python -m scripts.spec_check.cli all --format markdown

# JSON (for tooling / scripting)
python -m scripts.spec_check.cli all --format json

# Matrix grid (compact model × rule view)
python -m scripts.spec_check.cli all --format matrix
```

---

## Filter by rule or layer

```bash
# Only naming rules
python -m scripts.spec_check.cli all --rule naming

# Only a specific rule
python -m scripts.spec_check.cli all --rule tests.relationships_on_fks

# Only staging models
python -m scripts.spec_check.cli all --layer staging
```

---

## List available rules

```bash
python -m scripts.spec_check.cli rules
```

---

## Fixing a DEVIATES finding

1. Read the **finding** text — it tells you exactly what is wrong.
2. Look up the rule in [dap-dwh-spec conventions](https://github.com/vicwik-gyg/dap-dwh-spec/blob/main/04-target-state/conventions.md) for the full requirement.
3. Fix the model SQL or YAML schema file.
4. Re-run `make parse && python -m scripts.spec_check.cli model <model_name>`.
5. Repeat until all rules show PASS.

**Do not modify the spec-check rules to make a finding go away.** If a rule is genuinely inapplicable, use the suppression mechanism (see below).

---

## Suppressing a rule

If a rule is genuinely inapplicable (e.g., an enum column with unbounded values), suppress it in the model's YAML with a justification:

```yaml
columns:
  - name: tour_category
    description: Category of the tour.
    meta:
      spec_check_suppress:
        - rule: "tests.accepted_values_on_enums"
          justification: "Open-domain classification — unbounded set of values"
```

Model-level suppression (applies to all rules matching the name):

```yaml
models:
  - name: my_model
    config:
      meta:
        spec_check_suppress:
          - rule: "archetype.staging"
            justification: "Hybrid model — intentional deviation documented in ADR-042"
```

Suppressed rules appear in the report's **Suppressions** section — visible, not silent.

---

## CI integration

The GitHub Actions workflow (`.github/workflows/spec-check.yml`) runs on every PR:
1. Parses the dbt project
2. Runs spec-check
3. Posts the compliance report as a PR comment
4. Fails the check if any DEVIATES findings exist

---

## Further reading

- [docs/SPEC-CHECK.md](SPEC-CHECK.md) — CLI architecture and how to add new rules
- [dap-dwh-spec conventions](https://github.com/vicwik-gyg/dap-dwh-spec/blob/main/04-target-state/conventions.md) — the rules themselves

# Documentation Coverage Audit

**Date:** 2026-04-28
**Spec:** `dap-dwh-spec/02-mined-standards/documentation.md`
**Scope:** All 21 SQL models + semantic models + metrics + exposure

---

## Summary

| Criterion | Result |
|-----------|--------|
| Model descriptions present | 21/21 PASS |
| Column descriptions present | ~160/160 PASS (all columns documented) |
| Column description quality | MIXED — staging/int excellent, marts terse |
| Model-level meta.synonyms | 10/14 mart models have synonyms |
| Column-level meta.synonyms | 0 columns — DEVIATES |
| meta.semantic_type | Not present — DEVIATES |
| meta.sample_questions | Not present — DEVIATES |
| Metric documentation | 5/5 PASS (name, desc, label, type) |
| Source documentation | 7/7 sources documented |

**Material deviations: 0.** All models and columns have descriptions. Quality varies but nothing is undocumented.

---

## Model Description Coverage

| Layer | Models | All Have Description? | Quality |
|-------|--------|----------------------|---------|
| Staging | 7 | YES | Excellent — full paragraphs explaining purpose, rules referenced |
| Intermediate | 3 | YES | Excellent — explains transformation and downstream usage |
| Marts (fact) | 3 | YES | Good — concise but clear |
| Marts (agg) | 3 | YES | Good — identifies grain and purpose |
| Marts (dim) | 4 | YES | Good — identifies entity and usage |
| Semantic/Infra | 1 | YES | Adequate |
| **Total** | **21** | **21/21** | |

---

## Column Description Coverage

### Staging Layer — EXCELLENT

All 7 staging models have complete column-level descriptions. Every column documents:
- Business meaning (e.g., "Unique identifier for each booking transaction")
- Data type context (e.g., "in minor currency units (cents)")
- UTC specification on all timestamps
- FK relationships identified

**Quality grade: A**

### Intermediate Layer — EXCELLENT

All 3 intermediate models have complete column-level descriptions for all columns. Descriptions explain derivation logic where applicable (e.g., "GYG commission amount for this booking in cents").

**Quality grade: A**

### Marts — Fact Layer — ADEQUATE

Column descriptions present on all columns, but quality is mixed:

**fct_bookings:** Terse descriptions.
- Good: "Unique booking identifier", "Total price in cents"
- Gap: "Tour FK", "Customer FK" — lack business context (what does this relationship mean?)
- Gap: No calculation logic documented on derived columns

**fct_bookings_snapshot:** Similarly terse ("Booking ID", "Tour ID").

**fct_bookings_accumulating_snapshot:** Better — describes milestones with business meaning.

**Quality grade: B-** (present but below "rich documentation" standard for mart tables)

### Marts — Aggregate Layer — ADEQUATE

All 3 aggregate models have column descriptions, but very terse:
- "Total bookings", "Confirmed bookings", "Cancelled bookings"
- Missing: calculation logic, valid value ranges, caveats
- Spec requires: "business meaning, calculation logic, valid values, and caveats"

Example of what spec requires vs. what exists:
```yaml
# Current
- name: net_bookings_in_cents
  description: Net revenue in cents.

# Spec-compliant
- name: net_bookings_in_cents
  description: >
    Revenue from confirmed bookings only, in cents. Excludes cancelled
    bookings. Calculated as sum(total_price_in_cents) where is_cancelled = false.
    Always >= 0. Compare against gross_bookings_in_cents for cancellation impact.
```

**Quality grade: C+** (present but below standard)

### Marts — Dimension Layer — GOOD

Dimension models have adequate descriptions. Most columns explain their purpose clearly.

**Quality grade: B+**

---

## meta.synonyms Coverage

### Model-Level Synonyms

| Model | Has meta.synonyms? | Values |
|-------|-------------------|--------|
| fct_bookings | YES | booking, order, transaction |
| fct_bookings_snapshot | YES | booking_snapshot |
| fct_bookings_accumulating_snapshot | YES | booking_lifecycle |
| agg_bookings_checkout_daily | YES | daily_bookings |
| agg_bookings_destination_daily | YES | destination_daily |
| agg_bookings_tour_category_monthly | YES | category_monthly |
| dim_destinations | YES | location, city, market |
| dim_tours | YES | activity, experience, product |
| dim_suppliers_history | YES | supplier, partner, vendor |
| dim_care_tickets | YES | support_ticket, care_case |
| All staging models | NO | — |
| All intermediate models | NO | — |

**Assessment:** Model-level synonyms are present on all consumer-facing models (marts). Staging and intermediate models correctly omit them (not exposed to end users).

### Column-Level Synonyms

**No columns in the project have `meta.synonyms` defined.**

- **Spec requires:** "`meta.synonyms` is required for any column exposed in Looker — enables AI prompt matching."
- **Assessment:** This is a gap for AI-discoverability. Important for Looker-exposed columns like `total_price_in_cents` (users might search for "revenue", "GMV", "price").

**Materiality: NON-MATERIAL** for gate decision. The models work correctly without column synonyms. This is an AI-enablement concern, not a correctness issue.

---

## AI-Assist Meta Fields

| Field | Present? | Spec Status |
|-------|----------|-------------|
| meta.synonyms (model) | YES (marts) | Required |
| meta.synonyms (column) | NO | Required |
| meta.semantic_type | NO | Encouraged |
| meta.sample_questions | NO | Encouraged |

**Assessment:** The "encouraged" fields (`semantic_type`, `sample_questions`) are aspirational. Column-level synonyms are the key gap.

---

## Metric Documentation

| Metric | name | description | label | type |
|--------|------|-------------|-------|------|
| gross_bookings | YES | YES | YES | YES |
| net_bookings | YES | YES | YES | YES |
| booking_count | YES | YES | YES | YES |
| cancelled_bookings_metric | YES | YES | YES | YES |
| cancellation_rate | YES | YES | YES | YES |

**All 5 metrics are fully documented per spec. PASS.**

---

## Source Documentation

All 7 source tables in `_sources__seeds.yml` have:
- Table-level description
- Key column descriptions (not exhaustive, but primary and important columns)

**PASS** — meets the "define raw data as sources" requirement.

---

## YAML Organisation

| Requirement | Compliance |
|-------------|-----------|
| One _<dir>__models.yml per directory | PASS — 7 YAML files across 7 directories |
| Leading underscores | PASS — all start with `_` |
| Directory name in filename | PASS — e.g., `_booking_fact__models.yml` |
| _<dir>__docs.md blocks | NOT PRESENT — no docs blocks |

**Finding: No `_<dir>__docs.md` files exist.**

The spec says "One `_<directory>__docs.md` per directory for documentation blocks." These are optional doc blocks for long-form descriptions that don't fit in YAML. All descriptions are inline in YAML which works fine for the current description lengths.

**Materiality: NON-MATERIAL.** Docs blocks are optional supplementary documentation.

---

## Findings Detail

### Finding 1: Mart column descriptions lack depth (NON-MATERIAL)

**Spec:** "Every column must document its business meaning, calculation logic, valid values, and caveats."
**Actual:** Mart columns have 1-5 word descriptions (functional but not rich).
**Impact:** Reduced self-service discoverability. Analysts need tribal knowledge to understand nuances.
**Remediation:** Expand descriptions on mart columns to include calculation logic and valid ranges. Priority: aggregate models (AI-queryable), then fact models.

### Finding 2: No column-level meta.synonyms (NON-MATERIAL)

**Spec:** "`meta.synonyms` is required for any column exposed in Looker."
**Actual:** No column has meta.synonyms.
**Impact:** AI agents (Langdock, Looker AI) cannot match user questions to column names when users use alternative terminology.
**Remediation:** Add synonyms to key mart columns:
```yaml
- name: total_price_in_cents
  meta:
    synonyms: [revenue, gmv, price, booking_value]
- name: commission_in_cents
  meta:
    synonyms: [take_rate, fee, margin]
```

### Finding 3: No meta.semantic_type or meta.sample_questions (NON-MATERIAL)

**Spec:** "Strongly encouraged for AI discovery."
**Actual:** Not present.
**Impact:** Nice-to-have for AI discoverability. Lower priority than synonyms.
**Remediation:** Optional — add when column synonyms are complete.

---

## Gate Decision

**0 material deviations.** All models and columns are documented. Quality improvements are recommended for mart layers but not blocking.

---

## Recommendations for Remediation Task (1.7)

Priority order:
1. Expand aggregate model column descriptions (calculation logic, valid ranges)
2. Add column-level meta.synonyms to mart models
3. Expand fact model column descriptions beyond terse labels
4. (Future) Add meta.semantic_type and meta.sample_questions

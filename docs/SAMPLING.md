# Seed Sampling — Source Mapping & Policy

**Date:** 2026-04-28
**Purpose:** Document the mapping from shadow repo seeds to production source tables, plus the PII scrubbing policy and sampling methodology.

---

## Source Mapping

| Seed File | Production Source Table | PK Column | Actual Rows |
|-----------|----------------------|-----------|-------------|
| seed_destinations.csv | `production.db_mirror_dbz.catalog__location` (type='city') | id → destination_id | 1,144 |
| seed_suppliers.csv | `production.db_mirror_dbz.catalog__supplier` (via tour FK) | id → supplier_id | 1,137 |
| seed_supplier_history.csv | `production.db_mirror_dbz.catalog__supplier_history` | id → supplier_id | 6,679 |
| seed_tours.csv | `production.db_mirror_dbz.catalog__tour` | id → tour_id | 1,031 |
| seed_bookings.csv | `production.db_mirror_dbz.gyg__booking` (via tour_option) | booking_id | 1,033 |
| seed_booking_status_history.csv | `production.db_mirror_dbz.gyg__booking_history` | booking_id | 8,977 |
| seed_care_tickets.csv | `production.care.fact_care_ticket` | ticket_id | 92 |

### Column Mapping Notes

**seed_destinations → catalog__location:**
- destination_id → id
- destination_name → name (full "City, Country" format)
- destination_city → parsed from name (before ", ")
- destination_country → parsed from name (after ", ")
- destination_continent → derived from country via static CASE mapping
- is_active → status = 'active'
- created_at → update_timestamp
- updated_at → update_timestamp

**seed_suppliers → catalog__supplier (joined via catalog__tour for location):**
- supplier_id → id
- supplier_name → name
- supplier_email → REDACTED (`supplier_<id>@redacted.example`)
- destination_id → catalog__tour.primary_location_id
- is_verified → verification_status = 'verified'
- is_active → gyg_status = 'active'
- created_at → update_timestamp
- updated_at → update_timestamp

**seed_supplier_history → catalog__supplier_history:**
- supplier_id → id
- supplier_name → name
- supplier_email → REDACTED (same pattern)
- destination_id → NULL (not available in history table)
- is_verified → verification_status = 'verified'
- is_active → gyg_status = 'active'
- valid_from → binlog_timestamp
- valid_to → computed from next row's binlog_timestamp (or '9999-12-31 23:59:59')
- operation → operation

**seed_tours → catalog__tour + catalog__tour_text + catalog__tour_option:**
- tour_id → id
- tour_name → catalog__tour_text.title (language_id=29, English)
- supplier_id → supplier_id
- destination_id → primary_location_id
- tour_category → category
- price_in_cents → commission_rate * 100
- currency_code → 'EUR'
- duration_minutes → MIN(catalog__tour_option.duration)
- is_active → gyg_status = 'active' AND online = true
- created_at → creation_timestamp
- updated_at → update_timestamp

**seed_bookings → gyg__booking (joined via catalog__tour_option):**
- booking_id → booking_id
- tour_id → catalog__tour_option.tour_id (from booking.tour_option_id)
- customer_id → abs(hash(customer_id_anon)) % 2147483647
- supplier_id → supplier_id
- destination_id → catalog__tour.primary_location_id
- booking_status → status
- number_of_participants → total_number_of_participants
- total_price_in_cents → customer_total_price * 100
- currency_code → 'EUR'
- commission_rate → commission_rate
- checkout_at → creation_timestamp
- travel_at → tour_start_datetime
- created_at → creation_timestamp
- cancelled_at → date_of_cancelation

**seed_booking_status_history → gyg__booking_history:**
- booking_id → booking_id
- booking_status → status
- changed_at → update_timestamp
- changed_by → update_user_type

**seed_care_tickets → care.fact_care_ticket:**
- ticket_id → ticket_id
- booking_id → booking_id
- customer_id → abs(hash(booking_id)) % 2147483647
- ticket_category → contact_reason_id (COALESCE → 'general_inquiry')
- ticket_priority → ticket_priority (COALESCE → 'medium')
- ticket_status → status
- created_at → date_of_creation
- first_response_at → NULL (not derivable)
- resolved_at → date_of_update WHERE status IN ('solved', 'closed')

---

## Sampling Methodology

### Deterministic Hash Sampling

```sql
WHERE abs(hash(cast(<pk_column> as string))) % <modulo> < 1
```

Modulo values calibrated from source cardinalities:

| Seed | Source Cardinality | Modulo | Yield |
|------|-------------------|--------|-------|
| destinations | ~30K cities | 30 | 1,144 |
| suppliers | ~7.4K (FK-filtered) | 7 | 1,137 |
| tours | ~27K (FK-filtered) | 27 | 1,031 |
| bookings | ~100K+ (FK-filtered) | 100 | 1,033 |

History and care ticket tables pull ALL rows matching sampled entity IDs (no hash filter).

### Referential Integrity Preservation

Sampling order ensures FK consistency:
1. **Destinations** — city-type locations, hash-sampled
2. **Suppliers** — those with tours in sampled destinations (via catalog__tour.primary_location_id)
3. **Supplier history** — all SCD2 versions for sampled suppliers
4. **Tours** — those belonging to sampled suppliers, hash-sampled
5. **Bookings** — those with tour_option.tour_id in sampled tours, hash-sampled
6. **Booking status history** — all events for sampled bookings
7. **Care tickets** — all tickets for sampled bookings (FK-constrained)

### Idempotency

- Deterministic hash function → same rows every time
- No TABLESAMPLE, no random sampling
- Output CSV sorted by PK
- Timestamps preserved as-is from source (ISO 8601 with timezone)

---

## PII Scrubbing Policy

### Redacted Columns

| Seed Column | Source Column | Method | Reason |
|-------------|-------------|--------|--------|
| supplier_email | catalog__supplier.email | `supplier_<id>@redacted.example` | Personal contact info |

### Hashed Columns

| Seed Column | Source | Method | Reason |
|-------------|--------|--------|--------|
| customer_id (bookings) | customer_id_anon | abs(hash(value)) % 2^31 | Pseudonymized, joinable |
| customer_id (care) | booking_id | abs(hash(value)) % 2^31 | Consistent tokenization |

### Dropped Columns (excluded from queries)

| Source Column | Table | Reason |
|--------------|-------|--------|
| email (raw) | catalog__supplier | Replaced with redacted placeholder |
| phone_number | catalog__supplier | Personal contact info |
| customer_comment | gyg__booking_history | Free-text customer content |
| supplier_contact | care.fact_care_ticket | Contact details |
| tour_title | care.fact_care_ticket | May contain PII |
| visitor_id | care.fact_care_ticket | Customer tracking ID |
| booking_reference | care.fact_care_ticket | Sensitive reference |

### Kept As-Is

- All non-PII IDs (booking_id, tour_id, supplier_id, destination_id, ticket_id)
- Supplier/tour names (business entity names, public product names)
- Categorical dimensions (status, category, priority, country)
- Numeric measures (prices, counts, rates)
- Timestamps
- Boolean flags

---

## Regeneration

```bash
cd dap-dbt-transformations-spec-compliant
uv run python scripts/sample_from_prod.py
```

### Prerequisites

- Databricks CLI with `bridge` profile (OAuth)
- `DATABRICKS_HOST_BRIDGE_WORKSPACE` and `DATABRICKS_WAREHOUSE_ID` in maestro `.env`
- Python 3.12+ with `pyyaml` and `requests`

### Options

```bash
uv run python scripts/sample_from_prod.py --dry-run     # Show queries only
uv run python scripts/sample_from_prod.py --seed <name> # Single seed + deps
```

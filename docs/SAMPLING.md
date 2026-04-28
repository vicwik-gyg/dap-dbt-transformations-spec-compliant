# Seed Sampling — Source Mapping & Policy

**Date:** 2026-04-28
**Purpose:** Document the mapping from shadow repo seeds to production source tables, plus the PII scrubbing policy and sampling methodology.

---

## Source Mapping

| Seed File | Production Source Table | PK Column | Est. Source Rows | Sample Size |
|-----------|----------------------|-----------|-----------------|-------------|
| seed_bookings.csv | `production.db_mirror_dbz.gyg__booking` | booking_id | ~50M | 1,000 |
| seed_booking_status_history.csv | `production.db_mirror_dbz.gyg__booking_history` | (booking_id, binlog_timestamp) | ~100M | 1,000 (per sampled booking) |
| seed_care_tickets.csv | `production.care.fact_care_ticket` | ticket_id | ~5M | 1,000 |
| seed_destinations.csv | `production.db_mirror_dbz.catalog__location` | id (→ destination_id) | ~30K | 1,000 |
| seed_supplier_history.csv | `production.db_mirror_dbz.catalog__supplier_history` | (supplier_id, binlog_timestamp) | ~1.6M | 1,000 (per sampled supplier) |
| seed_suppliers.csv | `production.db_mirror_dbz.catalog__supplier` | supplier_id | ~377K | 1,000 |
| seed_tours.csv | `production.db_mirror_dbz.catalog__tour` | tour_id | ~200K | 1,000 |

### Column Mapping Notes

**seed_bookings → gyg__booking:**
- booking_id → booking_id
- tour_id → tour_option_id (mapped via tour_option → tour)
- customer_id → customer_id_anon (hashed in source)
- supplier_id → supplier_id
- destination_id → derived via tour → location join
- booking_status → status
- number_of_participants → total_number_of_participants
- total_price_in_cents → customer_total_price × 100 (source is decimal EUR)
- currency_code → derived from customer_currency_id
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
- customer_id → requester_id (hashed)
- ticket_category → contact_reason_id (mapped to category label)
- ticket_priority → ticket_priority
- ticket_status → status
- created_at → date_of_creation
- first_response_at → derived from care metrics
- resolved_at → derived from status history

**seed_destinations → catalog__location:**
- destination_id → id
- destination_name → name (from location_text or location_details)
- destination_city → city (from location_details)
- destination_country → country (from location_relationship → parent)
- destination_continent → continent (from location hierarchy)
- is_active → is_active / status
- created_at → creation_timestamp
- updated_at → update_timestamp

**seed_supplier_history → catalog__supplier_history:**
- supplier_id → supplier_id
- supplier_name → name
- supplier_email → DROPPED (PII)
- destination_id → location_id
- is_verified → is_verified
- is_active → is_active
- valid_from → binlog_timestamp (row start)
- valid_to → next row's binlog_timestamp or '9999-12-31'
- operation → operation

**seed_suppliers → catalog__supplier:**
- supplier_id → supplier_id
- supplier_name → name
- supplier_email → DROPPED (PII)
- destination_id → location_id
- is_verified → is_verified
- is_active → is_active
- created_at → creation_timestamp
- updated_at → update_timestamp

**seed_tours → catalog__tour:**
- tour_id → tour_id
- tour_name → derived from catalog__tour_text (title)
- supplier_id → supplier_id
- destination_id → derived from catalog__tour_to_location
- tour_category → derived from catalog__tour_to_category
- price_in_cents → derived from pricing tables × 100
- currency_code → derived from pricing currency
- duration_minutes → duration
- is_active → status = 'active'
- created_at → creation_timestamp
- updated_at → update_timestamp

---

## Sampling Methodology

### Deterministic Hash Sampling

Uses stable hash-based sampling to ensure reproducibility:

```sql
WHERE abs(hash(cast(<pk_column> as string))) % <modulo> < <target>
```

The modulo is calculated from source cardinality to yield approximately 1,000 rows:
- `modulo = source_row_count / 1000` (rounded to nearest power of 10 for stability)

### Referential Integrity Preservation

Sampling order ensures FK consistency:
1. **Destinations** sampled first (smallest, reference table)
2. **Suppliers** sampled from those linked to sampled destinations
3. **Tours** sampled from those linked to sampled suppliers + destinations
4. **Bookings** sampled from those referencing sampled tours
5. **Booking status history** pulled for all sampled bookings (complete lifecycle)
6. **Supplier history** pulled for all sampled suppliers (complete SCD2 chain)
7. **Care tickets** sampled from those linked to sampled bookings

This cascade ensures all FK relationships in the sampled data are valid.

### Idempotency

- Same hash seed → same rows every time
- No random sampling, no TABLESAMPLE
- Output CSV sorted by PK for byte-identical reproducibility
- Timestamps formatted consistently (ISO 8601, UTC)

---

## PII Scrubbing Policy

### Dropped Columns (not included in seeds)

| Source Column | Table | Reason |
|--------------|-------|--------|
| supplier_email | catalog__supplier, catalog__supplier_history | Personal contact information |
| customer_comment | gyg__booking_history | Free-text customer content |
| billing_details | gyg__booking_history | Payment information |
| modification_log | gyg__booking_history | May contain customer details |
| customer_address_id_anon | gyg__booking | Even anonymized, not needed |
| supplier_contact | care.fact_care_ticket | Supplier contact details |
| tour_title | care.fact_care_ticket | May contain location-specific PII |
| raw_subject | care.stg_ticket | Free-text subject line |
| recipient | care.stg_ticket | Email address |
| tags | care.fact_care_ticket | May contain customer identifiers |

### Hashed Columns (deterministic tokenization)

| Source Column | Hashing Method | Reason |
|--------------|---------------|--------|
| customer_id | sha256(salt + id) → bigint | Pseudonymized but joinable within sample |
| requester_id (care) | sha256(salt + id) → bigint | Same customer pseudonymization |
| visitor_id | DROPPED | Not needed for shadow repo scope |

### Kept As-Is

- All non-PII IDs (booking_id, tour_id, supplier_id, destination_id, ticket_id)
- Categorical dimensions (status, category, priority, country, etc.)
- Numeric measures (prices, counts, rates)
- Timestamps (creation, update, travel dates)
- Boolean flags (is_active, is_verified, etc.)

### Salt Management

The hashing salt is stored in `scripts/.sampling-salt` (gitignored). It must be consistent across all seeds for FK integrity on customer_id.

---

## Regeneration

To regenerate seeds from production:

```bash
cd /path/to/dap-dbt-transformations-spec-compliant
uv run python scripts/sample_from_prod.py
```

This will:
1. Connect to Databricks via OAuth (`databricks auth token --profile bridge`)
2. Execute sampling queries per `scripts/sampling-config.yaml`
3. Apply PII scrubbing
4. Write CSVs to `seeds/`
5. Report row counts and FK integrity check results

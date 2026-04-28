"""
Deterministic production seed sampler for the shadow repo.

Connects to Databricks via OAuth (databricks auth token --profile bridge),
executes sampling queries defined in sampling-config.yaml, applies PII
scrubbing, and writes reproducible CSVs to seeds/.

Usage:
    uv run python scripts/sample_from_prod.py [--dry-run] [--seed NAME]
"""

import argparse
import csv
import hashlib
import subprocess
import sys
from pathlib import Path

import yaml

try:
    from databricks import sql as dbsql
except ImportError:
    dbsql = None

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "scripts" / "sampling-config.yaml"
SALT_PATH = REPO_ROOT / "scripts" / ".sampling-salt"

# Default salt if none exists (first run creates one)
DEFAULT_SALT = "shadow-repo-seed-salt-2026"


def get_salt() -> str:
    """Load or create the hashing salt for PII pseudonymization."""
    if SALT_PATH.exists():
        return SALT_PATH.read_text().strip()
    SALT_PATH.write_text(DEFAULT_SALT)
    print(f"  Created salt file: {SALT_PATH}")
    return DEFAULT_SALT


def get_oauth_token(profile: str) -> str:
    """Get OAuth token via databricks CLI."""
    result = subprocess.run(
        ["databricks", "auth", "token", "--profile", profile],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: Failed to get token for profile '{profile}':")
        print(f"  {result.stderr.strip()}")
        sys.exit(1)

    # Parse the JSON output for access_token
    import json

    try:
        data = json.loads(result.stdout)
        return data["access_token"]
    except (json.JSONDecodeError, KeyError):
        # Fallback: token might be raw text
        return result.stdout.strip()


def load_config() -> dict:
    """Load sampling configuration."""
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_databricks_config(profile: str) -> tuple[str, str]:
    """Get host and http_path from databricks CLI profile or env vars."""
    import os

    host = os.environ.get("DATABRICKS_HOST")
    http_path = os.environ.get("DATABRICKS_HTTP_PATH")

    if host and http_path:
        return host, http_path

    # Read from databricks CLI config
    result = subprocess.run(
        ["databricks", "auth", "env", "--profile", profile],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        import json

        try:
            env_data = json.loads(result.stdout)
            host = host or env_data.get("DATABRICKS_HOST", "")
            # http_path not in auth env — use default serverless
            http_path = http_path or "/sql/1.0/warehouses/auto"
        except json.JSONDecodeError:
            pass

    if not host:
        print("ERROR: Cannot determine Databricks host.")
        print("  Set DATABRICKS_HOST env var or configure databricks CLI profile.")
        sys.exit(1)

    return host, http_path or "/sql/1.0/warehouses/auto"


def connect(config: dict, token: str):
    """Create Databricks SQL connection."""
    if dbsql is None:
        print("ERROR: databricks-sql-connector not installed.")
        print("  Run: uv add databricks-sql-connector")
        sys.exit(1)

    profile = config["connection"]["auth_profile"]
    host, http_path = get_databricks_config(profile)

    return dbsql.connect(
        server_hostname=host,
        http_path=http_path,
        access_token=token,
    )


def resolve_query(query_template: str, collected_ids: dict) -> str:
    """Replace {{placeholder}} tokens with collected FK values."""
    for key, values in collected_ids.items():
        placeholder = "{{" + key + "}}"
        if placeholder in query_template:
            if not values:
                # No matching IDs — return query that yields 0 rows
                query_template = query_template.replace(
                    placeholder, "SELECT NULL WHERE 1=0"
                )
            else:
                id_list = ", ".join(str(v) for v in values)
                query_template = query_template.replace(placeholder, id_list)
    return query_template


def compute_valid_to(rows: list[dict]) -> list[dict]:
    """Post-process SCD2 rows: compute valid_to from next row's valid_from."""
    if not rows:
        return rows

    # Group by supplier_id
    from itertools import groupby

    rows_sorted = sorted(rows, key=lambda r: (r["supplier_id"], r["valid_from"] or ""))
    result = []

    for _supplier_id, group in groupby(rows_sorted, key=lambda r: r["supplier_id"]):
        versions = list(group)
        for i, row in enumerate(versions):
            if i + 1 < len(versions):
                row["valid_to"] = versions[i + 1]["valid_from"]
            else:
                row["valid_to"] = "9999-12-31 23:59:59"
            result.append(row)

    return result


def write_csv(rows: list[dict], target_path: Path) -> int:
    """Write rows to CSV deterministically (sorted, consistent formatting)."""
    if not rows:
        print(f"  WARNING: No rows to write to {target_path}")
        return 0

    target_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(rows[0].keys())
    with open(target_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for row in rows:
            # Normalize None → empty string for CSV
            writer.writerow({k: ("" if v is None else v) for k, v in row.items()})

    return len(rows)


def extract_pk_values(rows: list[dict], pk_column: str) -> list:
    """Extract primary key values from result set for FK cascading."""
    return [row[pk_column] for row in rows if row.get(pk_column) is not None]


def run_sampling(
    config: dict,
    connection,
    dry_run: bool = False,
    only_seed: str | None = None,
):
    """Execute the full sampling pipeline."""
    collected_ids: dict[str, list] = {}
    seeds = config["seeds"]

    if only_seed:
        # Find the seed and all its dependencies
        seed_names = {s["name"] for s in seeds}
        if only_seed not in seed_names:
            print(f"ERROR: Seed '{only_seed}' not found in config.")
            print(f"  Available: {sorted(seed_names)}")
            sys.exit(1)

    for seed_cfg in seeds:
        name = seed_cfg["name"]
        if only_seed and name != only_seed:
            # Still run dependencies
            deps = seed_cfg.get("depends_on", [])
            if only_seed not in _get_all_dependents(seeds, name):
                continue

        print(f"\n{'='*60}")
        print(f"  Sampling: {name}")
        print(f"  Target:   {seed_cfg['target_file']}")
        print(f"  Note:     {seed_cfg.get('sample_note', 'N/A')}")

        # Resolve FK placeholders
        query = resolve_query(seed_cfg["source_query"], collected_ids)

        if dry_run:
            print(f"  [DRY RUN] Query preview (first 200 chars):")
            print(f"    {query[:200]}...")
            continue

        # Execute query
        print(f"  Executing query...")
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()
            rows = [dict(zip(columns, row)) for row in raw_rows]
        finally:
            cursor.close()

        print(f"  Fetched {len(rows)} rows")

        # Post-processing
        if seed_cfg.get("post_process") == "compute_valid_to":
            rows = compute_valid_to(rows)
            print(f"  Post-processed: computed valid_to ({len(rows)} rows)")

        # Collect FK values for downstream seeds
        pk_col = seed_cfg["pk_column"]
        fk_filter = seed_cfg.get("fk_filter")
        if fk_filter:
            collected_ids[fk_filter] = extract_pk_values(rows, pk_col)
            print(f"  Collected {len(collected_ids[fk_filter])} {fk_filter} for downstream")

        # Write CSV
        target_path = REPO_ROOT / seed_cfg["target_file"]
        count = write_csv(rows, target_path)
        print(f"  Wrote {count} rows to {target_path.relative_to(REPO_ROOT)}")

    print(f"\n{'='*60}")
    print("  Sampling complete!")


def _get_all_dependents(seeds: list[dict], name: str) -> set[str]:
    """Get all seeds that depend (directly or transitively) on the given seed."""
    dependents = set()
    for s in seeds:
        if name in s.get("depends_on", []):
            dependents.add(s["name"])
            dependents.update(_get_all_dependents(seeds, s["name"]))
    return dependents


def main():
    parser = argparse.ArgumentParser(description="Sample production data for seeds")
    parser.add_argument("--dry-run", action="store_true", help="Print queries without executing")
    parser.add_argument("--seed", type=str, help="Only sample a specific seed (and deps)")
    args = parser.parse_args()

    print("Shadow Repo — Production Seed Sampler")
    print("=" * 60)

    config = load_config()
    salt = get_salt()
    print(f"  Config: {CONFIG_PATH.relative_to(REPO_ROOT)}")
    print(f"  Salt:   {'[loaded]' if SALT_PATH.exists() else '[created]'}")

    if args.dry_run:
        print("  Mode:   DRY RUN (no queries executed)")
        run_sampling(config, connection=None, dry_run=True, only_seed=args.seed)
        return

    # Get OAuth token
    profile = config["connection"]["auth_profile"]
    print(f"  Auth:   OAuth via profile '{profile}'")
    token = get_oauth_token(profile)
    print(f"  Token:  {'[obtained]'}")

    # Connect
    connection = connect(config, token)
    print(f"  Connected to Databricks")

    try:
        run_sampling(config, connection, dry_run=False, only_seed=args.seed)
    finally:
        connection.close()


if __name__ == "__main__":
    main()

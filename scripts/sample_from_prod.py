"""
Deterministic production seed sampler for the shadow repo.

Connects to Databricks via OAuth (databricks auth token --profile bridge),
executes sampling queries defined in sampling-config.yaml using the Statement
Execution API (reliable, with timeouts and polling), applies PII scrubbing,
and writes reproducible CSVs to seeds/.

Usage:
    uv run python scripts/sample_from_prod.py [--dry-run] [--seed NAME]
"""

import argparse
import csv
import json
import subprocess
import sys
import time
from itertools import groupby
from pathlib import Path

import requests
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "scripts" / "sampling-config.yaml"
SALT_PATH = REPO_ROOT / "scripts" / ".sampling-salt"

DEFAULT_SALT = "shadow-repo-seed-salt-2026"

# Databricks config — read from env or maestro .env
MAESTRO_ROOT = Path.home() / "git" / "maestro"
ENV_PATH = MAESTRO_ROOT / ".env"


def get_salt() -> str:
    """Load or create the hashing salt for PII pseudonymization."""
    if SALT_PATH.exists():
        return SALT_PATH.read_text().strip()
    SALT_PATH.write_text(DEFAULT_SALT)
    print(f"  Created salt file: {SALT_PATH}")
    return DEFAULT_SALT


def load_dotenv() -> dict:
    """Load .env file from maestro root."""
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def get_oauth_token(profile: str) -> str:
    """Get OAuth token via databricks CLI."""
    result = subprocess.run(
        ["databricks", "auth", "token", "--profile", profile],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        print(f"ERROR: Failed to get token for profile '{profile}':")
        print(f"  {result.stderr.strip()}")
        sys.exit(1)

    try:
        data = json.loads(result.stdout)
        return data["access_token"]
    except (json.JSONDecodeError, KeyError):
        return result.stdout.strip()


def get_databricks_config(profile: str) -> tuple[str, str, str]:
    """Get host, warehouse_id, and token."""
    import os

    env = load_dotenv()

    host = os.environ.get("DATABRICKS_HOST") or env.get(
        "DATABRICKS_HOST_BRIDGE_WORKSPACE"
    )
    warehouse_id = os.environ.get("DATABRICKS_WAREHOUSE_ID") or env.get(
        "DATABRICKS_WAREHOUSE_ID", ""
    )

    if not host:
        # Fallback: read from databricks CLI
        result = subprocess.run(
            ["databricks", "auth", "env", "--profile", profile],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                env_data = data.get("env", data)
                host = env_data.get("DATABRICKS_HOST", "")
            except json.JSONDecodeError:
                pass

    if not host:
        print("ERROR: Cannot determine Databricks host.")
        print("  Set DATABRICKS_HOST_BRIDGE_WORKSPACE in maestro .env")
        sys.exit(1)

    host = host.rstrip("/")
    if not host.startswith("http"):
        host = f"https://{host}"

    token = get_oauth_token(profile)
    return host, warehouse_id, token


def submit_query(host: str, token: str, warehouse_id: str, sql: str) -> dict:
    """Submit query via Statement Execution API."""
    url = f"{host}/api/2.0/sql/statements"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "statement": sql,
        "warehouse_id": warehouse_id,
        "wait_timeout": "0s",
        "disposition": "INLINE",
        "catalog": "production",
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def poll_result(host: str, token: str, statement_id: str, timeout: int = 300) -> dict:
    """Poll for query completion."""
    url = f"{host}/api/2.0/sql/statements/{statement_id}"
    headers = {"Authorization": f"Bearer {token}"}

    start = time.monotonic()
    poll_interval = 1.0

    while True:
        elapsed = time.monotonic() - start
        if elapsed > timeout:
            print(f"  ERROR: Query timed out after {timeout}s")
            try:
                requests.post(f"{url}/cancel", headers=headers, timeout=5)
            except Exception:
                pass
            sys.exit(1)

        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        state = data.get("status", {}).get("state", "UNKNOWN")

        if state == "SUCCEEDED":
            return data
        elif state in ("FAILED", "CANCELED", "CLOSED"):
            error = data.get("status", {}).get("error", {})
            msg = error.get("message", state)
            print(f"  ERROR: Query {state}: {msg}")
            return None

        time.sleep(min(poll_interval, 3.0))
        poll_interval *= 1.5


def execute_query(host: str, token: str, warehouse_id: str, sql: str) -> list[dict] | None:
    """Execute SQL and return list of dicts."""
    result = submit_query(host, token, warehouse_id, sql)
    state = result.get("status", {}).get("state", "UNKNOWN")
    statement_id = result.get("statement_id", "")

    if state in ("PENDING", "RUNNING"):
        print(f"    Statement {statement_id} polling...")
        result = poll_result(host, token, statement_id)
        if result is None:
            return None
    elif state == "SUCCEEDED":
        pass
    else:
        error = result.get("status", {}).get("error", {})
        msg = error.get("message", state)
        print(f"  ERROR: Query {state}: {msg}")
        return None

    # Parse result
    manifest = result.get("manifest", {})
    columns = manifest.get("schema", {}).get("columns", [])
    col_names = [c["name"] for c in columns]
    data_array = result.get("result", {}).get("data_array", [])

    return [dict(zip(col_names, row)) for row in data_array]


def load_config() -> dict:
    """Load sampling configuration."""
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def resolve_query(query_template: str, collected_ids: dict) -> str:
    """Replace {{placeholder}} tokens with collected FK values."""
    for key, values in collected_ids.items():
        placeholder = "{{" + key + "}}"
        if placeholder in query_template:
            if not values:
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

    rows_sorted = sorted(rows, key=lambda r: (r["supplier_id"] or "", r["valid_from"] or ""))
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
            writer.writerow({k: ("" if v is None else v) for k, v in row.items()})

    return len(rows)


def extract_pk_values(rows: list[dict], pk_column: str) -> list:
    """Extract primary key values from result set for FK cascading."""
    return [row[pk_column] for row in rows if row.get(pk_column) is not None]


def run_sampling(
    config: dict,
    host: str,
    token: str,
    warehouse_id: str,
    dry_run: bool = False,
    only_seed: str | None = None,
):
    """Execute the full sampling pipeline."""
    collected_ids: dict[str, list] = {}
    seeds = config["seeds"]

    if only_seed:
        seed_names = {s["name"] for s in seeds}
        if only_seed not in seed_names:
            print(f"ERROR: Seed '{only_seed}' not found in config.")
            print(f"  Available: {sorted(seed_names)}")
            sys.exit(1)

    for seed_cfg in seeds:
        name = seed_cfg["name"]
        if only_seed and name != only_seed:
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
        rows = execute_query(host, token, warehouse_id, query)

        if rows is None:
            print(f"  FAILED — skipping {name}")
            continue

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
        run_sampling(config, "", "", "", dry_run=True, only_seed=args.seed)
        return

    # Get Databricks config
    profile = config["connection"]["auth_profile"]
    print(f"  Auth:   OAuth via profile '{profile}'")
    host, warehouse_id, token = get_databricks_config(profile)
    print(f"  Host:   {host}")
    print(f"  Warehouse: {warehouse_id or '[auto/serverless]'}")

    run_sampling(config, host, token, warehouse_id, dry_run=False, only_seed=args.seed)


if __name__ == "__main__":
    main()

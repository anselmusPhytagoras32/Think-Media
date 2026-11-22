"""NFR07: export the approved hosted demo to private workstation storage."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

from sqlalchemy.engine import make_url


def export(credentials_file: Path, pg_bin: Path, output_dir: Path):
    record = json.loads(credentials_file.read_text(encoding="utf-8"))
    url = make_url(record["external_database_url"])
    if (
        url.get_backend_name() not in {"postgres", "postgresql"}
        or url.database != "thinkmedia_demo"
        or url.username != "thinkmedia_demo_runtime"
        or url.query.get("sslmode") != "require"
    ):
        raise ValueError("Use the dedicated ThinkMedia demo backup credentials.")
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / ("thinkmedia-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".dump")
    pending = destination.with_suffix(".partial")
    environment = {
        **os.environ,
        "PGPASSWORD": url.password,
        "PGSSLMODE": "require",
        "PGCONNECT_TIMEOUT": "20",
    }
    result = subprocess.run(
        [
            str(pg_bin / ("pg_dump.exe" if os.name == "nt" else "pg_dump")),
            "--host", url.host, "--port", str(url.port or 5432),
            "--username", url.username, "--dbname", url.database,
            "--format=custom", "--no-owner", "--no-acl",
            "--file", str(pending),
        ],
        env=environment, capture_output=True, timeout=180, check=False,
    )
    if result.returncode:
        raise RuntimeError("PostgreSQL export failed. Check connectivity and database version.")
    pending.rename(destination)
    return {"archive": str(destination), "bytes": destination.stat().st_size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials-file", type=Path, required=True)
    parser.add_argument("--pg-bin", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = export(args.credentials_file, args.pg_bin, args.output_dir)
    except Exception as failure:
        parser.exit(1, f"Hosted backup failed ({type(failure).__name__}).\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()

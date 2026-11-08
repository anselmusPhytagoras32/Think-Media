"""FR01/05, NFR02/03/11: local aggregate storage report and session expiry.

Run from backend: python -m ops.maintenance
The default is read-only. --prune-expired-sessions removes only sessions whose
absolute expiry has passed. Applications, attachments and audit history are
never deleted; their retention requires an approved policy.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url


def local_database_url() -> str:
    """Require explicit local configuration; do not fall back to app defaults."""
    if os.environ.get("APP_ENV", "").strip().lower() not in {
        "local", "test", "development"
    }:
        raise ValueError("Set APP_ENV explicitly to local, test or development.")
    raw = os.environ.get("DATABASE_URL", "")
    if not raw:
        raise ValueError("Set DATABASE_URL explicitly to a local database.")
    try:
        url = make_url(raw)
    except Exception:
        raise ValueError("DATABASE_URL must be a valid PostgreSQL URL.") from None
    if (
        url.get_backend_name() != "postgresql"
        or url.host not in {"localhost", "127.0.0.1", "::1"}
        or not url.database
        # libpq connection overrides could otherwise bypass the host check.
        or url.query
    ):
        raise ValueError("Only explicit loopback PostgreSQL URLs without query overrides are permitted.")
    return raw


def snapshot(connection, cutoff: datetime) -> dict:
    """Return aggregate numbers only, without user, file or credential values."""
    quote = connection.dialect.identifier_preparer.quote
    tables = sorted(inspect(connection).get_table_names(schema="public"))
    counts = {
        name: connection.scalar(text(f'SELECT count(*) FROM public.{quote(name)}'))
        for name in tables
    }
    return {
        "database_bytes": connection.scalar(
            text("SELECT pg_database_size(current_database())")
        ),
        "row_counts": counts,
        "private_attachment_bytes": connection.scalar(
            text("SELECT coalesce(sum(octet_length(attachment)), 0) FROM applications")
        ),
        "expired_sessions": connection.scalar(
            text("SELECT count(*) FROM sessions WHERE expires_at <= :cutoff"),
            {"cutoff": cutoff},
        ),
    }


def run(*, prune_expired_sessions: bool = False) -> dict:
    """Report and optional deletion share one transaction; failure rolls back."""
    database_url = local_database_url()
    engine = create_engine(database_url)
    cutoff = datetime.now(timezone.utc)
    try:
        with engine.begin() as connection:
            if not prune_expired_sessions:
                connection.execute(text("SET TRANSACTION READ ONLY"))
            removed = 0
            if prune_expired_sessions:
                result = connection.execute(
                    text("DELETE FROM sessions WHERE expires_at <= :cutoff"),
                    {"cutoff": cutoff},
                )
                removed = result.rowcount
            report = snapshot(connection, cutoff)
            report.update(
                requirement="FR01/05; NFR02/03/11",
                generated_at=cutoff.isoformat(),
                mode="prune_expired_sessions" if prune_expired_sessions else "read_only",
                deleted_sessions=removed,
                application_file_retention="No application or attachment deletion is performed.",
            )
        return report
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prune-expired-sessions", action="store_true")
    args = parser.parse_args()
    try:
        report = run(prune_expired_sessions=args.prune_expired_sessions)
    except ValueError as error:
        parser.exit(2, f"Configuration error: {error}\n")
    except Exception:
        # DB exceptions can contain connection parameters or query data.
        parser.exit(1, "Maintenance failed; the transaction was rolled back. Check local database readiness and permissions.\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

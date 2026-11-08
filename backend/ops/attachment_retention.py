"""NFR03/04/11: local policy-controlled attachment expiry; dry run by default."""
import argparse
import json
import os

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.services.attachment_retention import run


def local_database_url():
    if os.environ.get("APP_ENV", "").strip().lower() not in {"local", "test", "development"}:
        raise ValueError("Set APP_ENV explicitly to local, test or development.")
    raw = os.environ.get("DATABASE_URL", "")
    try:
        url = make_url(raw)
    except Exception:
        raise ValueError("Set an explicit valid PostgreSQL DATABASE_URL.") from None
    if url.get_backend_name() != "postgresql" or url.host not in {"localhost", "127.0.0.1", "::1"} or not url.database or url.query:
        raise ValueError("Only explicit loopback PostgreSQL without query overrides is permitted.")
    return raw


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retention-days", required=True, type=int)
    parser.add_argument("--policy-reference", required=True)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-expiry", action="store_true")
    parser.add_argument("--actor-email")
    args = parser.parse_args(argv)
    engine = None
    try:
        raw = local_database_url()
        engine = create_engine(raw)
        with Session(engine) as db:
            report = run(db, retention_days=args.retention_days, policy_reference=args.policy_reference,
                batch_size=args.batch_size, apply=args.apply, confirm_expiry=args.confirm_expiry,
                actor_email=args.actor_email)
    except ValueError as error:
        parser.exit(2, f"Retention configuration error: {error}\n")
    except Exception:
        parser.exit(1, "Retention operation failed and was rolled back. Check local database readiness and policy configuration.\n")
    finally:
        if engine is not None:
            engine.dispose()
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

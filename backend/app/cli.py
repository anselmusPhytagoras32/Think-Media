"""Local administrator provisioning CLI (hidden password entry only).

Usage:
    python -m app.cli create-admin --email admin@example.org --display-name "Site Admin"

The password is prompted with hidden input and confirmed. There is no default
administrator and no HTTP endpoint that can create or elevate an administrator.
"""

from __future__ import annotations

import argparse
import getpass
import sys

from app.config import Settings
from app.db import build_engine, build_session_factory
from app.errors import ApiError
from app.services.accounts import AccountService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="ThinkMedia local management commands (not an HTTP surface).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_admin = subparsers.add_parser(
        "create-admin", help="Provision an administrator account."
    )
    create_admin.add_argument("--email", required=True, help="Administrator email address.")
    create_admin.add_argument(
        "--display-name", required=True, help="Administrator display name."
    )
    return parser


def _prompt_password() -> str:
    password = getpass.getpass("Administrator password: ")
    confirmation = getpass.getpass("Confirm administrator password: ")
    if password != confirmation:
        raise ValueError("Passwords do not match.")
    return password


def create_admin(email: str, display_name: str, password: str) -> int:
    settings = Settings()
    engine = build_engine(settings)
    factory = build_session_factory(engine)
    try:
        with factory() as db:
            AccountService(db).create_administrator(
                email=email, password=password, display_name=display_name
            )
    except ApiError as exc:
        print(f"Error: {exc.message}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception:
        # Never print the DSN, SQL or any part of the password.
        print("Error: could not provision administrator (database error).", file=sys.stderr)
        return 1
    finally:
        engine.dispose()
    print("Administrator provisioned.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "create-admin":
        try:
            password = _prompt_password()
        except (ValueError, EOFError, KeyboardInterrupt) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
        return create_admin(args.email, args.display_name, password)
    print("Unknown command.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

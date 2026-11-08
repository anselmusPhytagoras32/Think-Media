"""FR01/02/11, NFR02/03/06: provision four synthetic local presentation roles.

Run from backend with an explicit local DATABASE_URL and APP_ENV=local:
    python -m ops.presentation_accounts
Passwords are generated once in .local/presentation/presentation-accounts.private.json.
The manifest is a private recovery journal, never console output or research data.
Existing users, passwords, profiles and company verification are never reset.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.engine import make_url

from app.config import Settings
from app.db import build_engine, build_session_factory
from app.models import User
from app.repositories import ProfileRepository, UserRepository
from app.security.passwords import hash_password, verify_password
from app.validation import normalize_display_name, normalize_email, validate_password


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ROLES = ("student", "instructor", "company", "administrator")
MANIFEST_NAME = "presentation-accounts.private.json"


def configuration():
    raw = os.environ.get("DATABASE_URL", "")
    if os.environ.get("APP_ENV", "").strip().lower() != "local" or not raw:
        raise ValueError("Set APP_ENV=local and DATABASE_URL explicitly.")
    try:
        url = make_url(raw)
    except Exception:
        raise ValueError("Use a valid local PostgreSQL database URL.") from None
    if (
        url.get_backend_name() != "postgresql"
        or url.host not in {"localhost", "127.0.0.1", "::1"}
        or not (url.database or "").endswith("_local")
        or url.query
    ):
        raise ValueError("Use loopback PostgreSQL ending in _local without query overrides.")
    return Settings(_env_file=None, app_env="local", database_url=raw), {
        "host": url.host, "port": url.port or 5432,
        "database": url.database, "username": url.username,
    }


def private_state_dir(state_dir: Path | None) -> Path:
    allowed = (REPOSITORY_ROOT / ".local").resolve()
    if not allowed.is_relative_to(REPOSITORY_ROOT.resolve()):
        raise ValueError("Repository/.local must not resolve outside the repository.")
    chosen = state_dir if state_dir is not None else allowed / "presentation"
    if not chosen.is_absolute():
        raise ValueError("The state directory must be absolute and inside repository/.local.")
    resolved = chosen.resolve()
    if not resolved.is_relative_to(allowed):
        raise ValueError("The state directory must stay inside repository/.local.")
    return resolved


def new_manifest(database: dict) -> dict:
    return {
        "version": 1, "synthetic_only": True, "database": database,
        "accounts": {
            role: {
                "id": str(uuid4()),
                "email": f"presentation-{role}@example.test",
                "password": secrets.token_urlsafe(24),
            }
            for role in ROLES
        },
    }


def validate_manifest(manifest: dict, database: dict):
    if (
        not isinstance(manifest, dict) or manifest.get("version") != 1
        or manifest.get("synthetic_only") is not True
        or manifest.get("database") != database
        or set(manifest.get("accounts", {})) != set(ROLES)
    ):
        raise ValueError("Presentation manifest is invalid or belongs to another database.")
    ids = []
    for role in ROLES:
        account = manifest["accounts"][role]
        if not isinstance(account, dict) or set(account) != {"id", "email", "password"}:
            raise ValueError("Presentation account manifest is invalid.")
        if account["email"] != f"presentation-{role}@example.test":
            raise ValueError("Presentation email does not match its dedicated role.")
        ids.append(UUID(account["id"]))
        validate_password(account["password"])
    if len(set(ids)) != len(ROLES):
        raise ValueError("Presentation manifest requires distinct account IDs.")


def verify_ownership(db, manifest):
    users = UserRepository(db)
    for role in ROLES:
        account = manifest["accounts"][role]
        user = users.get_by_email(account["email"])
        by_id = users.get_by_id(UUID(account["id"]))
        if user is None and by_id is None:
            continue
        if (
            user is None or by_id is None or user.id != by_id.id
            or str(user.id) != account["id"] or user.role != role
        ):
            raise ValueError("An existing account is not owned by this presentation manifest.")
        if not verify_password(account["password"], user.password_hash):
            raise ValueError("An existing presentation password differs; it will not be reset.")


def create_accounts(db, manifest):
    """Use the account/CLI repository boundaries without intermediate commits."""
    users, profiles = UserRepository(db), ProfileRepository(db)
    created = []
    for role in ROLES:
        account = manifest["accounts"][role]
        if users.get_by_email(account["email"]) is not None:
            continue
        user = users.create(
            user_id=UUID(account["id"]),
            email=normalize_email(account["email"]),
            password_hash=hash_password(validate_password(account["password"])),
            display_name=normalize_display_name(f"Presentation {role.title()} (synthetic)"),
            role=role,
        )
        if role == "student":
            profile = profiles.create_student(user.id)
            profile.institution = "Presentation Campus (synthetic)"
            profile.program = "BS Information Technology"
            profile.location = "Metro Manila"
            profile.skills = ["React", "Python", "SQL"]
            profile.interests = ["OJT", "Web development"]
            profile.background = "Synthetic presentation account; not a real participant."
        elif role == "instructor":
            profiles.create_instructor(user.id).institution = "Presentation Campus (synthetic)"
        elif role == "company":
            profile = profiles.create_company(
                user_id=user.id, company_name="Presentation Practice Studio (synthetic)"
            )
            profile.description = "Synthetic presentation company; no real vacancies or partnership."
            profile.location = "Metro Manila"
            profile.contact_email = account["email"]
        # Administrator is provisioned only by this explicit local command,
        # matching the CLI's hashing/UserRepository path; no public role change.
        created.append(role)
    db.flush()
    return created


def provision(state_dir: Path | None = None) -> dict:
    settings, database = configuration()
    state_dir = private_state_dir(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = state_dir / MANIFEST_NAME
    if path.is_symlink():
        raise ValueError("The private manifest must not be a symbolic link.")
    existing = path.exists()
    manifest = json.loads(path.read_text(encoding="utf-8")) if existing else new_manifest(database)
    validate_manifest(manifest, database)
    engine = build_engine(settings)
    try:
        with build_session_factory(engine)() as db, db.begin():
            if not existing:
                if db.scalar(select(User.id).where(User.email.in_(
                    [manifest["accounts"][role]["email"] for role in ROLES]
                )).limit(1)) is not None:
                    raise ValueError("A dedicated presentation email already exists without this manifest.")
            verify_ownership(db, manifest)
            if not existing:
                # Journal ownership IDs and credentials before a DB commit. If
                # any later step fails, all DB writes roll back and the intact
                # journal permits retry without losing or resetting passwords.
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    json.dump(manifest, stream, indent=2)
                    stream.flush()
                    os.fsync(stream.fileno())
            created = create_accounts(db, manifest)
        return {
            "synthetic_only": True,
            "created_roles": created,
            "accounts": {role: manifest["accounts"][role]["email"] for role in ROLES},
            "credentials_file": str(path),
            "company_verification": "Existing state preserved; newly created company is pending.",
        }
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path)
    args = parser.parse_args()
    try:
        output = provision(args.state_dir)
    except Exception:
        # Never expose connection parameters, passwords or SQL exception values.
        parser.exit(1, "Presentation provisioning failed. Check local configuration, dedicated email ownership and the private manifest. Existing passwords are never reset.\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

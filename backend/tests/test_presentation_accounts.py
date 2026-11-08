"""FR01/02/11, NFR02/03: local-only synthetic role access without resets."""

import json
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.config import Settings
from app.models import CompanyProfile, User
from app.security.passwords import verify_password
from ops import presentation_accounts as accounts


def test_default_state_root_is_the_repository_containing_backend():
    expected_root = Path(__file__).resolve().parents[2]
    assert accounts.REPOSITORY_ROOT == expected_root
    assert Path(accounts.__file__).resolve().is_relative_to(expected_root / "backend" / "ops")


@pytest.mark.parametrize("app_env,url", [
    ("", "postgresql+psycopg://localhost/demo_local"),
    ("production", "postgresql+psycopg://localhost/demo_local"),
    ("local", ""),
    ("local", "postgresql+psycopg://remote.example/demo_local"),
    ("local", "postgresql+psycopg://localhost/demo_test"),
    ("local", "postgresql+psycopg://localhost/demo_local?host=remote.example"),
])
def test_configuration_rejects_nonlocal_or_implicit_target(monkeypatch, app_env, url):
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("DATABASE_URL", url)
    with pytest.raises(ValueError):
        accounts.configuration()


def test_state_path_rejects_relative_outside_and_symlink_escape(tmp_path, monkeypatch):
    monkeypatch.setattr(accounts, "REPOSITORY_ROOT", tmp_path)
    with pytest.raises(ValueError):
        accounts.private_state_dir(tmp_path.parent / "outside")
    with pytest.raises(ValueError):
        accounts.private_state_dir(type(tmp_path)("relative"))
    assert accounts.private_state_dir(None) == tmp_path / ".local" / "presentation"
    (tmp_path / ".local").mkdir()
    (tmp_path / "outside").mkdir()
    try:
        (tmp_path / ".local" / "escape").symlink_to(tmp_path / "outside", target_is_directory=True)
    except OSError:
        pytest.skip("Symbolic link creation is unavailable on this platform.")
    with pytest.raises(ValueError):
        accounts.private_state_dir(tmp_path / ".local" / "escape")


@pytest.fixture()
def setup(monkeypatch, tmp_path, database_url):
    # Exercise real PostgreSQL in the disposable test DB, while target-guard
    # behavior is separately asserted above; never seed presentation data in tests.
    monkeypatch.setattr(accounts, "REPOSITORY_ROOT", tmp_path)
    settings = Settings(_env_file=None, app_env="test", database_url=database_url)
    identity = {"host": "localhost", "database": "synthetic_test", "port": 0, "username": "test"}
    monkeypatch.setattr(accounts, "configuration", lambda: (settings, identity))
    return tmp_path / ".local" / "presentation"


def test_provision_all_roles_pending_company_and_private_credentials(setup, db, capsys):
    result = accounts.provision(setup)
    manifest = json.loads((setup / accounts.MANIFEST_NAME).read_text())
    assert set(result["created_roles"]) == set(accounts.ROLES)
    assert db.scalar(select(func.count()).select_from(User)) == 4
    for role, entry in manifest["accounts"].items():
        user = db.scalar(select(User).where(User.email == entry["email"]))
        assert str(user.id) == entry["id"] and user.role == role
        assert verify_password(entry["password"], user.password_hash)
        assert entry["password"] not in json.dumps(result)
        assert entry["password"] not in capsys.readouterr().out
    company = db.scalar(select(CompanyProfile))
    assert company.verification_status == "pending"


def test_idempotent_preserves_passwords_profiles_and_verification(setup, db):
    accounts.provision(setup)
    before = (setup / accounts.MANIFEST_NAME).read_bytes()
    company = db.scalar(select(CompanyProfile))
    company.description = "Changed during actual demo"
    company.verification_status = "verified"
    db.commit()
    hashes = dict(db.execute(select(User.email, User.password_hash)).all())
    second = accounts.provision(setup)
    db.expire_all()
    assert second["created_roles"] == []
    assert (setup / accounts.MANIFEST_NAME).read_bytes() == before
    assert dict(db.execute(select(User.email, User.password_hash)).all()) == hashes
    assert company.description == "Changed during actual demo"
    assert company.verification_status == "verified"


def test_collision_without_owned_manifest_refuses_and_preserves_existing(setup, db):
    from app.services.accounts import AccountService
    AccountService(db).create_administrator(
        email="presentation-student@example.test", display_name="Existing owner",
        password="Existing-owner-password-123",
    )
    with pytest.raises(ValueError, match="already exists"):
        accounts.provision(setup)
    assert db.scalar(select(func.count()).select_from(User)) == 1
    assert not (setup / accounts.MANIFEST_NAME).exists()


def test_failure_rolls_back_all_accounts_and_journal_allows_retry(setup, db, monkeypatch):
    original = accounts.create_accounts

    def fail(session, manifest):
        original(session, manifest)
        raise RuntimeError("Injected failure before commit")

    monkeypatch.setattr(accounts, "create_accounts", fail)
    with pytest.raises(RuntimeError, match="Injected"):
        accounts.provision(setup)
    assert db.scalar(select(func.count()).select_from(User)) == 0
    journal = (setup / accounts.MANIFEST_NAME).read_bytes()
    monkeypatch.setattr(accounts, "create_accounts", original)
    assert len(accounts.provision(setup)["created_roles"]) == 4
    assert (setup / accounts.MANIFEST_NAME).read_bytes() == journal


def test_manifest_database_mismatch_never_changes_accounts(setup, db):
    accounts.provision(setup)
    path = setup / accounts.MANIFEST_NAME
    manifest = json.loads(path.read_text())
    manifest["database"]["database"] = "another_local"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="another database"):
        accounts.provision(setup)
    assert db.scalar(select(func.count()).select_from(User)) == 4

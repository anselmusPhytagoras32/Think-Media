"""Administrator provisioning CLI (explicit local command, hidden password)."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app import cli
from app.models import InstructorProfile, StudentProfile, User
from tests.helpers import ADMIN_PASSWORD, create_admin, login


def test_service_provisions_only_an_administrator(app, client, db):
    create_admin(app, email="cli-admin@example.org", display_name="CLI Admin")
    user = db.scalar(select(User).where(User.email == "cli-admin@example.org"))
    assert user is not None
    assert user.role == "administrator"
    assert user.password_hash.startswith("$argon2id$")
    assert db.scalar(select(func.count()).select_from(StudentProfile)) == 0
    assert db.scalar(select(func.count()).select_from(InstructorProfile)) == 0

    response = login(client, email="cli-admin@example.org", password=ADMIN_PASSWORD)
    assert response.status_code == 200
    assert response.json()["profile"] == {"kind": "administrator"}


def test_duplicate_administrator_is_rejected(app):
    create_admin(app, email="dupe-admin@example.org")
    from app.errors import ApiError
    from app.services.accounts import AccountService

    with app.state.session_factory() as session:
        with pytest.raises(ApiError) as exc:
            AccountService(session).create_administrator(
                email="dupe-admin@example.org",
                password=ADMIN_PASSWORD,
                display_name="Duplicate",
            )
    assert exc.value.status_code == 409
    assert exc.value.code == "EMAIL_EXISTS"


def test_hidden_password_prompt_requires_confirmation(monkeypatch):
    answers = iter(["a-long-password-123", "a-long-password-123"])
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt="": next(answers))
    assert cli._prompt_password() == "a-long-password-123"

    answers = iter(["a-long-password-123", "different-password-123"])
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt="": next(answers))
    with pytest.raises(ValueError):
        cli._prompt_password()


def test_cli_main_provisions_admin_and_hides_password(
    monkeypatch, database_url, app, client
):
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setattr(
        cli, "_prompt_password", lambda: "cli-password-12345"
    )
    exit_code = cli.main(
        [
            "create-admin",
            "--email",
            "main-admin@example.org",
            "--display-name",
            "Main Admin",
        ]
    )
    assert exit_code == 0

    response = login(
        client, email="main-admin@example.org", password="cli-password-12345"
    )
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "administrator"

    # Duplicate provisioning fails without changing the account.
    exit_code = cli.main(
        [
            "create-admin",
            "--email",
            "main-admin@example.org",
            "--display-name",
            "Another",
        ]
    )
    assert exit_code == 1


def test_cli_has_no_password_argument():
    parser = cli.build_parser()
    subparsers_action = next(
        action for action in parser._actions if action.dest == "command"
    )
    create_admin_parser = subparsers_action.choices["create-admin"]
    assert "password" not in {action.dest for action in create_admin_parser._actions}
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "create-admin",
                "--email",
                "x@example.org",
                "--display-name",
                "X",
                "--password",
                "leak",
            ]
        )

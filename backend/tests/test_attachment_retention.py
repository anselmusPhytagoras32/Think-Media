"""FR05/07/11; NFR02/03/04/11: explicit private-file expiry in test DB only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
from pathlib import Path
from threading import Barrier, Event
from uuid import UUID, uuid4

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import event, func, select, text
from sqlalchemy.exc import IntegrityError

from app.models import Application, ApplicationStatusHistory, AttachmentRetentionEvent, Listing, User
from app.services.attachment_retention import run, validate_policy
from app.time_utils import utcnow
from ops.attachment_retention import local_database_url, main
from tests.helpers import create_admin, login_admin, patch_json, post_json
from tests.test_marketplace import PDF, company, listing, student, upload

ADMIN_EMAIL = "retention-admin@example.test"


def fixture_application(app, *, final="rejected", close=True, review=False):
    suffix = uuid4().hex[:10]
    recruiter = company(app, email=f"retention-company-{suffix}@example.test")
    learner = student(app, email=f"retention-student-{suffix}@example.test")
    opportunity = listing(recruiter)
    receipt = upload(learner, opportunity["id"])
    assert receipt.status_code == 201
    record = receipt.json()
    if final == "accepted" or review:
        assert patch_json(recruiter, f'/api/v1/applications/{record["id"]}/status', {"status": "under_review"}).status_code == 200
    if final:
        assert patch_json(recruiter, f'/api/v1/applications/{record["id"]}/status', {"status": final}).status_code == 200
    if close:
        assert post_json(recruiter, f'/api/v1/company/listings/{opportunity["id"]}/close').status_code == 200
    now = utcnow()
    old = now - timedelta(days=45)
    with app.state.session_factory() as db:
        row = db.get(Application, UUID(record["id"]))
        row.created_at = old
        db.get(Listing, row.listing_id).updated_at = old
        history = list(db.scalars(select(ApplicationStatusHistory).where(
            ApplicationStatusHistory.application_id == row.id
        ).order_by(ApplicationStatusHistory.created_at, ApplicationStatusHistory.id)))
        for index, entry in enumerate(history):
            entry.created_at = old + timedelta(seconds=index + 1)
        db.commit()
    return UUID(record["id"]), recruiter, learner, now


def execute(app, *, apply=False, now=None, batch_size=100, actor_email=ADMIN_EMAIL, confirm=True):
    with app.state.session_factory() as db:
        return run(db, retention_days=30, policy_reference="Synthetic test policy; not real approval",
                   apply=apply, confirm_expiry=confirm, actor_email=actor_email,
                   batch_size=batch_size, now=now)


@pytest.mark.parametrize("environment,url", [
    ("", "postgresql+psycopg://localhost/demo_local"),
    ("production", "postgresql+psycopg://localhost/demo_local"),
    ("local", ""),
    ("local", "sqlite:///demo"),
    ("local", "postgresql+psycopg://remote.example/demo_local"),
    ("local", "postgresql+psycopg://localhost/demo_local?host=remote.example"),
])
def test_operator_target_requires_explicit_local_configuration(monkeypatch, environment, url):
    monkeypatch.setenv("APP_ENV", environment)
    monkeypatch.setenv("DATABASE_URL", url)
    with pytest.raises(ValueError):
        local_database_url()


@pytest.mark.parametrize("days,policy,batch", [
    (0, "policy", 100), (True, "policy", 100), (36501, "policy", 100),
    (30, "", 100), (30, "x" * 201, 100), (30, "line\nbreak", 100),
    (30, "policy", 0), (30, "policy", 101),
])
def test_policy_and_batch_are_explicit_and_bounded(days, policy, batch):
    with pytest.raises(ValueError):
        validate_policy(days, policy, batch)


def test_dry_run_is_aggregate_and_preserves_all_bytes_history(app):
    application_id, _, learner, now = fixture_application(app)
    before = learner.get(f"/api/v1/applications/{application_id}").json()
    report = execute(app, now=now)
    assert report["mode"] == "dry_run" and report["eligible_files"] == 1
    assert report["eligible_bytes"] == len(PDF) and report["expired_files"] == 0
    assert report["cutoff"].endswith("+08:00")
    after = learner.get(f"/api/v1/applications/{application_id}").json()
    assert before == after and after["attachment_available"]
    assert after["attachment_deleted_at"] is None
    assert learner.get(f"/api/v1/applications/{application_id}/attachment").content == PDF
    with app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(AttachmentRetentionEvent)) == 0
    output = json.dumps(report)
    assert str(application_id) not in output and "resume.pdf" not in output and "PDF-1.4" not in output


def test_retention_queries_do_not_load_application_text_names_or_passwords(app):
    _, _, _, now = fixture_application(app)
    create_admin(app, email=ADMIN_EMAIL)
    selected = []
    def capture(_connection, _cursor, statement, _parameters, _context, _many):
        if statement.lstrip().upper().startswith("SELECT"):
            selected.append(statement)
    event.listen(app.state.engine, "before_cursor_execute", capture)
    try:
        assert execute(app, apply=True, now=now)["expired_files"] == 1
    finally:
        event.remove(app.state.engine, "before_cursor_execute", capture)
    assert selected
    assert all("cover_letter" not in sql and "attachment_name" not in sql and "password_hash" not in sql for sql in selected)


def test_apply_requires_confirmation_and_current_administrator(app):
    application_id, _, learner, now = fixture_application(app)
    with pytest.raises(ValueError, match="confirmation"):
        execute(app, apply=True, now=now, confirm=False)
    with pytest.raises(ValueError, match="current administrator"):
        execute(app, apply=True, now=now)
    actor_id = create_admin(app, email=ADMIN_EMAIL)
    with app.state.session_factory() as db:
        db.get(User, actor_id).role = "student"
        db.commit()
    with pytest.raises(ValueError, match="current administrator"):
        execute(app, apply=True, now=now)
    assert learner.get(f"/api/v1/applications/{application_id}/attachment").content == PDF


def test_cached_administrator_demoted_between_transactions_is_denied(app):
    application_id, _, learner, now = fixture_application(app)
    actor_id = create_admin(app, email=ADMIN_EMAIL)
    with app.state.session_factory() as cached:
        actor = cached.get(User, actor_id)
        cached.commit()
        assert actor.role == "administrator"
        with app.state.session_factory() as changed:
            changed.get(User, actor_id).role = "student"
            changed.commit()
        # The caller has no active transaction, but the identity map still has
        # the old role. The privilege decision must use the current DB value.
        assert actor.role == "administrator" and not cached.in_transaction()
        with pytest.raises(ValueError, match="current administrator"):
            run(cached, retention_days=30, policy_reference="Synthetic role-race policy",
                apply=True, confirm_expiry=True, actor_email=ADMIN_EMAIL, now=now)
    assert learner.get(f"/api/v1/applications/{application_id}/attachment").content == PDF


@pytest.mark.parametrize("final,review", [("accepted", True), ("rejected", False), ("rejected", True)])
def test_expiry_preserves_decision_and_history_and_authorizes_before_410(app, final, review):
    application_id, recruiter, learner, now = fixture_application(app, final=final, review=review)
    create_admin(app, email=ADMIN_EMAIL)
    before = learner.get(f"/api/v1/applications/{application_id}").json()
    result = execute(app, apply=True, now=now)
    assert result["expired_files"] == 1
    for actor in (learner, recruiter):
        response = actor.get(f"/api/v1/applications/{application_id}/attachment")
        assert response.status_code == 410 and response.json()["error"]["code"] == "ATTACHMENT_EXPIRED"
        assert response.headers["cache-control"] == "no-store"
        current = actor.get(f"/api/v1/applications/{application_id}").json()
        assert current["attachment_available"] is False and current["attachment_deleted_at"].endswith("+08:00")
        assert current["attachment_name"] == "expired.pdf"
        assert current["history"] == before["history"] and current["status"] == final
        assert current["reference"] == before["reference"]
    outsider = student(app, email=f"outsider-{uuid4().hex[:8]}@example.test")
    instructor = student(app, email=f"instructor-{uuid4().hex[:8]}@example.test", role="instructor")
    other_company = company(app, email=f"other-company-{uuid4().hex[:8]}@example.test")
    administrator = TestClient(app)
    login_admin(administrator, email=ADMIN_EMAIL)
    for actor in (outsider, instructor, other_company, administrator):
        response = actor.get(f"/api/v1/applications/{application_id}/attachment")
        assert response.status_code == 404 and "EXPIRED" not in response.text
    assert TestClient(app).get(f"/api/v1/applications/{application_id}/attachment").status_code == 401
    with app.state.session_factory() as db:
        row = db.get(Application, application_id)
        assert row.attachment is None
        audit = db.scalar(select(AttachmentRetentionEvent).where(AttachmentRetentionEvent.application_id == application_id))
        assert audit.byte_count == len(PDF) and audit.retention_days == 30
        assert audit.created_at == row.attachment_deleted_at
        assert db.get(User, audit.actor_id).role == "administrator"
    assert execute(app, apply=True, now=now)["expired_files"] == 0


@pytest.mark.parametrize("case", [
    "pending", "open", "recent_submission", "recent_closure", "recent_decision",
    "missing_initial", "accepted_missing_review", "duplicate_initial", "wrong_old_status", "reversed_times",
])
def test_ineligible_or_incomplete_records_are_kept(app, case):
    final = "accepted" if case == "accepted_missing_review" else None if case == "pending" else "rejected"
    application_id, _, learner, now = fixture_application(app, final=final, close=case != "open")
    create_admin(app, email=ADMIN_EMAIL)
    with app.state.session_factory() as db:
        row = db.get(Application, application_id)
        history = list(db.scalars(select(ApplicationStatusHistory).where(
            ApplicationStatusHistory.application_id == application_id
        ).order_by(ApplicationStatusHistory.created_at)))
        if case == "recent_submission":
            row.created_at = now - timedelta(days=2)
        elif case == "recent_closure":
            db.get(Listing, row.listing_id).updated_at = now - timedelta(days=2)
        elif case == "recent_decision":
            history[-1].created_at = now - timedelta(days=2)
        elif case == "missing_initial":
            db.delete(history[0])
        elif case == "accepted_missing_review":
            db.delete(history[1])
        elif case == "duplicate_initial":
            db.add(ApplicationStatusHistory(application_id=application_id, actor_id=history[0].actor_id,
                old_status=None, new_status="submitted", created_at=history[0].created_at))
        elif case == "wrong_old_status":
            history[-1].old_status = "under_review"
        elif case == "reversed_times":
            history[0].created_at = history[-1].created_at + timedelta(seconds=1)
        db.commit()
    assert execute(app, apply=True, now=now)["expired_files"] == 0
    assert learner.get(f"/api/v1/applications/{application_id}/attachment").content == PDF


def test_tied_valid_chain_is_eligible_and_batch_limit_continues(app):
    first, _, _, now = fixture_application(app, final="accepted")
    second, _, _, _ = fixture_application(app)
    create_admin(app, email=ADMIN_EMAIL)
    with app.state.session_factory() as db:
        timestamp = now - timedelta(days=45)
        db.get(Application, first).created_at = timestamp
        for row in db.scalars(select(ApplicationStatusHistory).where(ApplicationStatusHistory.application_id == first)):
            row.created_at = timestamp
        db.commit()
    one = execute(app, apply=True, now=now, batch_size=1)
    two = execute(app, apply=True, now=now, batch_size=1)
    assert one["eligible_files"] == two["eligible_files"] == 1
    assert execute(app, apply=True, now=now, batch_size=1)["eligible_files"] == 0
    with app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(AttachmentRetentionEvent)) == 2


def test_audit_failure_rolls_back_bytes_tombstone_and_name(app):
    application_id, _, learner, now = fixture_application(app)
    create_admin(app, email=ADMIN_EMAIL)
    def fail_audit(*_):
        raise RuntimeError("Injected retention audit failure")
    event.listen(AttachmentRetentionEvent, "before_insert", fail_audit)
    try:
        with pytest.raises(RuntimeError, match="Injected retention audit"):
            execute(app, apply=True, now=now)
    finally:
        event.remove(AttachmentRetentionEvent, "before_insert", fail_audit)
    current = learner.get(f"/api/v1/applications/{application_id}").json()
    assert current["attachment_name"] == "resume.pdf" and current["attachment_available"]
    assert current["attachment_deleted_at"] is None
    assert learner.get(f"/api/v1/applications/{application_id}/attachment").content == PDF
    with app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(AttachmentRetentionEvent)) == 0


def test_concurrent_expiry_commits_one_event(app):
    application_id, _, _, now = fixture_application(app)
    create_admin(app, email=ADMIN_EMAIL)
    gate = Barrier(2)
    def expire(_):
        gate.wait(timeout=10)
        return execute(app, apply=True, now=now)["expired_files"]
    with ThreadPoolExecutor(max_workers=2) as pool:
        result = list(pool.map(expire, range(2)))
    assert sorted(result) == [0, 1]
    with app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(AttachmentRetentionEvent)) == 1
        assert db.scalar(select(func.count()).select_from(ApplicationStatusHistory).where(
            ApplicationStatusHistory.application_id == application_id)) == 2


def test_download_expiry_race_returns_410_instead_of_empty_pdf(app, monkeypatch):
    from app.services.marketplace import MarketplaceService
    application_id, _, learner, now = fixture_application(app)
    create_admin(app, email=ADMIN_EMAIL)
    authorized = Event()
    expired = Event()
    original = MarketplaceService.authorized_application
    def pause_after_authorization(self, id, lock=False):
        row = original(self, id, lock)
        authorized.set()
        assert expired.wait(timeout=10)
        return row
    monkeypatch.setattr(MarketplaceService, "authorized_application", pause_after_authorization)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(learner.get, f"/api/v1/applications/{application_id}/attachment")
        try:
            assert authorized.wait(timeout=10)
            assert execute(app, apply=True, now=now)["expired_files"] == 1
        finally:
            expired.set()
        response = pending.result(timeout=10)
    assert response.status_code == 410 and response.json()["error"]["code"] == "ATTACHMENT_EXPIRED"


@pytest.mark.parametrize("value,deleted", [(None, False), (PDF, True), (b"", False)])
def test_schema_rejects_inconsistent_attachment_state(app, value, deleted):
    application_id, _, _, now = fixture_application(app)
    with pytest.raises(IntegrityError):
        with app.state.session_factory() as db, db.begin():
            row = db.get(Application, application_id)
            row.attachment = value
            row.attachment_deleted_at = now if deleted else None
            db.flush()


def test_cli_rejects_unconfirmed_apply_without_exposing_private_configuration(monkeypatch, capsys):
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://synthetic:secret-marker@localhost/unreachable_local")
    # Confirmation guard is evaluated before any connection is established.
    with pytest.raises(SystemExit) as error:
        main(["--retention-days", "30", "--policy-reference", "Synthetic policy", "--apply"])
    assert error.value.code == 2
    output = capsys.readouterr()
    assert "secret-marker" not in output.out + output.err


def test_downgrade_refuses_tombstones_and_retains_version(app, database_url):
    application_id, _, _, now = fixture_application(app)
    create_admin(app, email=ADMIN_EMAIL)
    execute(app, apply=True, now=now)
    with app.state.session_factory() as db:
        before = db.scalar(text("SELECT version_num FROM alembic_version"))
    backend = Path(__file__).resolve().parents[1]
    config = Config(str(backend / "alembic.ini"))
    config.set_main_option("script_location", str(backend / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    with pytest.raises(RuntimeError, match="Cannot downgrade attachment retention"):
        command.downgrade(config, "0006_satisfaction_feedback")
    with app.state.session_factory() as db:
        assert db.scalar(text("SELECT version_num FROM alembic_version")) == before
        assert db.get(Application, application_id).attachment is None
        assert db.scalar(select(func.count()).select_from(AttachmentRetentionEvent)) == 1


def test_retention_upgrade_preserves_existing_pdf_reference_and_history(app, database_url):
    application_id, _, learner, _ = fixture_application(app, final="accepted")
    backend = Path(__file__).resolve().parents[1]
    config = Config(str(backend / "alembic.ini"))
    config.set_main_option("script_location", str(backend / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    def snapshot():
        with app.state.session_factory() as db:
            reference, payload, name = db.execute(text(
                "SELECT reference, attachment, attachment_name FROM applications WHERE id=:id"
            ), {"id": application_id}).one()
            history = list(db.execute(text(
                "SELECT actor_id, old_status, new_status, created_at FROM application_status_history "
                "WHERE application_id=:id ORDER BY created_at, id"
            ), {"id": application_id}))
            return reference, bytes(payload), name, history
    original = snapshot()
    command.downgrade(config, "0006_satisfaction_feedback")
    assert snapshot() == original
    command.upgrade(config, "head")
    assert snapshot() == original
    current = learner.get(f"/api/v1/applications/{application_id}")
    assert current.status_code == 200 and current.json()["attachment_available"]
    assert current.json()["attachment_deleted_at"] is None

"""Real PostgreSQL constraint tests (roles, statuses, FKs, uniqueness, triggers)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DataError, IntegrityError

from tests.helpers import register


def _insert_user(db, *, email: str, role: str = "student"):
    return db.execute(
        text(
            "INSERT INTO users (email, password_hash, display_name, role) "
            "VALUES (:email, '$argon2id$placeholder', 'Constraint User', :role) "
            "RETURNING id"
        ),
        {"email": email, "role": role},
    ).scalar_one()


def test_users_role_check_constraint(db):
    with pytest.raises(IntegrityError):
        db.execute(
            text(
                "INSERT INTO users (email, password_hash, display_name, role) "
                "VALUES ('bad-role@example.org', 'x', 'Bad', 'superadmin')"
            )
        )
        db.flush()
    db.rollback()


def test_users_reject_overlong_or_blank_display_name(db):
    for name in ("", "x" * 101):
        with pytest.raises((IntegrityError, DataError)):
            db.execute(
                text(
                    "INSERT INTO users (email, password_hash, display_name, role) "
                    "VALUES (:email, 'x', :name, 'student')"
                ),
                {"email": f"{uuid.uuid4().hex}@example.org", "name": name},
            )
            db.flush()
        db.rollback()


def test_email_uniqueness(db):
    _insert_user(db, email="dupe@example.org")
    db.commit()
    with pytest.raises(IntegrityError):
        _insert_user(db, email="dupe@example.org")
        db.flush()
    db.rollback()


def test_email_must_be_stored_normalized(db):
    with pytest.raises(IntegrityError):
        _insert_user(db, email="UPPER@example.org")
        db.flush()
    db.rollback()


def test_company_profile_foreign_key_and_status_check(db):
    with pytest.raises(IntegrityError):
        db.execute(
            text(
                "INSERT INTO company_profiles (user_id, company_name, verification_status) "
                "VALUES (:id, 'Orphan', 'pending')"
            ),
            {"id": uuid.uuid4()},
        )
        db.flush()
    db.rollback()

    user_id = _insert_user(db, email="company-constraint@example.org", role="company")
    with pytest.raises(IntegrityError):
        db.execute(
            text(
                "INSERT INTO company_profiles (user_id, company_name, verification_status) "
                "VALUES (:id, 'Bad Status', 'approved')"
            ),
            {"id": user_id},
        )
        db.flush()
    db.rollback()

    user_id = _insert_user(db, email="company-ok@example.org", role="company")
    db.commit()
    db.execute(
        text(
            "INSERT INTO company_profiles (user_id, company_name) VALUES (:id, 'Okay')"
        ),
        {"id": user_id},
    )
    db.commit()
    status, version = db.execute(
        text(
            "SELECT verification_status, verification_version FROM company_profiles "
            "WHERE user_id = :id"
        ),
        {"id": user_id},
    ).one()
    assert status == "pending"
    assert version == 1


def test_company_profile_one_per_user(db):
    user_id = _insert_user(db, email="company-one@example.org", role="company")
    db.commit()
    db.execute(
        text("INSERT INTO company_profiles (user_id, company_name) VALUES (:id, 'One')"),
        {"id": user_id},
    )
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(
            text(
                "INSERT INTO company_profiles (user_id, company_name) VALUES (:id, 'Two')"
            ),
            {"id": user_id},
        )
        db.flush()
    db.rollback()


def test_profile_role_triggers_prevent_misclassification(db):
    instructor_id = _insert_user(
        db, email="instructor-constraint@example.org", role="instructor"
    )
    student_id = _insert_user(db, email="student-constraint@example.org", role="student")
    db.commit()

    with pytest.raises(IntegrityError):
        db.execute(
            text("INSERT INTO student_profiles (user_id) VALUES (:id)"),
            {"id": instructor_id},
        )
        db.flush()
    db.rollback()

    with pytest.raises(IntegrityError):
        db.execute(
            text("INSERT INTO instructor_profiles (user_id) VALUES (:id)"),
            {"id": student_id},
        )
        db.flush()
    db.rollback()

    with pytest.raises(IntegrityError):
        db.execute(
            text("INSERT INTO company_profiles (user_id, company_name) VALUES (:id, 'X')"),
            {"id": student_id},
        )
        db.flush()
    db.rollback()

    # The matching profile is accepted.
    db.execute(
        text("INSERT INTO instructor_profiles (user_id) VALUES (:id)"), {"id": instructor_id}
    )
    db.execute(
        text("INSERT INTO student_profiles (user_id) VALUES (:id)"), {"id": student_id}
    )
    db.commit()
    db.execute(text("DELETE FROM users WHERE id = :id"), {"id": instructor_id})
    db.commit()
    assert (
        db.execute(
            text("SELECT count(*) FROM instructor_profiles WHERE user_id = :id"),
            {"id": instructor_id},
        ).scalar_one()
        == 0
    )


def test_session_expiry_check_and_token_uniqueness(db):
    user_id = _insert_user(db, email="session-constraint@example.org")
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(
            text(
                "INSERT INTO sessions (user_id, token_hash, created_at, expires_at) "
                "VALUES (:id, :hash, now(), now() - interval '1 hour')"
            ),
            {"id": user_id, "hash": "a" * 64},
        )
        db.flush()
    db.rollback()

    db.execute(
        text(
            "INSERT INTO sessions (user_id, token_hash, expires_at) "
            "VALUES (:id, :hash, now() + interval '1 hour')"
        ),
        {"id": user_id, "hash": "b" * 64},
    )
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(
            text(
                "INSERT INTO sessions (user_id, token_hash, expires_at) "
                "VALUES (:id, :hash, now() + interval '1 hour')"
            ),
            {"id": user_id, "hash": "b" * 64},
        )
        db.flush()
    db.rollback()


def test_audit_event_constraints(db):
    actor_id = _insert_user(db, email="actor-constraint@example.org", role="administrator")
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(
            text(
                "INSERT INTO audit_events "
                "(actor_id, action, target_id, old_status, new_status, reason) "
                "VALUES (:actor, 'company.verification_changed', :target, 'pending', "
                "'pending', 'reason')"
            ),
            {"actor": actor_id, "target": uuid.uuid4()},
        )
        db.flush()
    db.rollback()

    with pytest.raises(IntegrityError):
        db.execute(
            text(
                "INSERT INTO audit_events "
                "(actor_id, action, target_id, old_status, new_status, reason) "
                "VALUES (:actor, 'company.verification_changed', :target, 'pending', "
                "'verified', '')"
            ),
            {"actor": actor_id, "target": uuid.uuid4()},
        )
        db.flush()
    db.rollback()


def test_api_registration_rows_respect_constraints(client, db):
    register(client, email="api-constraint@example.org", role="student")
    row = db.execute(
        text("SELECT role FROM users WHERE email = 'api-constraint@example.org'")
    ).one()
    assert row.role == "student"
    count = db.execute(
        text(
            "SELECT count(*) FROM student_profiles sp JOIN users u ON u.id = sp.user_id "
            "WHERE u.email = 'api-constraint@example.org'"
        )
    ).scalar_one()
    assert count == 1

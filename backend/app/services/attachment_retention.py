"""FR05/07/11, NFR03/04/11: explicit, bounded, transactionally audited expiry."""
from datetime import timedelta

from sqlalchemy import and_, exists, func, or_, select, text
from sqlalchemy.orm import load_only

from app.models import Application, ApplicationStatusHistory, AttachmentRetentionEvent, Listing, User
from app.time_utils import iso_manila, utcnow
from app.validation import normalize_email


def validate_policy(retention_days, policy_reference, batch_size):
    if type(retention_days) is not int or not 1 <= retention_days <= 36500:
        raise ValueError("Retention days must be an explicit integer between 1 and 36500.")
    if type(batch_size) is not int or not 1 <= batch_size <= 100:
        raise ValueError("Batch size must be between 1 and 100.")
    if not isinstance(policy_reference, str):
        raise ValueError("An explicit policy reference is required.")
    policy = policy_reference.strip()
    if not 1 <= len(policy) <= 200 or any(ord(char) < 32 for char in policy):
        raise ValueError("Policy reference must contain 1–200 characters without control characters.")
    return policy


def eligible_files(cutoff, batch_size, *, lock=False):
    initial = and_(ApplicationStatusHistory.old_status.is_(None), ApplicationStatusHistory.new_status == "submitted")
    review = and_(ApplicationStatusHistory.old_status == "submitted", ApplicationStatusHistory.new_status == "under_review")
    accepted = and_(ApplicationStatusHistory.old_status == "under_review", ApplicationStatusHistory.new_status == "accepted")
    direct_rejection = and_(ApplicationStatusHistory.old_status == "submitted", ApplicationStatusHistory.new_status == "rejected")
    reviewed_rejection = and_(ApplicationStatusHistory.old_status == "under_review", ApplicationStatusHistory.new_status == "rejected")
    history = select(
        ApplicationStatusHistory.application_id,
        func.count().label("total_count"),
        func.max(ApplicationStatusHistory.created_at).label("latest_at"),
        func.count().filter(initial).label("initial_count"),
        func.min(ApplicationStatusHistory.created_at).filter(initial).label("initial_at"),
        func.count().filter(review).label("review_count"),
        func.min(ApplicationStatusHistory.created_at).filter(review).label("review_at"),
        func.count().filter(accepted).label("accepted_count"),
        func.count().filter(direct_rejection).label("direct_rejection_count"),
        func.count().filter(reviewed_rejection).label("reviewed_rejection_count"),
    ).group_by(ApplicationStatusHistory.application_id).subquery()
    final_record = exists(select(ApplicationStatusHistory.id).where(
        ApplicationStatusHistory.application_id == Application.id,
        ApplicationStatusHistory.new_status == Application.status,
        ApplicationStatusHistory.created_at == history.c.latest_at,
    ))
    valid_chain = or_(
        and_(Application.status == "accepted", history.c.total_count == 3,
             history.c.review_count == 1, history.c.accepted_count == 1,
             history.c.initial_at <= history.c.review_at, history.c.review_at <= history.c.latest_at),
        and_(Application.status == "rejected", history.c.total_count == 2,
             history.c.direct_rejection_count == 1, history.c.initial_at <= history.c.latest_at),
        and_(Application.status == "rejected", history.c.total_count == 3,
             history.c.review_count == 1, history.c.reviewed_rejection_count == 1,
             history.c.initial_at <= history.c.review_at, history.c.review_at <= history.c.latest_at),
    )
    query = select(Application, func.octet_length(Application.attachment).label("byte_count")).join(
        Listing, Listing.id == Application.listing_id
    ).join(history, history.c.application_id == Application.id).where(
        Listing.status == "closed", Application.status.in_(("accepted", "rejected")),
        Application.attachment_deleted_at.is_(None), Application.attachment.is_not(None),
        Application.created_at < cutoff, Listing.updated_at < cutoff,
        history.c.latest_at < cutoff, history.c.initial_count == 1,
        Application.created_at <= history.c.initial_at, valid_chain, final_record,
    ).options(load_only(Application.id, Application.attachment_deleted_at, raiseload=True)).order_by(Application.id).limit(batch_size)
    # Closed listings cannot be reopened/edited and final decisions cannot change
    # via the marketplace. Lock each application to serialize expiry execution.
    return query.with_for_update(of=Application, skip_locked=True) if lock else query


def run(db, *, retention_days, policy_reference, apply=False, confirm_expiry=False,
        actor_email=None, batch_size=100, now=None):
    """Use a fresh Session. Audit/byte changes commit together or all roll back."""
    policy = validate_policy(retention_days, policy_reference, batch_size)
    if type(apply) is not bool or type(confirm_expiry) is not bool:
        raise ValueError("Execution flags must be explicit booleans.")
    if apply and (not confirm_expiry or not actor_email):
        raise ValueError("Apply requires explicit confirmation and an administrator email.")
    when = now or utcnow()
    if when.tzinfo is None or when.utcoffset() is None:
        raise ValueError("Retention time must include a timezone.")
    cutoff = when - timedelta(days=retention_days)
    if db.in_transaction():
        raise ValueError("Use a fresh session for the retention transaction.")
    with db.begin():
        actor = None
        if not apply:
            db.execute(text("SET TRANSACTION READ ONLY"))
        else:
            # Scalar values bypass an older ORM identity-map role retained after
            # commit; authorization must use this transaction's current DB row.
            actor = db.execute(select(User.id, User.role).where(
                User.email == normalize_email(actor_email)
            ).with_for_update()).one_or_none()
            if actor is None or actor.role != "administrator":
                raise ValueError("A current administrator is required to execute expiry.")
        rows = list(db.execute(eligible_files(cutoff, batch_size, lock=apply)))
        total_bytes = sum(row.byte_count for row in rows)
        if apply:
            for application, byte_count in rows:
                application.attachment = None
                application.attachment_deleted_at = when
                application.attachment_name = "expired.pdf"
                db.add(AttachmentRetentionEvent(
                    application_id=application.id, actor_id=actor.id, created_at=when,
                    retention_days=retention_days, policy_reference=policy,
                    byte_count=byte_count,
                ))
            db.flush()
        result = dict(
            mode="applied" if apply else "dry_run", generated_at=iso_manila(when),
            cutoff=iso_manila(cutoff), retention_days=retention_days,
            batch_limit=batch_size, eligible_files=len(rows), eligible_bytes=total_bytes,
            expired_files=len(rows) if apply else 0,
            more_may_remain=len(rows) == batch_size,
        )
    return result

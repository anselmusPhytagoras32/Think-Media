"""NFR03/07: restore verification distinguishes bytes, tombstones and corruption."""
from datetime import datetime, timedelta, timezone
import pytest
from ops.backup import attachment_fingerprint
from ops.backup import restore_smoke


@pytest.fixture(autouse=True)
def clean_database():
    # Pure streaming fingerprint checks do not connect to a database.
    yield


def test_retained_bytes_and_tombstones_are_checked_not_only_row_counts():
    expired = datetime(2026, 11, 8, tzinfo=timezone.utc)
    rows = [('first', b'PDF-one', None), ('second', None, expired)]
    expected = attachment_fingerprint(iter(rows))
    assert expected == attachment_fingerprint(iter(rows))
    assert expected != attachment_fingerprint([('first', b'PDF-two', None), rows[1]])
    assert expected != attachment_fingerprint([rows[0], ('second', None, expired + timedelta(seconds=1))])
    assert expected != attachment_fingerprint([rows[0]])
    assert expected == attachment_fingerprint([rows[0], ('second', None, expired.astimezone(timezone(timedelta(hours=8))))])


@pytest.mark.parametrize('payload,deleted_at', [(None, None), (b'PDF', datetime.now(timezone.utc))])
def test_inconsistent_attachment_state_cannot_pass_restore_verification(payload, deleted_at):
    with pytest.raises(ValueError):
        attachment_fingerprint([('invalid', payload, deleted_at)])


def test_restore_refuses_arbitrary_database_names_before_connection():
    with pytest.raises(ValueError, match='existing databases are never targets'):
        restore_smoke(None, None, target_namespace='postgres')

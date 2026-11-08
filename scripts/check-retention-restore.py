"""NFR03/04/07: restore retained and expired synthetic files in fresh DBs only."""
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
PHASE = 'configuration'
sys.path.insert(0, str(ROOT / 'backend'))

from alembic import command
from alembic.config import Config
import psycopg
from psycopg import sql
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.config import Settings
from app.main import create_app
from app.services.attachment_retention import run
from ops.backup import private_dump, restore_smoke
from tests.helpers import create_admin
from tests.test_attachment_retention import fixture_application


def main():
    global PHASE
    raw = os.environ.get('TEST_DATABASE_URL', '')
    url = make_url(raw)
    if (os.environ.get('APP_ENV') != 'test' or url.get_backend_name() != 'postgresql'
            or url.host not in {'localhost', '127.0.0.1', '::1'} or url.query
            or not (url.database or '').endswith('_test')):
        raise ValueError('Use explicit loopback TEST_DATABASE_URL and APP_ENV=test.')
    run_id = uuid4().hex[:12]
    # Reuse the explicitly permitted disposable migration-test namespace.
    # Never widen pg_hba rules or alter database roles for verification.
    source_name = f'tm_migration_{run_id}'
    parameters = dict(host=url.host, port=url.port or 5432, user=url.username,
                      password=url.password, dbname='postgres')
    PHASE = 'create isolated source database'
    with psycopg.connect(**parameters, autocommit=True) as connection:
        connection.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(source_name)))
    source_url = url.set(database=source_name).render_as_string(hide_password=False)
    cfg = Config(str(ROOT / 'backend/alembic.ini'))
    cfg.set_main_option('script_location', str(ROOT / 'backend/alembic'))
    cfg.set_main_option('sqlalchemy.url', source_url)
    PHASE = 'migrate isolated source database'
    command.upgrade(cfg, 'head')
    PHASE = 'seed synthetic source'
    app = create_app(Settings(_env_file=None, app_env='test', database_url=source_url,
                              assistant_mode='disabled', allowed_origins='http://testserver'))
    clients = []
    try:
        administrator = 'synthetic-retention-restore-admin@example.test'
        create_admin(app, email=administrator)
        _, company_one, student_one, when = fixture_application(app)
        clients += [company_one, student_one]
        _, company_two, student_two, _ = fixture_application(app, final=None, close=False)
        clients += [company_two, student_two]
        with app.state.session_factory() as db:
            outcome = run(db, retention_days=30, policy_reference='Synthetic restore verification only; not an approved real-user policy',
                          apply=True, confirm_expiry=True, actor_email=administrator, now=when)
            assert outcome['expired_files'] == 1
        with app.state.engine.connect() as db:
            present = db.scalar(text('SELECT count(*) FROM applications WHERE attachment IS NOT NULL'))
            expired = db.scalar(text('SELECT count(*) FROM applications WHERE attachment_deleted_at IS NOT NULL'))
            assert present == expired == 1
    finally:
        for client in clients:
            client.close()
        app.state.engine.dispose()
    # Only the newly created fixture database is supplied to the backup utility.
    os.environ['DATABASE_URL'] = source_url
    dump_path = ROOT / '.local/retention-restore' / f'{run_id}.dump'
    pg_bin = Path(os.environ['PG_BIN'])
    PHASE = 'dump synthetic source'
    dumped = private_dump(dump_path, pg_bin)
    PHASE = 'restore and verify synthetic source'
    restored = restore_smoke(dump_path, pg_bin, target_namespace='migration_test')
    assert restored['attachment_states_match'] is True
    assert restored['row_counts']['attachment_retention_events'] == 1
    report = {
        'requirement': 'FR05/11; NFR03/04/07/11', 'synthetic_only': True,
        'source_database': source_name, 'retained_files': present, 'expired_files': expired,
        'dump_bytes': dumped['bytes'], 'dump_sha256': dumped['sha256'],
        'restore': restored,
        'limitations': ['New synthetic source and restored databases are preserved for inspection.',
                        'No presentation application or file was expired.',
                        'This verifies attachment state and audit restoration, not legal erasure of old backups.'],
    }
    target = ROOT / 'backend/reports/retention-restore-local.json'
    target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as failure:
        original = getattr(failure, 'orig', failure)
        message = str(original).splitlines()[0]
        try:
            configured = make_url(os.environ.get('TEST_DATABASE_URL', ''))
            if configured.password:
                message = message.replace(configured.password, '<REDACTED>')
        except Exception:
            message = 'Invalid configuration; values withheld.'
        print(f'Synthetic retention restore failed at {PHASE} ({type(failure).__name__}): {message[:240]}. Created artifacts are preserved.', file=sys.stderr)
        raise SystemExit(1) from None

"""FR01-12/NFR02/03/04/07: reset a local test workspace, retaining administrators.

Preview by default. --execute requires a successful private backup before any
deletion. Does not change schema, migrations, passwords or environment files.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.engine import make_url

from app.models import Base, User
from ops.backup import private_dump

ROOT = Path(__file__).resolve().parents[2]


def configuration():
    raw = os.environ.get('DATABASE_URL', '')
    if os.environ.get('APP_ENV', '').strip().lower() != 'local' or not raw:
        raise ValueError('Set APP_ENV=local and an explicit local DATABASE_URL.')
    try:
        url = make_url(raw)
    except Exception:
        raise ValueError('Use a valid local PostgreSQL URL.') from None
    if (url.get_backend_name() != 'postgresql'
            or url.host not in {'localhost', '127.0.0.1', '::1'}
            or not (url.database or '').endswith('_local') or url.query):
        raise ValueError('Reset requires loopback PostgreSQL ending in _local, without connection overrides.')
    return raw, url.database


def application_tables(connection):
    tables = list(Base.metadata.sorted_tables)
    actual = set(inspect(connection).get_table_names(schema='public'))
    expected = {table.name for table in tables} | {'alembic_version'}
    if actual != expected:
        raise ValueError('Schema differs from the application models; reset refused. Check migrations first.')
    return tables


def snapshot(connection, tables):
    return {table.name: connection.scalar(select(func.count()).select_from(table)) for table in tables}


def wipe(connection, tables):
    """Child-first deletion; caller owns the transaction and rollback."""
    removed = {}
    for table in reversed(tables):
        if table.name != 'users':
            removed[table.name] = connection.execute(table.delete()).rowcount
    removed['users'] = connection.execute(User.__table__.delete().where(User.role != 'administrator')).rowcount
    return removed


def backup_path():
    allowed = (ROOT / '.local').resolve()
    if not allowed.is_relative_to(ROOT.resolve()):
        raise ValueError('Local backup directory must stay inside the repository.')
    directory = (allowed / 'resets').resolve()
    if not directory.is_relative_to(allowed):
        raise ValueError('Reset backups must stay inside repository/.local.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    return directory / f'before-wipe-{stamp}-{uuid4().hex[:8]}.dump'


def run(*, execute=False):
    raw, database = configuration()
    engine = create_engine(raw, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            tables = application_tables(connection)
            if execute:
                # Freeze writes while taking the backup and deleting. Ordinary
                # SELECT and pg_dump's ACCESS SHARE locks remain compatible.
                quote = connection.dialect.identifier_preparer.quote
                names = ', '.join('public.' + quote(table.name) for table in tables)
                connection.execute(text("SET LOCAL lock_timeout = '5s'"))
                connection.execute(text('LOCK TABLE ' + names + ' IN EXCLUSIVE MODE'))
            else:
                connection.execute(text('SET TRANSACTION READ ONLY'))
            before = snapshot(connection, tables)
            admins = connection.scalar(select(func.count()).select_from(User).where(User.role == 'administrator'))
            report = {
                'mode': 'execute' if execute else 'preview', 'database': database,
                'before': before, 'administrators_preserved': admins,
                'non_administrator_accounts_to_remove': before['users'] - admins,
                'preserved': ['administrator accounts and passwords', 'database schema and migrations', '.env.local and API configuration'],
            }
            if execute:
                if not admins:
                    raise ValueError('No administrator exists; provision one before resetting this workspace.')
                pg_bin = os.environ.get('PG_BIN')
                if not pg_bin:
                    raise ValueError('Set PG_BIN to the local PostgreSQL tools directory for the mandatory backup.')
                report['backup'] = private_dump(backup_path(), Path(pg_bin))
                report['removed'] = wipe(connection, tables)
                report['after'] = snapshot(connection, tables)
                if report['after']['users'] != admins or any(
                    count for name, count in report['after'].items() if name != 'users'
                ):
                    raise ValueError('Reset verification failed; all database deletions will roll back.')
        return report
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Back up and delete all application data except administrator accounts.')
    args = parser.parse_args()
    try:
        print(json.dumps(run(execute=args.execute), indent=2))
    except ValueError as error:
        parser.exit(2, f'{error}\n')
    except Exception:
        parser.exit(1, 'Reset failed; database deletions were rolled back. Private error details withheld.\n')


if __name__ == '__main__':
    main()

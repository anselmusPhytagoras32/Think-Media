"""NFR07 local private backup/restore smoke; never overwrite/drop an existing DB.

Use DATABASE_URL in the environment. Only loopback PostgreSQL is permitted by
this local verification utility. Production operations require separate approval.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import uuid
import hashlib
from datetime import datetime, timezone
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url


def local_connection():
    raw=os.environ.get('DATABASE_URL','')
    if not raw: raise ValueError('Set DATABASE_URL explicitly to a local database.')
    url=make_url(raw)
    if not url.drivername.startswith('postgresql') or url.host not in {'localhost','127.0.0.1','::1'}:
        raise ValueError('This utility permits loopback PostgreSQL only.')
    if not url.database: raise ValueError('A source database is required.')
    return dict(host=url.host,port=url.port or 5432,user=url.username,password=url.password,dbname=url.database)


def private_dump(output:Path,pg_bin:Path):
    connection=local_connection()
    output.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    descriptor=os.open(output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    environment=os.environ.copy()
    environment.update(PGHOST=connection['host'],PGPORT=str(connection['port']),PGDATABASE=connection['dbname'])
    if connection['user']: environment['PGUSER']=connection['user']
    if connection['password']: environment['PGPASSWORD']=connection['password']
    try:
        with os.fdopen(descriptor,'wb') as stream:
            result=subprocess.run([str(pg_bin/'pg_dump'),'--format=custom','--no-owner','--no-acl'],stdout=stream,stderr=subprocess.PIPE,env=environment,check=False)
        if result.returncode: raise RuntimeError('pg_dump failed; inspect local database connectivity and permissions.')
        with output.open('rb') as source:
            digest=hashlib.file_digest(source,'sha256').hexdigest()
        return dict(backup=str(output),bytes=output.stat().st_size,sha256=digest,created_at=datetime.now(timezone.utc).isoformat())
    except Exception:
        # Preserve failed artifacts for inspection; never delete a user path.
        raise


def attachment_fingerprint(rows):
    """NFR03/07: hash retained bytes and expiry tombstones without logging either."""
    digest = hashlib.sha256()
    for identity, payload, deleted_at in rows:
        digest.update(str(identity).encode())
        if payload is None:
            if deleted_at is None:
                raise ValueError('A missing attachment requires an expiry tombstone.')
            digest.update(b'\x00expired\x00')
            digest.update(deleted_at.astimezone(timezone.utc).isoformat(timespec='microseconds').encode())
        else:
            if deleted_at is not None:
                raise ValueError('Retained attachment bytes cannot have an expiry tombstone.')
            digest.update(b'\x00retained\x00')
            digest.update(hashlib.sha256(payload).digest())
    return digest.hexdigest()


def restore_smoke(backup:Path,pg_bin:Path,*,target_namespace='backup'):
    if target_namespace not in {'backup','migration_test'}:
        raise ValueError('Restore namespace must be backup or migration_test; existing databases are never targets.')
    source=local_connection()
    target=('tm_restore_'+uuid.uuid4().hex[:16]) if target_namespace=='backup' else ('tm_migration_'+uuid.uuid4().hex[:12])
    admin={**source,'dbname':'postgres'}
    with psycopg.connect(**admin,autocommit=True) as connection:
        connection.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(target)))
    environment=os.environ.copy()
    environment.update(PGHOST=source['host'],PGPORT=str(source['port']),PGDATABASE=target)
    if source['user']: environment['PGUSER']=source['user']
    if source['password']: environment['PGPASSWORD']=source['password']
    result=subprocess.run([str(pg_bin/'pg_restore'),'--no-owner','--no-acl','--exit-on-error','--single-transaction','--dbname',target,str(backup)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=environment,check=False)
    if result.returncode: raise RuntimeError(f'Restore failed in fresh database {target}; it has been preserved for inspection.')
    # Read-only verification of schema version and every public-table row count.
    def snapshot(parameters):
        with psycopg.connect(**parameters) as connection:
            tables=connection.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").fetchall()
            counts={name:connection.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(name))).fetchone()[0] for (name,) in tables}
            version=connection.execute('SELECT version_num FROM alembic_version').fetchone()[0]
            # Keep backup compatibility with databases predating retention.
            has_expiry=connection.execute("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='applications' AND column_name='attachment_deleted_at')").fetchone()[0]
            with connection.cursor(name='restore_attachment_verification') as cursor:
                expiry_column='attachment_deleted_at' if has_expiry else 'NULL::timestamptz'
                cursor.execute(f'SELECT id, attachment, {expiry_column} FROM applications ORDER BY id')
                fingerprint=attachment_fingerprint(iter(cursor.fetchone,None))
            return dict(version=version,rows=counts,attachment_fingerprint=fingerprint,attachment_fingerprint_format='retained-and-expired-v2')
    expected=snapshot(source); actual=snapshot({**source,'dbname':target})
    if expected!=actual: raise RuntimeError(f'Restored schema/row counts differ in fresh database {target}; ensure the source is quiescent.')
    return dict(restored_database=target,schema_version=actual['version'],tables=len(actual['rows']),row_counts=actual['rows'],source_counts_match=True,private_attachment_bytes_match=True,attachment_states_match=True,attachment_fingerprint_format=actual['attachment_fingerprint_format'],cleanup='Fresh database preserved; no existing resource was overwritten or dropped.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pg-bin',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--restore-smoke',action='store_true')
    args=parser.parse_args()
    report=private_dump(args.output,args.pg_bin)
    if args.restore_smoke: report.update(restore_smoke(args.output,args.pg_bin))
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()

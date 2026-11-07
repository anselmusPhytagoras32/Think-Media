"""NFR01/07: local-only benchmarks and private, non-overwriting backups."""
import os
from pathlib import Path
import pytest
from ops.backup import local_connection, private_dump
from ops.benchmark import p95, run

def test_ops_refuse_nonlocal_targets(monkeypatch):
    monkeypatch.setenv('DATABASE_URL','postgresql+psycopg://test@remote.example/thinkmedia_dev')
    with pytest.raises(ValueError,match='loopback'):local_connection()
    monkeypatch.setenv('DATABASE_URL','postgresql+psycopg://test@localhost:55433/thinkmedia_dev')
    with pytest.raises(ValueError,match='loopback'):run('https://remote.example',20,200)
    with pytest.raises(ValueError,match='multiple'):run('http://localhost:8000',20,21)

def test_backup_never_overwrites_existing_file(tmp_path,monkeypatch):
    monkeypatch.setenv('DATABASE_URL','postgresql+psycopg://test@localhost:55433/thinkmedia_dev')
    target=tmp_path/'existing.dump';target.write_bytes(b'preserve existing data')
    with pytest.raises(FileExistsError):private_dump(target,Path('/missing/pg-tools'))
    assert target.read_bytes()==b'preserve existing data'

def test_nearest_rank_p95_uses_the_whole_sample():
    assert p95(list(range(1,101)))==95
    assert p95([]) is None

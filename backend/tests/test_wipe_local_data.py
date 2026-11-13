"""FR01-12/NFR02/03/04/07: reset must preserve admin access and be atomic."""
import pytest
from sqlalchemy import select, text

from app.models import Base, User
from ops import wipe_local_data as reset
from tests.test_learning import administrator, create_content, learner
from tests.test_marketplace import company, listing, upload


@pytest.mark.parametrize('app_env,url', [
    ('production', 'postgresql+psycopg://localhost/app_local'),
    ('', 'postgresql+psycopg://localhost/app_local'),
    ('local', ''),
    ('local', 'postgresql+psycopg://remote.example/app_local'),
    ('local', 'postgresql+psycopg://localhost/app_test'),
    ('local', 'postgresql+psycopg://localhost/postgres'),
    ('local', 'postgresql+psycopg://localhost/app_local?host=remote.example'),
])
def test_reset_refuses_unsafe_targets(monkeypatch, app_env, url):
    monkeypatch.setenv('APP_ENV', app_env)
    monkeypatch.setenv('DATABASE_URL', url)
    with pytest.raises(ValueError):
        reset.configuration()


@pytest.fixture()
def populated(app, monkeypatch, database_url, tmp_path):
    admin = administrator(app)
    resource = create_content(admin)
    student = learner(app)
    recruiter = company(app)
    job = listing(recruiter)
    receipt = upload(student, job['id'])
    assert receipt.status_code == 201
    monkeypatch.setattr(reset, 'configuration', lambda: (database_url, 'isolated_reset_test'))
    monkeypatch.setattr(reset, 'backup_path', lambda: tmp_path / 'private.dump')
    monkeypatch.setenv('PG_BIN', '/unused/injected-backup')
    return app, admin, student, resource


def test_preview_is_read_only(populated):
    app, admin, student, _ = populated
    report = reset.run()
    assert report['mode'] == 'preview'
    assert report['before']['applications'] == 1
    assert student.get('/api/v1/applications/me').json()['total'] == 1
    assert admin.get('/api/v1/auth/me').status_code == 200


def test_execute_clears_every_table_except_admin_and_migrations(populated, monkeypatch):
    app, admin, student, _ = populated
    with app.state.engine.connect() as connection:
        before_admin = connection.execute(select(User.__table__).where(User.role == 'administrator')).mappings().all()
        migration = connection.scalar(text('SELECT version_num FROM alembic_version'))
    called = []
    def backup(path, pg_bin):
        called.append(path)
        return {'backup': str(path), 'bytes': 123, 'sha256': 'test-only'}
    monkeypatch.setattr(reset, 'private_dump', backup)
    report = reset.run(execute=True)
    assert called and report['after']['users'] == 1
    assert all(count == 0 for name, count in report['after'].items() if name != 'users')
    with app.state.engine.connect() as connection:
        after_admin = connection.execute(select(User.__table__).where(User.role == 'administrator')).mappings().all()
        assert before_admin == after_admin
        assert connection.scalar(text('SELECT version_num FROM alembic_version')) == migration
    assert student.get('/api/v1/auth/me').status_code == 401
    assert admin.get('/api/v1/auth/me').status_code == 401  # sessions are reset too
    from tests.helpers import login_admin
    assert login_admin(admin).status_code == 200
    assert admin.get('/api/v1/admin/companies').json()['total'] == 0
    assert reset.run(execute=True)['removed']['users'] == 0  # idempotent


def test_failed_backup_prevents_all_deletion(populated, monkeypatch):
    before = reset.run()['before']
    def failed(*args):
        raise RuntimeError('backup unavailable')
    monkeypatch.setattr(reset, 'private_dump', failed)
    with pytest.raises(RuntimeError):
        reset.run(execute=True)
    assert reset.run()['before'] == before


def test_partial_deletion_rolls_back_atomically(populated, monkeypatch):
    before = reset.run()['before']
    monkeypatch.setattr(reset, 'private_dump', lambda *args: {})
    def failed(connection, tables):
        connection.execute(Base.metadata.tables['sessions'].delete())
        raise RuntimeError('injected deletion failure')
    monkeypatch.setattr(reset, 'wipe', failed)
    with pytest.raises(RuntimeError):
        reset.run(execute=True)
    assert reset.run()['before'] == before

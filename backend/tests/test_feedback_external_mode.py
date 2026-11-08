"""FR10/12, NFR03/04/08: external-mode CSAT persists without provider calls."""
import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text

from app.main import create_app
from app.models.feedback import SatisfactionFeedback
from tests.conftest import alembic_config
from tests.helpers import post_json, register_and_login


def external_feedback(settings):
    app = create_app(settings.model_copy(update={'assistant_mode': 'external'}))
    try:
        with TestClient(app) as client:
            register_and_login(client, email='synthetic-external-csat@example.test', role='student')
            response = post_json(client, '/api/v1/feedback/csat', {'rating': 4})
            assert response.status_code == 200, response.text
            assert app.state.assistant_provider.calls_used == 0
            assert post_json(client, '/api/v1/feedback/csat', {'rating': 5, 'mode': 'retrieval'}).status_code == 422
        with app.state.session_factory() as db:
            row = db.scalar(select(SatisfactionFeedback))
            assert row.rating == 4 and row.mode == 'external'
    finally:
        app.state.engine.dispose()


def test_external_mode_feedback_does_not_break_when_gemini_is_enabled(settings):
    external_feedback(settings)


def test_feedback_downgrade_refuses_to_reclassify_external_observations(settings, database_url):
    external_feedback(settings)
    with pytest.raises(RuntimeError, match='external-mode satisfaction feedback'):
        command.downgrade(alembic_config(database_url), '0007_attachment_retention')
    engine = create_engine(database_url)
    try:
        with engine.connect() as db:
            assert db.scalar(text('SELECT version_num FROM alembic_version')) == '0008_feedback_external_mode'
            assert db.scalar(text("SELECT count(*) FROM satisfaction_feedback WHERE mode='external'")) == 1
    finally:
        engine.dispose()

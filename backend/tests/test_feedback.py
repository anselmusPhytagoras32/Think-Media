"""FR12 explicit real feedback, never manufactured from other interactions."""
from fastapi.testclient import TestClient
from sqlalchemy import select,func
from app.models.feedback import SatisfactionFeedback
from tests.helpers import register_and_login,post_json

def test_csat_requires_auth_strict_rating_and_server_derived_actor(app):
    anonymous=TestClient(app)
    assert post_json(anonymous,'/api/v1/feedback/csat',{'rating':5}).status_code==401
    learner=TestClient(app);register_and_login(learner,email='csat@example.test',role='student')
    for payload in ({'rating':0},{'rating':6},{'rating':True},{'rating':'5'},{'rating':5,'user_id':'someone-else'}):
        assert post_json(learner,'/api/v1/feedback/csat',payload).status_code==422
    assert post_json(learner,'/api/v1/feedback/csat',{'rating':4}).status_code==200
    assert post_json(learner,'/api/v1/feedback/csat',{'rating':5}).status_code==200
    with app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(SatisfactionFeedback))==1
        row=db.scalar(select(SatisfactionFeedback));assert row.rating==5 and row.mode=='disabled'

"""FR04–07 / NFR02–04,11 real PostgreSQL workflow and isolation checks."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import func, select, text

from app.models import Application, ApplicationStatusHistory, CompanyProfile, Listing, MarketplaceEvent
from app.repositories.marketplace import MarketplaceRepository
from tests.helpers import create_admin, login_admin, csrf_headers, get_company_id, get_csrf, patch_json, post_json, register_and_login

PDF = b'%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF\n'
DETAILS = dict(title='Web development OJT', description='Build accessible websites.', requirements='Submit a resume PDF.', location='Legazpi City', type='ojt', skills=['React', 'Python'])


def company(app, email='company@example.test', verified=True):
    client = TestClient(app)
    register_and_login(client, email=email, role='company', company_name='Synthetic Test Company')
    if verified:
        with app.state.session_factory() as db:
            row = db.get(CompanyProfile, get_company_id(app, email))
            row.verification_status = 'verified'
            db.commit()
    return client


def student(app, email='student@example.test', role='student'):
    client = TestClient(app)
    register_and_login(client, email=email, role=role)
    return client


def listing(company_client, publish=True):
    response = post_json(company_client, '/api/v1/company/listings', DETAILS)
    assert response.status_code == 201, response.text
    row = response.json()
    if publish:
        response = post_json(company_client, f'/api/v1/company/listings/{row["id"]}/publish')
        assert response.status_code == 200, response.text
        row = response.json()
    return row


def upload(client, listing_id, *, data=PDF, name='resume.pdf', mime='application/pdf', headers=None):
    headers = headers or csrf_headers(get_csrf(client))
    return client.post(f'/api/v1/listings/{listing_id}/applications', files={'file': (name, data, mime)}, data={'cover_letter': 'I would like to apply.'}, headers=headers)


def test_verified_company_student_review_workflow(app):
    recruiter = company(app)
    learner = student(app)
    draft = listing(recruiter, publish=False)
    assert learner.get('/api/v1/listings').json()['total'] == 0
    assert learner.get(f'/api/v1/listings/{draft["id"]}').status_code in (403, 404)
    assert recruiter.get(f'/api/v1/listings/{draft["id"]}').status_code == 200
    edited = patch_json(recruiter, f'/api/v1/company/listings/{draft["id"]}', {'title': 'Accessible web OJT'})
    assert edited.status_code == 200, edited.text
    assert post_json(recruiter, f'/api/v1/company/listings/{draft["id"]}/publish').status_code == 200
    found = learner.get('/api/v1/listings?q=Accessible&location=Legazpi&type=ojt&skill=React').json()
    assert found['total'] == 1
    public = found['items'][0]
    assert public['company_name'] == 'Synthetic Test Company'
    assert 'contact_email' not in public and 'contact_phone' not in public
    assert 'company_description' in public and 'company_website' in public
    assert learner.get('/api/v1/listings?q=unmatched').json()['total'] == 0
    assert learner.get('/api/v1/listings?limit=101').status_code == 422
    receipt = upload(learner, draft['id'])
    assert receipt.status_code == 201, receipt.text
    record = receipt.json()
    assert record['reference'].startswith('TM-') and record['status'] == 'submitted'
    assert [h['new_status'] for h in record['history']] == ['submitted']
    assert record['history'][0]['old_status'] is None
    assert 'student_profile' not in record and 'attachment' not in record
    assert learner.get('/api/v1/applications/me').json()['total'] == 1
    own = recruiter.get('/api/v1/company/applications').json()
    assert own['total'] == 1
    assert set(own['items'][0]['student_profile']) == {'display_name','institution','program','skills','interests','location','background'}
    for status in ('under_review', 'accepted'):
        response = patch_json(recruiter, f'/api/v1/applications/{record["id"]}/status', {'status': status})
        assert response.status_code == 200, response.text
    tracker = learner.get(f'/api/v1/applications/{record["id"]}').json()
    assert tracker['status'] == 'accepted'
    assert [h['new_status'] for h in tracker['history']] == ['submitted','under_review','accepted']
    assert all(h['actor_id'] and h['created_at'].endswith('+08:00') for h in tracker['history'])
    for actor in (learner, recruiter):
        download = actor.get(f'/api/v1/applications/{record["id"]}/attachment')
        assert download.status_code == 200 and download.content == PDF
        assert download.headers['Cache-Control'] == 'no-store'
        assert download.headers['X-Content-Type-Options'] == 'nosniff'
    assert post_json(recruiter, f'/api/v1/company/listings/{draft["id"]}/close').status_code == 200
    assert learner.get('/api/v1/listings').json()['total'] == 0
    assert learner.get(f'/api/v1/applications/{record["id"]}').json()['status'] == 'accepted'
    with app.state.session_factory() as db:
        events = list(db.scalars(select(MarketplaceEvent).where(MarketplaceEvent.listing_id == UUID(draft['id'])).order_by(MarketplaceEvent.created_at)))
        assert [e.action for e in events] == ['created', 'edited', 'published', 'closed']


def test_unverified_wrong_role_and_unauthenticated_writes_denied(app):
    pending = company(app, verified=False)
    assert post_json(pending, '/api/v1/company/listings', DETAILS).status_code == 403
    learner = student(app)
    assert post_json(learner, '/api/v1/company/listings', DETAILS).status_code == 403
    assert TestClient(app).get('/api/v1/listings').status_code == 401
    recruiter = company(app, email='verified@example.test')
    row = listing(recruiter)
    assert upload(recruiter, row['id']).status_code == 403
    teacher = student(app, email='teacher@example.test', role='instructor')
    assert upload(teacher, row['id']).status_code == 403
    assert teacher.get('/api/v1/applications/me').status_code == 403
    # Re-check stored verification before every write and public read.
    with app.state.session_factory() as db:
        db.get(CompanyProfile, get_company_id(app, 'verified@example.test')).verification_status = 'rejected'
        db.commit()
    assert patch_json(recruiter, f'/api/v1/company/listings/{row["id"]}', {'title':'Changed'}).status_code == 403
    assert learner.get('/api/v1/listings').json()['total'] == 0
    assert learner.get(f'/api/v1/listings/{row["id"]}').status_code == 404


def test_cross_tenant_application_and_listing_access_is_denied(app):
    recruiter = company(app)
    other_company = company(app, email='other-company@example.test')
    learner = student(app)
    other_student = student(app, email='other-student@example.test')
    teacher = student(app, email='teacher@example.test', role='instructor')
    administrator = TestClient(app)
    create_admin(app)
    login_admin(administrator)
    row = listing(recruiter)
    receipt = upload(learner, row['id']).json()
    for actor in (other_company, other_student, teacher, administrator):
        assert actor.get(f'/api/v1/applications/{receipt["id"]}').status_code in (403,404)
        assert actor.get(f'/api/v1/applications/{receipt["id"]}/attachment').status_code in (403,404)
        assert patch_json(actor, f'/api/v1/applications/{receipt["id"]}/status', {'status':'rejected'}).status_code in (403,404)
    assert other_company.get('/api/v1/company/applications').json()['total'] == 0
    assert other_student.get('/api/v1/applications/me').json()['total'] == 0
    assert patch_json(other_company, f'/api/v1/company/listings/{row["id"]}', {'title':'Stolen'}).status_code == 404
    assert post_json(other_company, f'/api/v1/company/listings/{row["id"]}/close').status_code == 404
    assert other_company.get(f'/api/v1/company/applications?listing_id={row["id"]}').status_code == 404
    assert patch_json(learner, f'/api/v1/applications/{receipt["id"]}/status', {'status':'accepted'}).status_code == 403


def test_duplicate_closed_and_final_transitions_preserve_records(app):
    recruiter = company(app)
    learner = student(app)
    row = listing(recruiter)
    receipt = upload(learner, row['id']).json()
    duplicate = upload(learner, row['id'])
    assert duplicate.status_code == 409 and duplicate.json()['error']['code'] == 'DUPLICATE_APPLICATION'
    assert patch_json(recruiter, f'/api/v1/applications/{receipt["id"]}/status', {'status':'accepted'}).status_code == 409
    rejected = patch_json(recruiter, f'/api/v1/applications/{receipt["id"]}/status', {'status':'rejected'})
    assert rejected.status_code == 200
    assert patch_json(recruiter, f'/api/v1/applications/{receipt["id"]}/status', {'status':'under_review'}).status_code == 409
    assert post_json(recruiter, f'/api/v1/company/listings/{row["id"]}/publish').status_code == 409
    assert post_json(recruiter, f'/api/v1/company/listings/{row["id"]}/close').status_code == 200
    assert patch_json(recruiter, f'/api/v1/company/listings/{row["id"]}', {'title':'Reopen'}).status_code == 409
    assert post_json(recruiter, f'/api/v1/company/listings/{row["id"]}/publish').status_code == 409
    new_student = student(app, email='late@example.test')
    assert upload(new_student, row['id']).status_code == 409
    with app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Application)) == 1
        assert db.scalar(select(func.count()).select_from(ApplicationStatusHistory)) == 2


def test_invalid_upload_and_request_bounds_create_no_application(app):
    recruiter = company(app)
    learner = student(app)
    row = listing(recruiter)
    for data,name,mime in ((b'not a PDF','resume.pdf','application/pdf'),(PDF,'resume.exe','application/pdf'),(PDF,'resume.pdf','text/plain'),(b'%PDF-1.4\nmissing trailer','resume.pdf','application/pdf')):
        response = upload(learner,row['id'],data=data,name=name,mime=mime)
        assert response.status_code == 422, response.text
    missing = learner.post(f'/api/v1/listings/{row["id"]}/applications', data={'cover_letter':'No file'}, headers=csrf_headers(get_csrf(learner)))
    assert missing.status_code == 422
    oversized = upload(learner,row['id'],data=b'%PDF-1.4\n'+b'x'*(5*1024*1024)+b'%%EOF')
    assert oversized.status_code == 413
    envelope = learner.post(f'/api/v1/listings/{row["id"]}/applications',content=iter([b'x'*(3*1024*1024),b'x'*(3*1024*1024+1)]),headers={'Content-Type':'application/octet-stream'})
    assert envelope.status_code == 413
    assert learner.get('/api/v1/applications/me').json()['total'] == 0
    # Upload endpoint alone receives the larger multipart cap.
    assert post_json(recruiter,'/api/v1/company/listings',{**DETAILS,'description':'x'*(65*1024)}).status_code == 413


def test_application_and_decision_roll_back_when_history_insert_fails(app, monkeypatch):
    recruiter = company(app)
    learner = student(app)
    row = listing(recruiter)
    original = MarketplaceRepository.add_history
    def fail_history(self, record, actor, old):
        raise RuntimeError('injected status-history failure')
    monkeypatch.setattr(MarketplaceRepository,'add_history',fail_history)
    probe = TestClient(app,raise_server_exceptions=False)
    probe.cookies.update(learner.cookies)
    failed = upload(probe,row['id'])
    assert failed.status_code == 500
    with app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Application)) == 0
        assert db.scalar(select(func.count()).select_from(ApplicationStatusHistory)) == 0
    monkeypatch.setattr(MarketplaceRepository,'add_history',original)
    receipt = upload(learner,row['id']).json()
    monkeypatch.setattr(MarketplaceRepository,'add_history',fail_history)
    probe.cookies.clear(); probe.cookies.update(recruiter.cookies)
    failed = patch_json(probe,f'/api/v1/applications/{receipt["id"]}/status',{'status':'under_review'})
    assert failed.status_code == 500
    current = learner.get(f'/api/v1/applications/{receipt["id"]}').json()
    assert current['status'] == 'submitted' and len(current['history']) == 1


def test_nonduplicate_integrity_failure_is_not_mislabeled(app,monkeypatch):
    recruiter = company(app)
    learner = student(app)
    row = listing(recruiter)
    def invalid_history(self,record,actor,old):
        self.db.execute(text("INSERT INTO application_status_history (id, application_id, actor_id, new_status, created_at) VALUES (gen_random_uuid(), :application_id, :actor_id, 'invalid', now())"),{'application_id':record.id,'actor_id':actor.id})
    monkeypatch.setattr(MarketplaceRepository,'add_history',invalid_history)
    probe = TestClient(app,raise_server_exceptions=False); probe.cookies.update(learner.cookies)
    failed = upload(probe,row['id'])
    assert failed.status_code == 500
    assert failed.json()['error']['code'] == 'INTERNAL_ERROR'
    assert learner.get('/api/v1/applications/me').json()['total'] == 0


def test_concurrent_duplicate_submission_has_exactly_one_winner(app):
    recruiter = company(app)
    learner = student(app)
    row = listing(recruiter)
    gate = Barrier(2)
    clients = [TestClient(app), TestClient(app)]
    for actor in clients: actor.cookies.update(learner.cookies)
    headers = [csrf_headers(get_csrf(actor)) for actor in clients]
    def attempt(index):
        gate.wait(timeout=10)
        return upload(clients[index],row['id'],headers=headers[index]).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, range(2)))
    assert sorted(results) == [201,409]
    with app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Application)) == 1
        assert db.scalar(select(func.count()).select_from(ApplicationStatusHistory)) == 1


def test_close_and_submission_serialize_without_orphans(app):
    recruiter = company(app)
    learner = student(app)
    row = listing(recruiter)
    gate = Barrier(2)
    headers = csrf_headers(get_csrf(learner))
    def submit():
        gate.wait(timeout=10)
        return upload(learner,row['id'],headers=headers).status_code
    def close():
        token = get_csrf(recruiter)
        gate.wait(timeout=10)
        return post_json(recruiter,f'/api/v1/company/listings/{row["id"]}/close',token=token).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        submitted = pool.submit(submit); closed = pool.submit(close)
        submit_status,close_status = submitted.result(timeout=20),closed.result(timeout=20)
    assert close_status == 200 and submit_status in (201,409)
    with app.state.session_factory() as db:
        assert db.get(Listing,UUID(row['id'])).status == 'closed'
        expected = int(submit_status == 201)
        assert db.scalar(select(func.count()).select_from(Application)) == expected
        assert db.scalar(select(func.count()).select_from(ApplicationStatusHistory)) == expected

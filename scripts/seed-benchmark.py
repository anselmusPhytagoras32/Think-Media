"""NFR01: add clearly synthetic listings/resources to the isolated benchmark DB."""
import os
from pathlib import Path
import secrets
import sys
from uuid import UUID, uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from sqlalchemy.engine import make_url
from app.config import Settings
from app.db import build_engine, build_session_factory
from app.repositories import UserRepository, ProfileRepository
from app.schemas import RegisterRequest
from app.schemas.learning import ContentInput, ContentPatch
from app.schemas.marketplace import ListingInput
from app.services.accounts import AccountService
from app.services.administration import AdministrationService
from app.services.learning import LearningService
from app.services.marketplace import MarketplaceService

url = make_url(os.environ.get('DATABASE_URL', ''))
if os.environ.get('APP_ENV') != 'test' or url.host not in {'localhost', '127.0.0.1', '::1'} or url.query or not (url.database or '').endswith('_test'):
    raise SystemExit('Only an explicit loopback disposable test database is permitted.')
engine = build_engine(Settings())
prefix = uuid4().hex[:12]
try:
    with build_session_factory(engine)() as db:
        accounts = AccountService(db)
        admin = accounts.create_administrator(email=f'benchmark-admin-{prefix}@example.test', password=secrets.token_urlsafe(24), display_name='Synthetic Benchmark Administrator')
        company_result = accounts.register(RegisterRequest(
            email=f'benchmark-company-{prefix}@example.test', password=secrets.token_urlsafe(24),
            display_name='Synthetic Benchmark Company', role='company', company_name='Synthetic Benchmark Studio',
        ))
        company = UserRepository(db).get_by_id(company_result.user.id)
        profile = ProfileRepository(db).get_company_by_user_id(company.id)
        AdministrationService(db).change_verification(company_id=profile.id, new_status='verified',
            reason='Synthetic isolated benchmark fixture only; no real company.',
            expected_version=profile.verification_version, actor=admin)
        marketplace = MarketplaceService(db, company)
        learning = LearningService(db, admin)
        for index in range(10):
            listing = marketplace.create_listing(ListingInput(
                title=f'Synthetic benchmark React Python OJT {prefix}-{index}', type='ojt',
                location='Metro Manila', skills=['Python', 'React'],
                description='Synthetic benchmark fixture. Practice web development with Python and React.',
                requirements='Fictional listing. No real vacancy, applicants or employment offer.',
            ))
            marketplace.transition_listing(UUID(listing['id']), 'published')
            resource = learning.create(ContentInput(
                title=f'Synthetic benchmark web development guide {prefix}-{index}',
                summary='Fictional Python and React preparation material for timing requests.',
                body='Use Python and React for a synthetic web development exercise. No real participants or research claims.',
                tags=['Python', 'React'],
            ))
            learning.edit(UUID(resource['id']), ContentPatch(status='published'))
finally:
    engine.dispose()
print('Added 10 synthetic listings and 10 synthetic published resources to the disposable benchmark database.')

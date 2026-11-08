"""FR01/02/11: verify synthetic role logins without printing credentials."""
import json
from pathlib import Path
import sys

import httpx

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / '.local/presentation/presentation-accounts.private.json').read_text())
if manifest.get('synthetic_only') is not True:
    raise SystemExit('Only the synthetic presentation manifest may be checked.')
results = []
for role, account in manifest['accounts'].items():
    try:
        with httpx.Client(base_url='http://127.0.0.1:8000/api/v1', timeout=10,
                          trust_env=False, follow_redirects=False,
                          headers={'Origin': 'http://127.0.0.1:5173'}) as client:
            bootstrap = client.get('/auth/csrf')
            bootstrap.raise_for_status()
            login = client.post('/auth/login', json={
                'email': account['email'], 'password': account['password'],
            }, headers={'X-CSRF-Token': bootstrap.json()['csrf_token']})
            login.raise_for_status()
            user = login.json()['user']
            if user['role'] != role or user['id'] != account['id']:
                raise ValueError('Role or ownership mismatch.')
            csrf = client.get('/auth/csrf')
            csrf.raise_for_status()
            logout = client.post('/auth/logout', headers={'X-CSRF-Token': csrf.json()['csrf_token']})
            logout.raise_for_status()
            results.append({'role': role, 'login': login.status_code, 'logout': logout.status_code})
    except Exception:
        print(f'Synthetic {role} login check failed; response and credentials withheld.', file=sys.stderr)
        raise SystemExit(1) from None
print(json.dumps({'synthetic_only': True, 'checks': results}, indent=2))

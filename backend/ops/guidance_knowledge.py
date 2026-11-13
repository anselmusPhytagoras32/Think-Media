"""FR03/10/11: publish useful editorial guides through the local admin API.

Dry run by default. Never creates accounts, listings, interactions or feedback,
and never overwrites existing content. Uses the ignored local operator manifest.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from app.schemas.learning import ContentInput

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ('title', 'summary', 'body', 'tags', 'status')


def local_api(value):
    url = urlsplit(value)
    if (url.scheme != 'http' or url.hostname not in {'localhost', '127.0.0.1'}
            or url.port != 8000 or url.username or url.password or url.path not in {'', '/'}
            or url.query or url.fragment):
        raise ValueError('Use the local presentation API at http://127.0.0.1:8000.')
    return value.rstrip('/') + '/api/v1'


def resources():
    rows = []
    for file in sorted((ROOT / 'backend/knowledge').glob('*.json')):
        for record in json.loads(file.read_text(encoding='utf-8')):
            content = ContentInput(**{key: record[key] for key in ('title', 'summary', 'body', 'tags')}, status='published')
            rows.append((record['slug'], content.model_dump(exclude={'questions'})))
    assert len(rows) == len({slug for slug, _ in rows}), 'Duplicate resource slug.'
    assert len(rows) == len({row['title'] for _, row in rows}), 'Duplicate resource title.'
    return rows


def publish(client, rows):
    def post(path, payload):
        csrf = client.get('/auth/csrf')
        csrf.raise_for_status()
        result = client.post(path, json=payload, headers={'X-CSRF-Token': csrf.json()['csrf_token']})
        result.raise_for_status()
        return result

    outcomes = []
    for slug, payload in rows:
        # Inspect all exact matches before any write; a changed resource belongs
        # to its editor and must never be silently restored by this importer.
        offset, matches = 0, []
        while True:
            result = client.get('/admin/content', params={'q': payload['title'], 'limit': 100, 'offset': offset})
            result.raise_for_status()
            page = result.json()
            matches.extend(item for item in page['items'] if item['title'] == payload['title'])
            offset += len(page['items'])
            if offset >= page['total'] or not page['items']:
                break
        if matches:
            unchanged = len(matches) == 1 and all(matches[0][key] == payload[key] for key in FIELDS)
            outcomes.append({'slug': slug, 'action': 'unchanged' if unchanged else 'preserved_editor_changes', 'id': matches[0]['id']})
        else:
            created = post('/admin/content', payload).json()
            outcomes.append({'slug': slug, 'action': 'published', 'id': created['id']})
    return outcomes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--api', default='http://127.0.0.1:8000')
    parser.add_argument('--manifest', type=Path, default=ROOT / '.local/presentation/presentation-accounts.private.json')
    args = parser.parse_args()
    base = local_api(args.api)
    rows = resources()
    if not args.publish:
        print(json.dumps({'dry_run': True, 'resources': [{'slug': slug, 'title': row['title']} for slug, row in rows]}, ensure_ascii=False))
        return
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    if manifest.get('synthetic_only') is not True:
        raise ValueError('Use the existing local presentation operator manifest.')
    credentials = manifest['accounts']['administrator']
    with httpx.Client(base_url=base, timeout=15, trust_env=False,
                      headers={'Origin': 'http://127.0.0.1:5173'}) as client:
        csrf = client.get('/auth/csrf')
        csrf.raise_for_status()
        login = client.post('/auth/login', json={key: credentials[key] for key in ('email', 'password')},
                            headers={'X-CSRF-Token': csrf.json()['csrf_token']})
        login.raise_for_status()
        try:
            identity = client.get('/auth/me')
            identity.raise_for_status()
            assert identity.json()['user']['role'] == 'administrator'
            print(json.dumps({'resources': publish(client, rows)}, ensure_ascii=False))
        finally:
            csrf = client.get('/auth/csrf')
            if csrf.is_success:
                client.post('/auth/logout', headers={'X-CSRF-Token': csrf.json()['csrf_token']})


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Do not expose request bodies, manifest credentials or private URLs.
        raise SystemExit(f'Knowledge publication failed ({type(error).__name__}); private details withheld.') from None

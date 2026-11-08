"""NFR01 reproducible local benchmark with 20 distinct synthetic student users.

Only explicit loopback development/test databases and HTTP targets are accepted.
Creates local synthetic actors; it never emails, removes data or targets production.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import platform
import secrets
from threading import Barrier
from time import perf_counter
import uuid
from urllib.parse import urlparse
import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from app.schemas import RegisterRequest
from app.services.accounts import AccountService

PATHS=('/profiles/me','/listings?limit=20','/content?limit=20','/recommendations?limit=10')

def p95(values):
    return sorted(values)[max(0,math.ceil(.95*len(values))-1)] if values else None

def run(base_url,concurrency,requests):
    target=urlparse(base_url)
    raw=os.environ.get('DATABASE_URL','')
    database=make_url(raw) if raw else None
    if target.scheme!='http' or target.hostname not in {'127.0.0.1','localhost','::1'}:
        raise ValueError('Benchmark target must be local loopback HTTP.')
    if database is None or database.host not in {'127.0.0.1','localhost','::1'} or not database.database or not database.database.endswith(('_dev','_test')):
        raise ValueError('Set DATABASE_URL explicitly to a loopback _dev or _test database.')
    if requests < concurrency or requests % concurrency:
        raise ValueError('Requests must be a multiple of concurrency and at least concurrency.')
    engine=create_engine(database)
    actors=[]
    run_id=uuid.uuid4().hex[:12]
    try:
        for index in range(concurrency):
            password=secrets.token_urlsafe(24)
            email=f'benchmark-{run_id}-{index}@example.test'
            with Session(engine) as db:
                AccountService(db).register(RegisterRequest(email=email,password=password,display_name=f'Synthetic Benchmark Student {index+1}',role='student'))
            client=httpx.Client(base_url=base_url.rstrip('/')+'/api/v1',timeout=30,trust_env=False)
            csrf=client.get('/auth/csrf');csrf.raise_for_status()
            login=client.post('/auth/login',json={'email':email,'password':password},headers={'X-CSRF-Token':csrf.json()['csrf_token']});login.raise_for_status()
            token=client.get('/auth/csrf').json()['csrf_token']
            saved=client.patch('/profiles/me',json={'skills':['Python','React'],'interests':['web development'],'program':'Computer Science'},headers={'X-CSRF-Token':token});saved.raise_for_status()
            for path in PATHS: client.get(path).raise_for_status()
            actors.append(client)
        with engine.connect() as db:
            counts={name:db.execute(text(f'SELECT count(*) FROM {name}')).scalar_one() for name in ('users','listings','learning_content','applications','interactions')}
        gate=Barrier(concurrency)
        def worker(index):
            client=actors[index];samples=[];gate.wait(timeout=30)
            for n in range(requests//concurrency):
                path=PATHS[(index+n)%len(PATHS)];start=perf_counter()
                try: status=client.get(path).status_code
                except httpx.HTTPError: status=0
                samples.append({'path':path,'status':status,'milliseconds':round((perf_counter()-start)*1000,3)})
            return samples
        begin=perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            samples=[sample for group in pool.map(worker,range(concurrency)) for sample in group]
        duration=perf_counter()-begin
        latency=[s['milliseconds'] for s in samples]
        report={'requirement':'NFR01','measured_at':datetime.now(timezone.utc).isoformat(),'environment':{'python':platform.python_version(),'platform':platform.platform(),'target':'local loopback FastAPI + PostgreSQL'},'dataset_kind':'synthetic local functional benchmark; not pilot participants','concurrent_users':concurrency,'measured_requests':len(samples),'warmup_requests':concurrency*len(PATHS),'path_mix':list(PATHS),'database_row_counts':counts,'elapsed_seconds':round(duration,3),'p95_method':'nearest-rank on all measured request durations','p95_ms':p95(latency),'max_ms':max(latency),'failures':sum(s['status']!=200 for s in samples),'per_path':{path:{'requests':len([s for s in samples if s['path']==path]),'p95_ms':p95([s['milliseconds'] for s in samples if s['path']==path])} for path in PATHS},'target_ms':2000,'limitations':['Warmed local runtime and synthetic accounts; not a production or pilot load result.','AI latency excluded. No external AI provider is called.','Synthetic actors are preserved; no existing data is removed.']}
        report['target_met']=report['failures']==0 and report['p95_ms']<=2000
        return report
    finally:
        for client in actors:client.close()
        engine.dispose()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    parser.add_argument('--concurrency',type=int,default=20,choices=range(1,51))
    parser.add_argument('--requests',type=int,default=200)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();report=run(args.base_url,args.concurrency,args.requests)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['target_met'] else 1

if __name__=='__main__':raise SystemExit(main())

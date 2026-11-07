"""FR12/NFR08 offline evaluation. No input means not measured; no fabricated data."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import json
import math
import os
from pathlib import Path
import statistics


def pending(reason):
    return {'status':'not_measured','reason':reason,'sample_count':None,'metrics':None}

def read_rows(path,required):
    with Path(path).open(newline='',encoding='utf-8-sig') as source:
        reader=csv.DictReader(source)
        if not set(required)<=set(reader.fieldnames or []):raise ValueError('Missing columns: '+', '.join(sorted(set(required)-set(reader.fieldnames or []))))
        rows=list(reader)
    if not rows:raise ValueError('The input contains no observations.')
    if any(None in row or any(row.get(key) is None for key in required) for row in rows):raise ValueError('CSV observations must have all required fields and the declared column count.')
    return rows

def provenance(path):
    with Path(path).open('rb') as source:digest=hashlib.file_digest(source,'sha256').hexdigest()
    return {'input_file':Path(path).name,'sha256':digest,'origin':'user-supplied; authenticity and consent must be established independently'}

def numeric_rating(raw):
    value=float(raw)
    if not math.isfinite(value) or value!=int(value) or not 1<=value<=5:raise ValueError('Ratings must be observed integer values from 1 to 5.')
    return int(value)

def validate_ratings(rows):
    seen=set();texts={}
    for row in rows:
        row['user_id']=row['user_id'].strip();row['item_id']=row['item_id'].strip()
        if not row['user_id'] or not row['item_id']:raise ValueError('Pseudonymous user and item IDs are required.')
        pair=(row['user_id'],row['item_id'])
        if pair in seen:raise ValueError('Provide one latest explicit rating per user/item; duplicate observations are ambiguous.')
        seen.add(pair);row['rating']=numeric_rating(row['rating'])
        if row['item_id'] in texts and texts[row['item_id']]!=row['item_text']:raise ValueError('Item text must be consistent for each item ID.')
        texts[row['item_id']]=row['item_text']
    return rows

def fingerprint(value):return hashlib.sha256(str(value).encode()).hexdigest()

def fit_text(train):
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer=TfidfVectorizer(max_features=5000,ngram_range=(1,2))
    vectorizer.fit([str(row[field]) for row in train for field in ('profile_text','item_text')])
    return vectorizer

def metrics(actual,predicted):
    if len(actual)!=len(predicted) or not actual:raise ValueError('Predictions must use the same nonempty holdout.')
    return {'mae':statistics.mean(abs(a-p) for a,p in zip(actual,predicted)),'rmse':math.sqrt(statistics.mean((a-p)**2 for a,p in zip(actual,predicted)))}

def evaluate_split(rows,train_indices,test_indices):
    train=[rows[int(i)] for i in train_indices];test=[rows[int(i)] for i in test_indices]
    train_users={r['user_id'] for r in train};test_users={r['user_id'] for r in test}
    if train_users&test_users:raise ValueError('User leakage detected.')
    vectorizer=fit_text(train)
    profiles=vectorizer.transform([r['profile_text'] for r in test]);items=vectorizer.transform([r['item_text'] for r in test])
    cosine=profiles.multiply(items).sum(axis=1).A1
    predicted=[1+4*min(1,max(0,float(score))) for score in cosine]
    observed=[r['rating'] for r in test]
    global_mean=statistics.mean(r['rating'] for r in train)
    item_ratings={}
    for row in train:item_ratings.setdefault(row['item_id'],[]).append(row['rating'])
    popularity=[statistics.mean(item_ratings[r['item_id']]) if r['item_id'] in item_ratings else global_mean for r in test]
    holdout=[fingerprint((r['user_id'],r['item_id'])) for r in test]
    return {'train_count':len(train),'test_count':len(test),'train_users':sorted(fingerprint(u) for u in train_users),'test_users':sorted(fingerprint(u) for u in test_users),'holdout_hashes':holdout,'model':metrics(observed,predicted),'item_mean_baseline':metrics(observed,popularity),'global_mean_baseline':metrics(observed,[global_mean]*len(test)),'vocabulary_size':len(vectorizer.vocabulary_)}

def recommender(path,seed=42,folds=0):
    if path is None:return pending('No genuine explicit-rating dataset supplied.')
    rows=validate_ratings(read_rows(path,['user_id','item_id','rating','profile_text','item_text']))
    users=[r['user_id'] for r in rows]
    if len(set(users))<4 or len(rows)<8:return {**pending('At least four users and eight explicit observations are required for this holdout protocol.'),'sample_count':len(rows),'provenance':provenance(path)}
    from sklearn.model_selection import GroupShuffleSplit,GroupKFold
    splitter=GroupShuffleSplit(n_splits=1,test_size=.25,random_state=seed)
    train,test=next(splitter.split(rows,groups=users))
    report={'status':'measured_offline','sample_count':len(rows),'distinct_users':len(set(users)),'provenance':provenance(path),'configuration':{'seed':seed,'split':'user-disjoint GroupShuffleSplit; 25% of users held out','model':'profile-only TF-IDF cosine; predicted rating = 1 + 4*cosine','max_features':5000,'ngram_range':[1,2],'alpha':1,'text_fit':'training rows only'},'comparison':evaluate_split(rows,train,test),'cross_validation':pending('Five-fold evaluation not requested.'),'limitations':['Offline profile-only reference evaluator, not validation of deployed hybrid weighting.','Numerical cosine-to-rating mapping is uncalibrated; compare against the same-holdout baselines.','These values characterize only the supplied dataset, not a pilot unless its provenance establishes that.','No missing interaction is converted into a numerical rating.']}
    if folds:
        if folds!=5:raise ValueError('This documented protocol supports five grouped folds only.')
        if len(set(users))<5 or len(rows)<10:report['cross_validation']=pending('Insufficient users or observations for five grouped folds.')
        else:report['cross_validation']={'status':'measured_offline','method':'five-fold GroupKFold; each fold fits text on its training rows only','folds':[evaluate_split(rows,a,b) for a,b in GroupKFold(n_splits=5).split(rows,groups=users)]}
    return report

def warm_hybrid(path):
    """Observed-only warm-user reference; select alpha on validation, never test."""
    if path is None:return pending('No timestamped explicit-rating dataset supplied.')
    rows=validate_ratings(read_rows(path,['user_id','item_id','rating','profile_text','item_text','occurred_at']))
    groups={}
    for row in rows:
        when=datetime.fromisoformat(row['occurred_at'].replace('Z','+00:00'))
        if when.tzinfo is None:raise ValueError('Warm-user timestamps must include a timezone.')
        row['_time']=when;groups.setdefault(row['user_id'],[]).append(row)
    if len(groups)<5 or any(len(group)<5 for group in groups.values()):return {**pending('Warm protocol requires five users and five distinct rated items per user.'),'sample_count':len(rows),'provenance':provenance(path)}
    train=[];validation=[];test=[]
    for group in groups.values():
        group.sort(key=lambda r:(r['_time'],r['item_id']))
        a=int(.6*len(group));b=max(a+1,int(.8*len(group)))
        if group[a-1]['_time']>=group[a]['_time'] or group[b-1]['_time']>=group[b]['_time']:raise ValueError('Timestamp ties cross a temporal split boundary.')
        train.extend(group[:a]);validation.extend(group[a:b]);test.extend(group[b:])
    if len(train)<20:return {**pending('Insufficient training-only observations for the documented hybrid threshold.'),'sample_count':len(rows),'provenance':provenance(path)}
    vectorizer=fit_text(train)
    observed={}
    for row in train:observed.setdefault(row['user_id'],{})[row['item_id']]=row['rating']
    global_mean=statistics.mean(r['rating'] for r in train);item_ratings={}
    for row in train:item_ratings.setdefault(row['item_id'],[]).append(row['rating'])
    def features(target):
        profiles=vectorizer.transform([r['profile_text'] for r in target]);items=vectorizer.transform([r['item_text'] for r in target]);content=[min(1,max(0,float(c))) for c in profiles.multiply(items).sum(axis=1).A1];collaborative=[]
        for row in target:
            current=observed[row['user_id']];votes=[]
            for other,values in observed.items():
                if other==row['user_id'] or row['item_id'] not in values:continue
                common=set(current)&set(values)
                if len(common)<2:continue
                denominator=math.sqrt(sum(current[k]**2 for k in common)*sum(values[k]**2 for k in common))
                similarity=sum(current[k]*values[k] for k in common)/denominator
                if similarity>0:votes.append((similarity,(values[row['item_id']]-1)/4))
            collaborative.append(sum(w*v for w,v in votes)/sum(w for w,_ in votes) if votes else None)
        return content,collaborative
    validation_content,validation_collab=features(validation);test_content,test_collab=features(test)
    def predictions(content,collaborative,alpha):return [1+4*(c if value is None else alpha*c+(1-alpha)*value) for c,value in zip(content,collaborative)]
    grid=[0,.25,.5,.75,1]
    validation_scores={str(alpha):metrics([r['rating'] for r in validation],predictions(validation_content,validation_collab,alpha)) for alpha in grid}
    alpha=min(grid,key=lambda a:(validation_scores[str(a)]['mae'],-a))
    actual=[r['rating'] for r in test]
    return {'status':'measured_offline','sample_count':len(rows),'distinct_users':len(groups),'provenance':provenance(path),'configuration':{'protocol':'within-user chronological 60/20/20; warm users, not unseen users','fit':'training text and ratings only; validation selects alpha; test is untouched','hybrid':'cosine similarity on at least two jointly observed ratings; weighted neighbor ratings; absent neighbors use content only','alpha_grid':grid,'selected_alpha':alpha,'thresholds':{'users':5,'training_ratings':20}},'train_count':len(train),'validation_count':len(validation),'test_count':len(test),'validation_metrics':validation_scores,'comparison':{'holdout_hashes':[fingerprint((r['user_id'],r['item_id'])) for r in test],'model':metrics(actual,predictions(test_content,test_collab,alpha)),'profile_only':metrics(actual,predictions(test_content,test_collab,1)),'item_mean_baseline':metrics(actual,[statistics.mean(item_ratings[r['item_id']]) if r['item_id'] in item_ratings else global_mean for r in test]),'global_mean_baseline':metrics(actual,[global_mean]*len(test)),'collaborative_covered_test_count':sum(v is not None for v in test_collab)},'limitations':['Offline reference estimator; not a pilot claim without genuine provenance.','Validation observations are not folded back into training histories.','Current runtime candidate eligibility and recommendation ranking require separate integration checks.','Do not reuse warm-user results as unseen-user accuracy.']}


def csat(path):
    if path is None:return pending('No genuine CSAT responses supplied; proposed 4.0/5 target is not a result.')
    rows=read_rows(path,['participant_id','rating']);seen=set();ratings=[]
    for row in rows:
        participant=row['participant_id'].strip()
        if not participant or participant in seen:raise ValueError('CSAT requires one response per pseudonymous participant.')
        seen.add(participant);ratings.append(numeric_rating(row['rating']))
    return {'status':'measured_from_supplied_responses','sample_count':len(ratings),'provenance':provenance(path),'configuration':{'scale':'five-point integer satisfaction','baseline':'not applicable to survey; target is separate'},'metrics':{'mean':statistics.mean(ratings),'distribution':{str(i):ratings.count(i) for i in range(1,6)},'satisfied_share_4_or_5':sum(r>=4 for r in ratings)/len(ratings)},'proposed_target':4.0,'limitations':['No respondents are generated; authenticity, consent and sampling bias require human review.','A CSAT score does not establish factual correctness.']}

def bertscore(path,model=None,layers=12):
    if path is None:return pending('No fixed candidate/reference answer set supplied.')
    rows=read_rows(path,['id','candidate','reference'])
    if len({r['id'] for r in rows})!=len(rows) or any(not r['candidate'].strip() or not r['reference'].strip() for r in rows):raise ValueError('Answer IDs must be unique and paired answers nonempty.')
    human=[r.get('human_factual_correct','').strip().lower() for r in rows]
    if any(v not in {'','true','false'} for v in human):raise ValueError('Human factual checks must be true, false, or blank.')
    report={'sample_count':len(rows),'provenance':provenance(path),'configuration':{'model':str(model) if model else None,'num_layers':layers,'device':'cpu','idf':False,'rescale_with_baseline':False,'network':'offline only','baseline':'no baseline candidate set supplied'},'human_review':{'reviewed':sum(v in {'true','false'} for v in human),'correct':human.count('true'),'incorrect':human.count('false'),'pending':human.count('')},'limitations':['BERTScore measures semantic similarity and does not prove factual truth.','Use a fixed, human-reviewed reference set and review factual correctness separately.']}
    if model is None or not Path(model).is_dir():return {**pending('A local BERTScore model directory is required; no model is downloaded automatically.'),**report}
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    try:from bert_score import score
    except ImportError:return {**pending('Optional bert-score/PyTorch dependencies are not installed.'),**report}
    precision,recall,f1=score([r['candidate'] for r in rows],[r['reference'] for r in rows],model_type=str(model),num_layers=layers,device='cpu',idf=False,rescale_with_baseline=False,verbose=False)
    return {**report,'status':'measured_offline','metrics':{'precision':float(precision.mean()),'recall':float(recall.mean()),'f1':float(f1.mean())}}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol',choices=['cold_start','warm_temporal'],default='cold_start');parser.add_argument('--ratings',type=Path);parser.add_argument('--csat',type=Path);parser.add_argument('--answers',type=Path);parser.add_argument('--bert-model',type=Path);parser.add_argument('--bert-layers',type=int,default=12);parser.add_argument('--folds',type=int,default=0);parser.add_argument('--seed',type=int,default=42);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.protocol=='warm_temporal' and args.folds:parser.error('Use cold_start for grouped unseen-user folds; warm_temporal uses chronological validation instead.')
    if args.bert_layers<1:parser.error('bert-layers must be positive.')
    report={'requirement':'FR12/NFR08','generated_at':datetime.now(timezone.utc).isoformat(),'recommender':None,'csat':None,'assistant':None}
    failed=False
    for name,action in [('recommender',lambda:recommender(args.ratings,args.seed,args.folds) if args.protocol=='cold_start' else warm_hybrid(args.ratings)),('csat',lambda:csat(args.csat)),('assistant',lambda:bertscore(args.answers,args.bert_model,args.bert_layers))]:
        try:report[name]=action()
        except (ValueError,OSError) as error:report[name]={'status':'invalid_input','reason':str(error),'metrics':None};failed=True
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2));return int(failed)
if __name__=='__main__':raise SystemExit(main())

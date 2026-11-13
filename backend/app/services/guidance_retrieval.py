"""FR10/NFR03/11: bounded relevance ranking over published learning material only."""
from collections import Counter
import math
import re
import unicodedata

from sqlalchemy import case, or_, select

from app.models import LearningContent

STOP = frozenset('a an and are as at be been being can could did do does for from give had has have help how i in into is it its me more my of on or our please should so some tell than that the their them then there these they this those to use want was we were what when where which who why will with would you your about example examples first next also'.split())
ALIASES = {
    'cv':'resume', 'resumes':'resume', 'interviews':'interview', 'interviewing':'interview',
    'preparation':'prepare', 'preparing':'prepare', 'prepared':'prepare',
    'applications':'apply', 'application':'apply', 'applying':'apply', 'applied':'apply',
    'verification':'verify', 'verified':'verify', 'verifying':'verify',
    'companies':'company', 'organizations':'company', 'organization':'company', 'employers':'company',
    'publishing':'publish', 'published':'publish', 'listings':'listing', 'opportunities':'opportunity',
    'internships':'internship', 'intern':'internship', 'interns':'internship',
    'skills':'skill', 'portfolios':'portfolio', 'projects':'project', 'requirements':'requirement',
    'students':'student', 'visible':'publish', 'visibility':'publish',
}
VARIANTS = {
    'resume': ('resume', 'résumé', 'cv'), 'apply': ('apply', 'applicat', 'applying'),
    'verify': ('verif',), 'company': ('compan', 'organization', 'employer'),
    'prepare': ('prepar',), 'publish': ('publish',), 'opportunity': ('opportunit',),
}

def tokens(text):
    plain = ''.join(char for char in unicodedata.normalize('NFKD', text.casefold()) if not unicodedata.combining(char))
    return [ALIASES.get(word, word) for word in re.findall(r'[a-z0-9]+', plain) if len(word) > 1 and word not in STOP]

def excerpt(body, weights, question=''):
    passages = []
    for paragraph in re.split(r'\n\s*\n', body):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if len(paragraph) <= 650:
            passages.append(paragraph)
        else:
            passages.extend(paragraph[start:start + 650] for start in range(0, len(paragraph), 500))
    def score(text):
        words = set(tokens(text))
        example = bool(re.search(r'\b(example|sample|illustrat\w*)\b', question, re.I))
        return sum(weight for term, weight in weights.items() if term in words) + (30 if example and re.search(r'\b(example|illustrative)\b', text, re.I) else 0)
    ranked = sorted(enumerate(passages), key=lambda pair: (-score(pair[1]), pair[0]))
    chosen = sorted(ranked[:3])
    return '\n\n'.join(text for _, text in chosen)[:1600] or body[:1600]

def retrieve_sources(db, question, previous_questions=()):
    current = list(dict.fromkeys(tokens(question)))[:12]
    previous = list(dict.fromkeys(tokens(' '.join(previous_questions))))[:12]
    # Resolve short follow-ups without dragging an old subject into a new topic.
    contextual = (not current or bool(set(current) & set(previous)) or
                  (len(current) <= 4 and re.search(r'\b(that|it|this|those|them|another|more|example)\b', question, re.I)))
    if not contextual:
        previous = []
    weights = {term: 1.0 for term in previous}
    weights.update({term: 3.0 for term in current})
    if not weights:
        return []
    matches = []
    sql_score = 0
    for term in weights:
        for variant in VARIANTS.get(term, (term,)):
            title = LearningContent.title.icontains(variant, autoescape=True)
            summary = LearningContent.summary.icontains(variant, autoescape=True)
            body = LearningContent.body.icontains(variant, autoescape=True)
            tag = LearningContent.tags.overlap([variant])
            matches.extend((title, summary, body, tag))
            sql_score += case((title, 12), else_=0) + case((summary, 4), else_=0) + case((body, 1), else_=0) + case((tag, 7), else_=0)
    rows = list(db.scalars(select(LearningContent).where(
        LearningContent.status == 'published', or_(*matches),
    ).order_by(sql_score.desc(), LearningContent.created_at.desc(), LearningContent.id).limit(200)))
    documents = [set(tokens(' '.join([row.title, row.summary, ' '.join(row.tags), row.body]))) for row in rows]
    frequency = Counter(term for words in documents for term in weights if term in words)
    weighted = {term: weight * (1 + math.log((len(rows) + 1) / (frequency[term] + 1))) for term, weight in weights.items()}
    def rank(pair):
        index, row = pair
        title = set(tokens(row.title))
        summary = set(tokens(row.summary))
        tags = set(tokens(' '.join(row.tags)))
        words = documents[index]
        return sum(weight * (12 * (term in title) + 7 * (term in tags) + 4 * (term in summary) + (term in words)) for term, weight in weighted.items())
    ranked = sorted(enumerate(rows), key=rank, reverse=True)
    return [dict(id=str(row.id), title=row.title, excerpt=excerpt(row.body, weighted, question))
            for index, row in ranked[:3] if rank((index, row)) > 0]

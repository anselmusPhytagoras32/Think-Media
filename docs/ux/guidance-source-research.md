# Guidance learning-source research

Researched 2026-11-14 for the current Guidance usefulness work (Phase 3 learning/assistant scope). Requirements: FR03 learning resources, FR10 grounded answers and source references, FR11 publication governance; NFR03 minimal private data, NFR06 separated knowledge artifact, NFR10 English content.

## Deliverable

`backend/knowledge/ojt-preparation.json` contains five original practical guides. These are editorial learning resources, not sample activity, participants, employer partnerships, vacancies, survey responses or measured outcomes. Each record has a stable slug, title, summary, body, tags and structured source links. Body text also includes the source URLs so provenance survives the existing learning-content shape.

| Slug | Intended student output |
| --- | --- |
| ojt-resume-from-real-experience | Evidence sheet and tailored résumé |
| ojt-project-portfolio | Project case page explaining contribution and evidence |
| ojt-interview-star-practice | Truthful story notes and spoken practice |
| ojt-first-week-communication | Supervisor questions and a useful progress update |
| ojt-search-and-evaluate | Search tracker and questions before accepting |

## Primary sources and editorial use

- [MIT CAPD: Resumes — Writing about your skills](https://capd.mit.edu/resources/resumes-writing-about-your-skills/): action, context and result in résumé bullets.
- [Harvard MCS: Creating a Strong Resume](https://careerservices.fas.harvard.edu/resources/create-a-strong-resume/): relevant, readable and factual résumé writing.
- [MIT CAPD: Tools and resources for creating portfolios](https://capd.mit.edu/tools-and-resources-for-creating-portfolios/): demonstrating work and choosing a suitable presentation medium.
- [Virginia Tech: Portfolios](https://career.vt.edu/resources/portfolios/): selecting relevant class or personal work and a usable format.
- [MIT CAPD: Career toolkit — Interviewing](https://capd.mit.edu/resources/career-toolkit-interviewing/): STAR structure, personal contribution and spoken practice.
- [Harvard MCS: Interviewing](https://careerservices.fas.harvard.edu/resources/interviewing/): role research and explaining potential contributions.
- [MIT CAPD: Get the most out of your micro-internship experience](https://capd.mit.edu/blog/2024/12/06/get-the-most-out-of-your-micro-internship-experience/): clarify expectations and communication, seek feedback and raise problems.
- [Temple University Career Center: Internships](https://careercenter.temple.edu/students/grow/internships): learning through questions, listening and notes.
- [Harvard MCS: Summer Experiences](https://careerservices.fas.harvard.edu/channels/find-an-internship/): strengths, values and an organized search.
- [Harvard MCS: Evaluating and Negotiating Job and Internship Offers](https://careerservices.fas.harvard.edu/resources/harvard-college-evaluating-and-negotiating-job-and-internship-offers/): compare learning and practical fit, clarify details and decision timing.

The exercise sequences, review questions, sample messages and class-project example are original editorial synthesis. They are labeled as illustrative and must be replaced with the student's actual circumstances. No university's example achievements or statistics were copied. Source-derived advice is paraphrased across multiple sources; no extended quotations are used.

## Scope and limits

These public university resources support general career preparation. Their local programs, advising access, software subscriptions, recruiting policies, academic credit arrangements and legal discussion are not presented as services or rules available to ThinkMedia students. Some live page opens returned rate limits; their official indexed page extracts supplied the relevant advice. This research used primary university career-center content, not third-party career summaries.

School-specific OJT hours, eligibility, endorsements, agreements, document requirements and placement approval remain questions for the student's actual coordinator. The guides do not assert Philippine employment law, guarantee hiring, endorse an employer or claim that ThinkMedia has a university partnership. Confidentiality reminders are editorial precautions consistent with this repository's privacy requirements.

The JSON file is a source artifact. Creating it does not publish a learning record or change a database. The app now allowlists these reviewed files as versioned, read-only guidance sources so an empty local database can still answer matching OJT questions. Administrator publication remains the workflow for editable learning records and feed visibility. Bundled sources use `guide:<slug>` IDs and a separate authenticated read-only preview endpoint; their metadata is never passed as unrecognized fields to `ContentInput`.

## Verification

Actual read-only Python validation passed for all five records on 2026-11-14 (exit code 0). Checks covered parseability, five unique stable slugs, exact required keys, nonempty bounded title/summary/body, 220–400 body words, nonempty tags, two titled HTTPS sources per guide and source URL presence in each body. Body word counts, including headings and source labels, were 319, 326, 319, 332 and 342 in file order.

To reproduce the basic artifact inspection from the repository root in PowerShell:

```powershell
@'
import json
from pathlib import Path
rows = json.loads(Path('backend/knowledge/ojt-preparation.json').read_text(encoding='utf-8'))
assert len(rows) == len({r['slug'] for r in rows}) == 5
for row in rows:
    assert set(row) == {'slug', 'title', 'summary', 'body', 'tags', 'sources'}
    for key, limit in [('title', 200), ('summary', 500), ('body', 20000)]:
        assert 0 < len(row[key].strip()) <= limit
    assert 220 <= len(row['body'].split()) <= 400
    assert row['tags'] and len(row['sources']) == 2
    assert all(s['title'] and s['url'].startswith('https://') and s['url'] in row['body'] for s in row['sources'])
    print(row['slug'], len(row['body'].split()))
'@ | python -
```

Runtime learning publication, retrieval and assistant behavior require integration verification by the coordinating agent.


# ThinkMedia — implementation brief grounded in the project SRS

**Source**: Software Requirements Specification and cumulative course deliverables, through PD7: Software Architecture and Detailed Design Package (Oct. 15, 2026). This brief condenses implementation requirements, not a replacement for the original document. Earlier duplicate versions of PD2–PD6 appear within the source file; favor the latest cumulative PD7 specification for implementation.

## Product and users

ThinkMedia is an English-language, responsive, web-based career and OJT preparation platform for college students. It combines educational content, opportunities, company applicant management, personalized recommendations, and a grounded AI assistant.

User roles: **student**, **instructor**, **company**, and **administrator** (provisioned separately). Students use profiles/feed/applications/recommendations/AI. Instructors can view approved educational and public opportunity content; they cannot access students' private applications. Verified companies own and manage listings and applicant review. Administrators verify companies, curate learning content, moderate reports, and audit actions.

## Mandatory technology (ADR01–02)

- React + HTML/CSS/JavaScript, responsive mobile-first web interface.
- Python FastAPI REST backend, modular monolith with accounts, learning, opportunities/applications, recommendations, assistant, administration/evaluation modules.
- PostgreSQL relational database; versioned schema migrations, parameterized SQL/ORM, indexes, foreign keys, unique constraints.
- Python pandas/scikit-learn for recommender and evaluation; BERTScore for chatbot evaluation.
- A separately chosen external LLM API for the **application's chatbot**. The developer's Codex ChatGPT login does **not** supply this runtime provider credential. Allow a safe disabled/mock provider for local development; never pretend a mock is a live AI integration.
- API secrets only server-side. No direct frontend connection to LLM provider. React -> HTTPS/FastAPI -> PostgreSQL, private files, approved retrieval content, LLM adapter.

## Functional requirements and acceptance checks

| ID | Build | Essential acceptance |
|---|---|---|
| FR01 | Register/login/logout with server-enforced roles | Unauthenticated and student-to-company/admin requests denied; admin not self-selected |
| FR02 | Student, company profiles; input validation | Profile persists across sessions; private profile cannot be read/edited by another student |
| FR03 | Published learning content, reactions/saves, quizzes | Unpublished items hidden; quiz score follows answer keys |
| FR04 | Search/filter published active listings by type/skills/location; company detail | Closed listings not presented as open; clear empty results |
| FR05 | Student application with permitted attachment, reference, tracking | Valid submission transactional; missing/invalid file and duplicates rejected |
| FR06 | Verified company create/edit/publish/close own listings | Company cannot edit another's listing; closed listing preserves applications |
| FR07 | Company review of own applicants and status updates | Only allowed transitions; actor, old/new status and timestamp logged; student read-only |
| FR08 | Eligible listing/content ranking using profile and collaborative data when available | Closed/unavailable filtered; cold-start profile fallback; suggestions not placement decisions |
| FR09 | Interaction events and optional explicit ratings | Valid user/item IDs, timestamps; never invent explicit ratings |
| FR10 | Read-only grounded AI assistant with source references | Acknowledges uncertainty; handles provider errors; never reveals other application data, secrets or changes decisions |
| FR11 | Company verification, learning publication, reported-content review | Pending company cannot publish; privileged action audited |
| FR12 | Evaluation reporting MAE/RMSE, cross-validation, CSAT, BERTScore | Report actual dataset/sample sizes, train/test split, baseline, config, and limitations; never fabricate metrics |

## Quality requirements

- NFR01: pilot performance target p95 non-AI requests <= 2 seconds with 20 concurrent users. Measure AI calls separately and include test conditions (target, not an established result).
- NFR02: HTTPS, hashed passwords, server-side access control, parameterized queries, protected secrets, unauthorized-access tests.
- NFR03: data use notice, minimum necessary PII, private resumes, no private applications in LLM requests; agree retention rules before pilot.
- NFR04: application and status history committed atomically; duplicate submissions and rollback tested.
- NFR05/NFR09: usable at 360px and desktop, labeled forms, keyboard navigation, visible focus and screen-reader announcements.
- NFR06: separated routes/services/data adapters/provider interfaces; migrations and tests.
- NFR07: daily DB backup and restoration test; proposed recovery point objective 24 hours.
- NFR08: leakage-free splits before fitting, same held-out set for baseline comparison; BERTScore paired with human factual checking.
- NFR10: English, Asia/Manila time, meaningful dates, Unicode/UTF-8 names, translation-ready text.
- NFR11: pagination, public-content caching, bounded upload and AI usage, expired file cleanup per retention policy.

## Domain entities / data stores

Tables given by the SRS: `users`, `student_profiles`, `company_profiles`, `listings`, `applications`, `application_status_history`, `learning_content`, `quiz_questions`, `quiz_attempts`, `interactions`, `moderation_reports`, `audit_events`.

Enforce unique email and unique `(student_id, listing_id)` application. Store attachments privately via protected references, not public URLs. Role-specific profiles and ownership links must be respected. Recommend indexes for browse/filter and ownership queries.

Listings: Draft -> Published -> Closed; only Published accepts applications. Applications: Submitted -> Under Review -> Accepted / Rejected; Submitted -> Rejected is allowed; final decisions stay final in MVP. Record status history and audit events.

## Screen requirements from PD7

- W01: Registration/profile for student, instructor, company; privacy notice; inline validation; admin provisioned separately.
- W02: Learning feed with search/tags, content cards, save/react, quiz card; loading, empty/unavailable states.
- W03: OJT search and listing detail; type/skill/location filters; recommendations; Closed disables Apply.
- W04: Application review/confirm, attachment validation, receipt, tracker/history; preserve valid fields after errors.
- W05: Company dashboard: verification banner, listing changes, applicant list/detail, status confirmation; owner-only.
- W06: Recommendation cards with 'based on your skills/interests' explanation, profile link and optional rating; fallback.
- W07: Assistant conversation, question input, sources/uncertainty, loading, provider-unavailable/retry.
- W08: Admin verification, content editor, reports queue, audit summary.

## Research evaluation / honest reporting

- Hybrid recommender: `score = alpha * contentScore + (1-alpha) * collaborativeScore`; validate alpha; alpha=1 if interaction data insufficient. Define an explicit data collection protocol for cold start and privacy.
- Collect actual optional ratings/feedback, not fabricated labels. MAE/RMSE require suitable ground-truth numerical ratings; compare with popularity or non-personalized baseline on the same holdout.
- k-fold cross-validation (e.g., k=5) only if data sufficient; group by user if evaluating unseen users. Always state sample counts and leakage controls.
- CSAT: real five-point survey sample and distribution; 4.0/5.0 is a **proposed target**, not a result.
- BERTScore: fixed reference-answer set. Human-review factual correctness separately; BERTScore alone does not prove factual truth.

## Boundaries and unresolved decisions

Out of scope: native mobile, payment processing, full LMS, live messaging/video, automated hiring decisions, automated scraping. Social media listings are only manually added/imported by authorized users in this version, subject to platform rules.

Before pilot/deployment confirm actual LLM provider, hosting, privacy notice, retention/deletion policy, role access details, upload size and permitted extensions, company verification procedure, sample/pilot participants, and targets for research evaluations. Never fill these in as if approved. Implement sensible safe defaults with clearly documented TODOs pending user approval.

## Timeline as documented

PD8 prototype target October 29, 2026 (already past as of November 5). Evaluation milestone November 12, 2026. Final presentation November 19, 2026. These are document dates, not claims of completion.

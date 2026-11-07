# Implementation decisions

## 2026-11-05 · Existing backend is extended in place
- Decided by: user.
- Why: preserve DeepSeek-generated functionality and avoid failed external orchestration.
- Rejected: custom team launcher and external headless workers, explicitly excluded by the user.
- Rests on: user implementation request; AGENTS.md modular-monolith constraint.

## 2026-11-05 · Career workspace uses green navigation and a light work surface
- Decided by: user approval of proposed restrained workspace direction.
- Why: readable task hierarchy across student, company, instructor and administrator workflows.
- Rejected: fabricated activity dashboards and invented opportunity content.
- Rests on: PRODUCT.md; cumulative PD7 W01/W05/W08 and NFR05/09.

## 2026-11-05 · Private application bytes default to PostgreSQL transactional storage
- Decided by: Codex default, pending marketplace implementation.
- Why: ensures attachments, application references and history commit or roll back together without orphan private files.
- Rejected: public upload paths and a separate storage service for this modular-monolith prototype.
- Rests on: SRS ADR05, FR05, NFR03–04; docs/API_MARKETPLACE.md.

## 2026-11-06 · External AI stays disabled; local guidance uses approved-resource lookup
- Decided by: user.
- Why: user selected disabled/resource lookup when asked about the runtime provider.
- Rejected: choosing an external provider or making live calls without configured authorization.
- Rests on: user reply and FR10 privacy/failure requirements.

## 2026-11-06 · Optional satisfaction stores one latest numerical response per user
- Decided by: Codex implementation default.
- Why: collect explicit feedback without manufacturing respondents or retaining conversation text; avoid inflating the participant count through repeated updates.
- Rejected: inferring satisfaction from views or reactions, and collecting unnecessary free-text personal information.
- Rests on: FR12/NFR03/08 and the SRS evaluation plan.

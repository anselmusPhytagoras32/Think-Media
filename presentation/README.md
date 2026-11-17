# Local presentation materials

`fictional-resume.pdf` is a valid one-page sample for the application form. It
contains only fictional account details and is labeled as a presentation
document. Select this PDF when demonstrating a student application.

The reproducible generator is `scripts/create-demo-pdf.py`. The role accounts
and generated passwords are kept separately in the ignored file
`.local/presentation/presentation-accounts.private.json`. Do not reuse those
passwords for real accounts. The newly provisioned presentation company starts
pending so its verification can be demonstrated.

Follow `docs/PRESENTATION_READINESS.md` for the complete demonstration sequence.

## Instructor learning demo

Apply migrations, then run `python -m ops.learning_demo` from `backend` with
`APP_ENV=local` and an explicit loopback PostgreSQL `DATABASE_URL` ending in
`_local`. The command uses the dedicated presentation accounts and creates
three published OJT lessons and three separate instructor drafts covering
résumé preparation, STAR interviews, and workplace communication. Each lesson
includes a quiz and reference link. The résumé lesson includes the fictional PDF.

Sign in as the presentation instructor and open **Teaching materials** to
edit and submit a draft. Sign in separately as the presentation administrator
and choose **Review instructor submissions** in **Learning content** to
request changes or approve publication. The
presentation student can find the approved lesson by skill in **Learning**.
Repeat runs preserve existing sample records and the edits made to them.

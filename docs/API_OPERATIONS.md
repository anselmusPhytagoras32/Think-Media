# Local operations contract — FR11 / NFR01/02/03/11

`GET /api/v1/admin/operations` requires a current, server-verified administrator.
Unauthenticated requests return 401; student/instructor/company requests return
403. The response is read-only, private and `Cache-Control: no-store`.

```typescript
type Operations = {
  generated_at: string; // ISO timestamp, Asia/Manila
  started_at: string;
  scope: "current_process";
  requests: { total: number; client_errors: number; server_errors: number };
  latency: { sample_count: number; window_limit: 512; p95_ms: number | null };
  routes: { method: string; route: string; count: number }[];
  storage: {
    database_bytes: number;
    application_count: number;
    attachment_bytes: number;
    expired_session_count: number;
  };
  assistant: { mode: "disabled" | "retrieval" | "external"; calls_used: number; call_budget: number };
};
```

Counters represent this API worker since startup. The latency window contains
at most the latest 512 API requests, including guidance calls. It measures time
to response headers, excluding response-body transfer; it is not the
controlled non-AI benchmark or a research result. Route counts retain at most
128 route/method combinations, aggregating overflow. Only matched route
templates are recorded; unmatched paths use a fixed label. Never retain query
strings, raw paths, IDs, IPs, headers, request/response bodies or exception text.
Unknown HTTP methods use a fixed OTHER label. Counter access must be thread safe.

Storage queries return aggregate counts/bytes only. No user, application or
attachment identifiers, file contents, database URL, API key, endpoint, password
or token is returned. A failed storage query returns the existing generic API
error; no misleading zero or simulated health is substituted. Monitoring never
mutates applications, decisions or provider budgets. The snapshot excludes its
own in-flight request, which is counted when completed. No schema migration is
needed. The app does not persist or aggregate these counters across processes.

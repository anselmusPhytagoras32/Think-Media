// FR11 / NFR01/02/03/11: administrator-only aggregate monitoring, no client estimates.
import { useEffect, useRef, useState } from "react";
import { api, manila } from "./api";

type OperationsSnapshot = {
  generated_at: string;
  started_at: string;
  scope: "current_process";
  requests: { total: number; client_errors: number; server_errors: number };
  latency: {
    sample_count: number;
    window_limit: number;
    p95_ms: number | null;
  };
  routes: { method: string; route: string; count: number }[];
  storage: {
    database_bytes: number;
    application_count: number;
    attachment_bytes: number;
    expired_session_count: number;
  };
  assistant: {
    mode: "disabled" | "retrieval" | "external";
    calls_used: number;
    call_budget: number;
  };
};
const number = (value: number) =>
  new Intl.NumberFormat("en-PH", { maximumFractionDigits: 2 }).format(value);
const bytes = (value: number) => `${number(value)} bytes`;
const modes = {
  disabled: "Disabled",
  retrieval: "Approved resource lookup",
  external: "External AI",
};

export function Operations() {
  const [snapshot, setSnapshot] = useState<OperationsSnapshot | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const requestSequence = useRef(0);
  useEffect(() => {
    const current = ++requestSequence.current;
    setBusy(true);
    setSnapshot(null);
    setError("");
    api<OperationsSnapshot>("/admin/operations")
      .then((data) => {
        if (current === requestSequence.current) setSnapshot(data);
      })
      .catch((failure: Error) => {
        if (current === requestSequence.current) setError(failure.message);
      })
      .finally(() => {
        if (current === requestSequence.current) setBusy(false);
      });
    return () => {
      requestSequence.current++;
    };
  }, [revision]);

  return (
    <section
      className="panel review-panel"
      aria-labelledby="operations-heading"
    >
      <div className="detail-toolbar">
        <h2 id="operations-heading">Local operations</h2>
        <button
          className="secondary"
          disabled={busy}
          onClick={() => setRevision((value) => value + 1)}
        >
          Refresh operations
        </button>
      </div>
      <p>
        Counters cover the current API process since startup and reset when it
        restarts. They are not combined across workers.
      </p>
      <p className="muted">
        Latency covers at most the latest 512 API requests, including guidance.
        Timing includes request body reading and handler work up to response
        headers; it excludes response body transfer. This snapshot is not a
        controlled non-AI benchmark or a research result.
      </p>
      <p role="status" aria-live="polite" aria-atomic="true">
        {busy
          ? "Loading operations snapshot…"
          : snapshot
            ? "Operations snapshot refreshed."
            : ""}
      </p>
      {error && (
        <div className="notice error" role="alert">
          {error} Use Refresh operations to try again.
        </div>
      )}
      {snapshot && (
        <>
          <p>
            Snapshot:{" "}
            <time dateTime={snapshot.generated_at}>
              {manila(snapshot.generated_at)}
            </time>{" "}
            (Asia/Manila). Process started:{" "}
            <time dateTime={snapshot.started_at}>
              {manila(snapshot.started_at)}
            </time>
            .
          </p>
          <h3>Requests and latency</h3>
          <dl className="receipt">
            <dt>Completed requests</dt>
            <dd>{number(snapshot.requests.total)}</dd>
            <dt>Client errors (4xx)</dt>
            <dd>{number(snapshot.requests.client_errors)}</dd>
            <dt>Server errors (5xx)</dt>
            <dd>{number(snapshot.requests.server_errors)}</dd>
            <dt>Recent latency samples</dt>
            <dd>
              {number(snapshot.latency.sample_count)} of{" "}
              {number(snapshot.latency.window_limit)} maximum
            </dd>
            <dt>Recent p95 time to response headers</dt>
            <dd>
              {snapshot.latency.p95_ms === null
                ? "Not measured: no latency samples yet."
                : `${number(snapshot.latency.p95_ms)} ms`}
            </dd>
          </dl>
          <h3>Storage</h3>
          <dl className="receipt">
            <dt>Database storage</dt>
            <dd>{bytes(snapshot.storage.database_bytes)}</dd>
            <dt>Applications stored</dt>
            <dd>{number(snapshot.storage.application_count)}</dd>
            <dt>Private attachment storage</dt>
            <dd>{bytes(snapshot.storage.attachment_bytes)}</dd>
            <dt>Expired sessions awaiting cleanup</dt>
            <dd>{number(snapshot.storage.expired_session_count)}</dd>
          </dl>
          <h3>Guidance usage</h3>
          <dl className="receipt">
            <dt>Configured guidance mode</dt>
            <dd>{modes[snapshot.assistant.mode]}</dd>
            <dt>External AI calls used</dt>
            <dd>{number(snapshot.assistant.calls_used)}</dd>
            <dt>External AI call budget</dt>
            <dd>{number(snapshot.assistant.call_budget)}</dd>
          </dl>
          <details>
            <summary>Request counts by route</summary>
            <p className="muted">
              Route templates only. Personal identifiers, query strings and
              request contents are excluded.
            </p>
            {snapshot.routes.length ? (
              snapshot.routes.map((route) => (
                <article
                  className="company-row"
                  key={`${route.method}:${route.route}`}
                >
                  <p>
                    {route.method} {route.route} — {number(route.count)}{" "}
                    requests
                  </p>
                </article>
              ))
            ) : (
              <p>No completed routes recorded in this process yet.</p>
            )}
          </details>
        </>
      )}
    </section>
  );
}

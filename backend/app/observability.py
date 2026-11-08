"""FR11 / NFR01/02/03/11: bounded aggregate process and storage monitoring."""

from collections import deque
from math import ceil
from threading import Lock
from time import perf_counter

from sqlalchemy import text

from app.time_utils import iso_manila, utcnow


METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"})
WINDOW_LIMIT = 512
ROUTE_LIMIT = 128


class APIMetrics:
    def __init__(self, allowed_routes=(), *, clock=perf_counter):
        self._routes = frozenset(allowed_routes)
        self._clock = clock
        self._started_at = iso_manila(utcnow())
        self._lock = Lock()
        self._total = self._client_errors = self._server_errors = 0
        self._latencies = deque(maxlen=WINDOW_LIMIT)
        self._counts = {}

    def start(self):
        return self._clock()

    def record(self, *, method, route, status, started):
        method = method if method in METHODS else "OTHER"
        route = route if route in self._routes else "UNMATCHED"
        duration = max(0, (self._clock() - started) * 1000)
        with self._lock:
            self._total += 1
            self._client_errors += int(400 <= status < 500)
            self._server_errors += int(status >= 500)
            self._latencies.append(duration)
            key = (method, route)
            # Reserve the last bucket for overflow so total cardinality is fixed.
            if key not in self._counts and len(self._counts) >= ROUTE_LIMIT - 1:
                key = ("OTHER", "OVERFLOW")
            self._counts[key] = self._counts.get(key, 0) + 1

    def snapshot(self):
        with self._lock:
            ordered = sorted(self._latencies)
            return {
                "generated_at": iso_manila(utcnow()),
                "started_at": self._started_at,
                "scope": "current_process",
                "requests": {
                    "total": self._total,
                    "client_errors": self._client_errors,
                    "server_errors": self._server_errors,
                },
                "latency": {
                    "sample_count": len(ordered), "window_limit": WINDOW_LIMIT,
                    "p95_ms": round(ordered[ceil(len(ordered) * .95) - 1], 3) if ordered else None,
                },
                "routes": [
                    {"method": method, "route": route, "count": count}
                    for (method, route), count in sorted(self._counts.items())
                ],
            }


def storage_snapshot(db):
    """Return numbers only; failed SQL must propagate to the generic API error."""
    row = db.execute(text("""
        SELECT pg_database_size(current_database()) AS database_bytes,
               (SELECT count(*) FROM applications) AS application_count,
               (SELECT coalesce(sum(octet_length(attachment)), 0) FROM applications) AS attachment_bytes,
               (SELECT count(*) FROM sessions WHERE expires_at <= now()) AS expired_session_count
    """)).mappings().one()
    return {key: int(value) for key, value in row.items()}

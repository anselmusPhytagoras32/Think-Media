"""In-process, testable authentication throttles.

Limitations: this is per-process state. A multi-worker or multi-host deployment
must move the counters to a shared store (for example Redis) before treating the
throttle as a security boundary. Documented in backend/README.md.
"""

from __future__ import annotations

import math
import threading
import time
from collections import deque
from collections.abc import Callable


class Throttle:
    def __init__(
        self,
        *,
        max_attempts: int,
        window_seconds: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_attempts < 1 or window_seconds < 1:
            raise ValueError("max_attempts and window_seconds must be positive")
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._clock = clock
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque[float]:
        events = self._events.setdefault(key, deque())
        cutoff = now - self.window_seconds
        while events and events[0] <= cutoff:
            events.popleft()
        if not events:
            self._events.pop(key, None)
            return deque()
        return events

    def retry_after(self, key: str) -> int | None:
        """Return seconds to wait when blocked, else ``None``."""

        with self._lock:
            now = self._clock()
            events = self._prune(key, now)
            if len(events) < self.max_attempts:
                return None
            oldest = events[0]
            return max(1, math.ceil(self.window_seconds - (now - oldest)))

    def record_attempt(self, key: str) -> None:
        with self._lock:
            now = self._clock()
            events = self._prune(key, now)
            events.append(now)
            self._events[key] = events

    def reset(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()

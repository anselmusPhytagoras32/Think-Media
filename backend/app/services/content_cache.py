"""FR03/11, NFR03/11: bounded process-local public learning projections.

Authorization and current publication status must be checked from the database
before using a projection. Personal save/react state and quiz answer keys never
enter this cache. HTTP responses remain private and no-store.
"""

from collections import OrderedDict
from copy import deepcopy
import json
from threading import Lock
from time import monotonic


PUBLIC_FIELDS = frozenset({
    "id", "title", "summary", "body", "tags", "status", "created_at",
    "updated_at", "has_quiz",
})


class PublicContentCache:
    def __init__(self, *, max_entries=128, ttl_seconds=30, clock=monotonic):
        if max_entries < 1 or ttl_seconds <= 0:
            raise ValueError("Cache bounds must be positive.")
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._clock = clock
        self._entries = OrderedDict()
        self._lock = Lock()

    def get(self, key):
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            expires, value = entry
            if self._clock() >= expires:
                del self._entries[key]
                return None
            self._entries.move_to_end(key)
            return deepcopy(value)

    def put(self, key, value):
        if set(value) != PUBLIC_FIELDS or value["status"] != "published":
            raise ValueError("Only published public content projections may be cached.")
        # Refuse ORM objects, datetimes or arbitrary mutable Python instances.
        json.dumps(value, allow_nan=False)
        with self._lock:
            now = self._clock()
            for expired in [k for k, (expiry, _) in self._entries.items() if expiry <= now]:
                del self._entries[expired]
            self._entries[key] = (now + self.ttl_seconds, deepcopy(value))
            self._entries.move_to_end(key)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)


public_content_cache = PublicContentCache()

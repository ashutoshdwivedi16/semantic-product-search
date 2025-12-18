import time
from typing import Any, Dict, Tuple, Optional


class TTLCache:
    """A very small in-memory TTL cache for simple response caching.

    Not designed for multi-process usage. Good enough for dev/small deployments.
    """

    def __init__(self, ttl_seconds: float = 60.0, maxsize: int = 256):
        self.ttl = ttl_seconds
        self.maxsize = maxsize
        self._store: Dict[Any, Tuple[float, Any]] = {}

    def get(self, key: Any) -> Optional[Any]:
        now = time.time()
        item = self._store.get(key)
        if not item:
            return None
        expires_at, value = item
        if now > expires_at:
            # expired
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: Any, value: Any) -> None:
        # Simple eviction if over size: drop oldest by expiry soonest
        if len(self._store) >= self.maxsize:
            # remove item with smallest expires_at
            oldest_key = min(self._store.keys(), key=lambda k: self._store[k][0])
            self._store.pop(oldest_key, None)
        self._store[key] = (time.time() + self.ttl, value)

    def size(self) -> int:
        return len(self._store)

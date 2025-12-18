import time
from collections import deque
from typing import Deque, Dict


class RateLimiter:
    """Very simple in-memory sliding-window rate limiter.

    Not safe for multi-process or distributed deployments, but adequate for this exercise.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: Dict[str, Deque[float]] = {}

    def allow(self, key: str) -> bool:
        now = time.time()
        dq = self._hits.setdefault(key, deque())
        # purge old
        cutoff = now - self.window
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= self.max_requests:
            return False
        dq.append(now)
        return True

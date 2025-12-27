import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import HTTPException, status


# key: (identifier, endpoint), value: deque of timestamps (seconds)
_requests: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)


def check_rate_limit(identifier: str, endpoint: str, limit: int, window_seconds: int) -> None:
    """Simple in-memory sliding-window rate limit.

    identifier: usually user id or email/username or IP.
    endpoint: a short name for where this is used (e.g. "login", "create_post").
    limit: maximum number of calls allowed in the time window.
    window_seconds: window length in seconds.
    """
    now = time.time()
    key = (identifier, endpoint)
    dq = _requests[key]

    # drop old timestamps outside the window
    cutoff = now - window_seconds
    while dq and dq[0] < cutoff:
        dq.popleft()

    if len(dq) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )

    dq.append(now)


class _RateLimiterModule:
    """Backwards-compatible facade exposing check_rate_limit as rate_limiter.check_rate_limit"""

    @staticmethod
    def check_rate_limit(identifier: str, endpoint: str, limit: int, window_seconds: int) -> None:
        return check_rate_limit(identifier, endpoint, limit, window_seconds)


rate_limiter = _RateLimiterModule()


__all__ = ["check_rate_limit", "rate_limiter"]

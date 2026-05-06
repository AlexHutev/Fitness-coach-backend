"""Rate limiting via slowapi (in-memory bucket per client IP).

For multi-process deployments swap the storage backend to Redis by setting
`storage_uri="redis://..."` on the Limiter. We keep it in-memory here because
the app currently runs as a single uvicorn process.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

limiter = Limiter(key_func=get_remote_address)

# Reusable rate-limit string for sensitive (auth) endpoints.
AUTH_RATE_LIMIT = f"{settings.auth_rate_limit_per_minute}/minute"

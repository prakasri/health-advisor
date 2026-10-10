"""NFR-6: 10 assessments per minute per client IP (slowapi, in-memory; single EC2 host)."""

from slowapi import Limiter
from slowapi.util import get_remote_address


def client_ip(request) -> str:
    # Behind Vercel rewrite + Caddy the real client is the first X-Forwarded-For entry.
    forwarded = request.headers.get("x-forwarded-for")
    return forwarded.split(",")[0].strip() if forwarded else get_remote_address(request)


limiter = Limiter(key_func=client_ip)

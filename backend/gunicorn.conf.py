import os


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")
# P0 only: gthread buys bounded capacity for the existing WSGI SSE endpoint.
# Set WORKERS/THREADS from the documented DB connection budget before deploy;
# this is deliberately conservative rather than a production capacity claim.
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gthread")
workers = _int_env("GUNICORN_WORKERS", 3)
threads = _int_env("GUNICORN_THREADS", 8)
timeout = _int_env("GUNICORN_TIMEOUT", 60)
graceful_timeout = _int_env("GUNICORN_GRACEFUL_TIMEOUT", 30)
keepalive = _int_env("GUNICORN_KEEPALIVE", 5)
max_requests = _int_env("GUNICORN_MAX_REQUESTS", 2000)
max_requests_jitter = _int_env("GUNICORN_MAX_REQUESTS_JITTER", 200)
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

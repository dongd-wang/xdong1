import multiprocessing
import os
from typing import Any, Dict

workers_per_core_str = os.getenv("WORKERS_PER_CORE", "2")
web_concurrency_str = os.getenv("WEB_CONCURRENCY", None)

host = os.getenv("HOST", "0.0.0.0")
port = os.getenv("PORT", "8000")
bind_env = os.getenv("BIND", None)
use_loglevel = os.getenv("LOG_LEVEL", "info")
if bind_env:
    use_bind = bind_env
else:
    use_bind = f"{host}:{port}"

cores = multiprocessing.cpu_count()
workers_per_core = float(workers_per_core_str)
default_web_concurrency = workers_per_core * cores + 1
if web_concurrency_str:
    web_concurrency = int(web_concurrency_str)
    assert web_concurrency > 0
else:
    web_concurrency = max(int(default_web_concurrency), 2)
graceful_timeout_str = os.getenv("GRACEFUL_TIMEOUT", "120")
timeout_str = os.getenv("TIMEOUT", "120")
keepalive_str = os.getenv("KEEP_ALIVE", "20")
max_requests_str = os.getenv("MAX_REQUEST", "5000")
max_requests_jitter_str = os.getenv("MAX_REQUESTS_JITTER", "10")

# Gunicorn config variables
loglevel = use_loglevel
workers = web_concurrency
bind = use_bind
graceful_timeout = int(graceful_timeout_str)
timeout = int(timeout_str)
keepalive = int(keepalive_str)
max_requests = int(max_requests_str)
max_requests_jitter = int(max_requests_jitter_str)

preload_app = True
pidfile = "xsrc.pid"
worker_class = "uvicorn.workers.UvicornWorker"
logger_class = "src.core.logging.StubbedGunicornLogger"
proc_name = "xsrc"
user=os.getenv("GUNICORN_USER", None)
group=os.getenv("GUNICORN_GROUP", None)

log_data: Dict[str, Any] = {
    "loglevel": loglevel,
    "workers": workers,
    "bind": bind,
    "graceful_timeout": graceful_timeout,
    "timeout": timeout,
    "keepalive": keepalive,
    "max_requests": max_requests,
    "workers_per_core": workers_per_core,
    "max_requests_jitter": max_requests_jitter,
    "host": host,
    "port": port,
    "pidfile": pidfile,
    "preload_app": preload_app,
    "worker_class": worker_class,
    "logger_class": logger_class,
    "proc_name": proc_name,
    "user": user,
    "group": group
}
import multiprocessing
import os

# Gunicorn configuration file
workers = int(os.getenv('WORKERS', '2'))
worker_class = 'uvicorn.workers.UvicornWorker'
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.getenv('LOG_LEVEL', 'info')

# Worker processes
def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("Worker received INT or QUIT signal")

def worker_abort(worker):
    worker.log.info("Worker received SIGABRT signal")

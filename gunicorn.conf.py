# Gunicorn configuration for Raspberry Pi 5
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 2  # Conservative for Pi 5
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/home/pi/TFL/logs/access.log"
errorlog = "/home/pi/TFL/logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "taxi-tracker"

# Daemon mode
daemon = False
pidfile = "/home/pi/TFL/gunicorn.pid"
user = "pi"
group = "pi"
tmp_upload_dir = None

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

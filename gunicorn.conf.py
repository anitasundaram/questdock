# gunicorn.conf.py
# Worker configuration
workers = 4  # (2 * num_cores) + 1
threads = 4
worker_class = 'gthread'

# Binding
bind = '0.0.0.0:8000'

# Advanced settings
keepalive = 120
timeout = 120
errorlog = '-'  # stderr
loglevel = 'info'
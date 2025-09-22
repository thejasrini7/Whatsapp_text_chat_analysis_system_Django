import multiprocessing
import os

# Memory-optimized worker configuration
workers = 1  # Use single worker to reduce memory usage
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 2

# Memory management
max_requests = 1000  # Restart worker after 1000 requests
max_requests_jitter = 50  # Add randomness to prevent all workers restarting at once
preload_app = True  # Load app before forking workers

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
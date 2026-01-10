"""
Prometheus metrics for Auth Service
"""

from prometheus_client import Counter, Histogram, Info

# Service info
auth_service = Info("auth_service", "Auth service version")
auth_service.info({"version": "1.0.0"})

# HTTP Metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
)

# Business Metrics
user_registrations_total = Counter(
    "user_registrations_total", "Total user registrations"
)

user_logins_total = Counter(
    "user_logins_total", "Total user logins", ["status"]  # success, failed
)

tokens_generated_total = Counter(
    "tokens_generated_total", "Total auth tokens generated"
)


# Helper functions
def record_http_request(method: str, endpoint: str, status_code: int, duration: float):
    """Record HTTP request metrics"""
    http_requests_total.labels(
        method=method, endpoint=endpoint, status=status_code
    ).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
        duration
    )

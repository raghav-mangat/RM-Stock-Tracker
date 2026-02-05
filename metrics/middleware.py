import time
from flask import request, g
from metrics import metrics
from metrics.registry import MetricName


SLOW_REQUEST_THRESHOLD_MS = 1000

def register_metrics_middleware(app):
    @app.before_request
    def start_timer():
        g.request_start_time = time.perf_counter()

    @app.after_request
    def record_metrics(response):
        latency_ms = (time.perf_counter() - g.request_start_time) * 1000

        if response.status_code >= 500:
            metrics.increment(MetricName.RESPONSES_5XX)

        if latency_ms >= SLOW_REQUEST_THRESHOLD_MS:
            metrics.increment(MetricName.SLOW_REQUESTS)

        if request.endpoint == "static":
            metrics.increment(MetricName.STATIC_REQUEST_COUNT)
            metrics.observe_static_latency(latency_ms)
        else:
            metrics.increment(MetricName.REQUEST_COUNT)
            metrics.observe_latency(latency_ms)

        return response
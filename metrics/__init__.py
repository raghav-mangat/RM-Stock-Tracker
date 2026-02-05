from metrics.proxy import MetricsProxy
from metrics.hybrid import HybridMetricsBackend
from metrics.noop import NoOpMetricsBackend
from metrics.lifecycle import register_metrics_shutdown


"""
- Metrics use a hybrid design: in-memory buffering with periodic Redis flushes
- Request paths never block on Redis (performance-safe)
- Metrics are aggregated per day using date-scoped Redis keys
- Latency is tracked using sum + count (efficient average calculation)
- Thread-safe design using locks to protect shared in-memory state
- Redis writes use atomic pipelines with TTL for automatic cleanup
- All the metrics in the metrics/registry.py are calculated properly,
    in their respective places in the project
- Redis flush success and failure are tracked as first-class metrics
- Flush failures do not break requests and buffers are retried later
- Each request has the actual app request part and static part,
    that's why we have request count and static request count
- Improvements / Future Work
    - Background flush thread instead of opportunistic flushing
    - Export metrics to Prometheus / Grafana
    - Alerting on sustained Redis flush failures
    - Multi-process aggregation using Redis-only backend
    - Histogram-based latency buckets if higher resolution is needed
    - Per route request count and average latency calculation
"""


metrics = MetricsProxy()

def init_metrics(app) -> None:
    if app.config["ENV"] == "prod":
        metrics.set_backend(
            HybridMetricsBackend(
                redis_conn=app.config["REDIS"],
                flush_interval_sec=3600, # 1 hour
            )
        )
    else:
        metrics.set_backend(NoOpMetricsBackend())

    register_metrics_shutdown(app, metrics)
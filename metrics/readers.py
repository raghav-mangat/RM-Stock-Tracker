from datetime import date
from metrics.keys import metrics_dated_key
from metrics.registry import MetricName


def read_daily_metrics(redis, utc_date: date) -> dict:
    def get_int(name):
        return int(redis.get(metrics_dated_key(name, utc_date)) or 0)

    def get_float(name):
        return float(redis.get(metrics_dated_key(name, utc_date)) or 0.0)

    latency_sum = get_float(MetricName.LATENCY_SUM_MS)
    latency_count = get_int(MetricName.LATENCY_COUNT)

    static_latency_sum = get_float(MetricName.STATIC_LATENCY_SUM_MS)
    static_latency_count = get_int(MetricName.STATIC_LATENCY_COUNT)

    avg_latency = latency_sum / latency_count if latency_count > 0 else 0.0
    avg_static_latency = (
        static_latency_sum / static_latency_count
        if static_latency_count > 0
        else 0.0
    )

    return {
        MetricName.EMAILS_ENQUEUED: get_int(MetricName.EMAILS_ENQUEUED),
        MetricName.API_CALLS: get_int(MetricName.API_CALLS),
        MetricName.GOOGLE_OAUTH_CALLBACKS: get_int(MetricName.GOOGLE_OAUTH_CALLBACKS),
        MetricName.REQUEST_COUNT: get_int(MetricName.REQUEST_COUNT),
        MetricName.STATIC_REQUEST_COUNT: get_int(MetricName.STATIC_REQUEST_COUNT),
        MetricName.RESPONSES_5XX: get_int(MetricName.RESPONSES_5XX),
        MetricName.SLOW_REQUESTS: get_int(MetricName.SLOW_REQUESTS),
        MetricName.UNCAUGHT_EXCEPTIONS: get_int(MetricName.UNCAUGHT_EXCEPTIONS),
        "avg_latency_ms": round(avg_latency, 2),
        "avg_static_latency_ms": round(avg_static_latency, 2),
        MetricName.REDIS_FLUSH_SUCCESS: get_int(MetricName.REDIS_FLUSH_SUCCESS),
        MetricName.REDIS_FLUSH_FAILURE: get_int(MetricName.REDIS_FLUSH_FAILURE),
    }

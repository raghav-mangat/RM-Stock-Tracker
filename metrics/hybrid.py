import time
import threading
from collections import defaultdict
from redis.exceptions import RedisError
from metrics.base import MetricsBackend
from metrics.keys import metrics_dated_key
from metrics.registry import MetricName
from utils.constants import REDIS_METRICS_TTL
from utils.datetime_utils import get_current_utc


class HybridMetricsBackend(MetricsBackend):
    """
    In-memory buffered metrics backend that periodically flushes
    aggregated metrics to Redis using daily keys.
    """

    def __init__(self, redis_conn, flush_interval_sec: int = 3600):
        self.redis = redis_conn
        self.flush_interval_sec = flush_interval_sec

        # In-memory counters (per process)
        self._counters = defaultdict(int)
        self._latency_counters = self.initialize_latency_counters()

        self._lock = threading.Lock()
        self._last_flush = time.time()

    @staticmethod
    def initialize_latency_counters():
        return {
            # App request latency
            MetricName.LATENCY_COUNT: 0,
            MetricName.LATENCY_SUM_MS: 0.0,
            # Static request latency
            MetricName.STATIC_LATENCY_COUNT: 0,
            MetricName.STATIC_LATENCY_SUM_MS: 0.0,
        }

    def increment(self, name: str, value: int = 1) -> None:
        with self._lock:
            self._counters[name] += value
        self._maybe_flush()

    def observe_latency(self, latency_ms: float) -> None:
        with self._lock:
            self._latency_counters[MetricName.LATENCY_COUNT] += 1
            self._latency_counters[MetricName.LATENCY_SUM_MS] += latency_ms
        self._maybe_flush()

    def observe_static_latency(self, latency_ms: float) -> None:
        with self._lock:
            self._latency_counters[MetricName.STATIC_LATENCY_COUNT] += 1
            self._latency_counters[MetricName.STATIC_LATENCY_SUM_MS] += latency_ms
        self._maybe_flush()

    def _maybe_flush(self) -> None:
        if time.time() - self._last_flush >= self.flush_interval_sec:
            self.flush()

    def flush(self) -> None:
        """
        Flush buffered metrics to Redis using daily keys.
        Tracks Redis flush success/failure safely.
        """
        with self._lock:
            if (
                not self._counters
                and self._latency_counters[MetricName.LATENCY_COUNT] == 0
                and self._latency_counters[MetricName.STATIC_LATENCY_COUNT] == 0
            ):
                return

            now = get_current_utc()
            pipe = self.redis.pipeline()

            try:
                # --- Flush counters ---
                for metric, value in self._counters.items():
                    key = metrics_dated_key(metric, now)
                    pipe.incrby(key, value)
                    pipe.expire(key, REDIS_METRICS_TTL)

                # --- Flush app latency ---
                if self._latency_counters[MetricName.LATENCY_COUNT] > 0:
                    pipe.incrby(
                        metrics_dated_key(MetricName.LATENCY_COUNT, now),
                        self._latency_counters[MetricName.LATENCY_COUNT],
                    )
                    pipe.incrbyfloat(
                        metrics_dated_key(MetricName.LATENCY_SUM_MS, now),
                        self._latency_counters[MetricName.LATENCY_SUM_MS],
                    )
                    pipe.expire(metrics_dated_key(MetricName.LATENCY_COUNT, now), REDIS_METRICS_TTL)
                    pipe.expire(metrics_dated_key(MetricName.LATENCY_SUM_MS, now), REDIS_METRICS_TTL)

                # --- Flush static latency ---
                if self._latency_counters[MetricName.STATIC_LATENCY_COUNT] > 0:
                    pipe.incrby(
                        metrics_dated_key(MetricName.STATIC_LATENCY_COUNT, now),
                        self._latency_counters[MetricName.STATIC_LATENCY_COUNT],
                    )
                    pipe.incrbyfloat(
                        metrics_dated_key(MetricName.STATIC_LATENCY_SUM_MS, now),
                        self._latency_counters[MetricName.STATIC_LATENCY_SUM_MS],
                    )
                    pipe.expire(
                        metrics_dated_key(MetricName.STATIC_LATENCY_COUNT, now),
                        REDIS_METRICS_TTL,
                    )
                    pipe.expire(
                        metrics_dated_key(MetricName.STATIC_LATENCY_SUM_MS, now),
                        REDIS_METRICS_TTL,
                    )

                # Execute atomic flush
                pipe.execute()

                # Record successful Redis flush
                success_key = metrics_dated_key(MetricName.REDIS_FLUSH_SUCCESS, now)
                self.redis.incr(success_key)
                self.redis.expire(success_key, REDIS_METRICS_TTL)

                # Reset buffers only after success
                self._counters.clear()
                self._latency_counters.clear()
                self._latency_counters = self.initialize_latency_counters()
                self._last_flush = time.time()

            except RedisError:
                try:
                    # Record failed Redis flush
                    failure_key = metrics_dated_key(MetricName.REDIS_FLUSH_FAILURE, now)
                    pipe = self.redis.pipeline()
                    pipe.incr(failure_key)
                    pipe.expire(failure_key, REDIS_METRICS_TTL)
                    pipe.execute()
                except RedisError:
                    # If even recording failure fails, log failure (optional)
                    pass

                # Do NOT clear buffers, retry on next flush
                # Log failure (optional)

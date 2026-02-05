from metrics.base import MetricsBackend
from metrics.noop import NoOpMetricsBackend


class MetricsProxy(MetricsBackend):
    """
    Proxy that forwards metrics calls to the active backend.
    """

    def __init__(self):
        self._backend: MetricsBackend = NoOpMetricsBackend()

    def set_backend(self, backend: MetricsBackend):
        self._backend = backend

    def increment(self, name: str, value: int = 1):
        return self._backend.increment(name, value)

    def observe_latency(self, latency_ms: float):
        return self._backend.observe_latency(latency_ms)

    def observe_static_latency(self, latency_ms: float):
        return self._backend.observe_static_latency(latency_ms)

    def flush(self):
        return self._backend.flush()
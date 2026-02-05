from metrics.base import MetricsBackend


class NoOpMetricsBackend(MetricsBackend):
    """
    No-op backend used before metrics are fully initialized
    or when metrics are disabled.
    """

    def increment(self, name: str, value: int = 1) -> None:
        pass

    def observe_latency(self, latency_ms: float) -> None:
        pass

    def observe_static_latency(self, latency_ms: float) -> None:
        pass

    def flush(self) -> None:
        pass
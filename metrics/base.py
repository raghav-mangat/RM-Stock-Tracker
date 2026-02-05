from abc import ABC, abstractmethod


class MetricsBackend(ABC):
    """
    Base interface for all metrics backends.
    """

    @abstractmethod
    def increment(self, name: str, value: int = 1) -> None:
        pass

    @abstractmethod
    def observe_latency(self, latency_ms: float) -> None:
        """
        Observe latency for application (non-static) requests.
        """
        pass

    @abstractmethod
    def observe_static_latency(self, latency_ms: float) -> None:
        """
        Observe latency for static asset requests.
        """
        pass

    @abstractmethod
    def flush(self) -> None:
        pass
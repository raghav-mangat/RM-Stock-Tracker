from abc import ABC, abstractmethod

class EmailProvider(ABC):
    @abstractmethod
    def send(
        self,
        subject: str,
        recipients: list[str],
        text_body: str,
        html_body: str,
        inline_images: dict[str, str] | None = None,
    ) -> None:
        pass
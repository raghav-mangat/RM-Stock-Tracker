from rq import Retry
from metrics import metrics
from metrics.registry import MetricName

class EmailService:

    @staticmethod
    def enqueue_auth_email(
        subject: str,
        recipients: list[str],
        text_body: str,
        html_body: str,
        inline_images: dict[str, str] | None = None
    ):
        """
        Enqueue auth email sending in Redis (non-blocking).
        """
        from tasks.email_tasks import send_email_task
        from app import email_high_queue

        email_high_queue.enqueue(
            send_email_task,
            subject,
            recipients,
            text_body,
            html_body,
            inline_images,
            job_timeout=120,
            retry=Retry(max=3, interval=[10, 30, 60]),
        )

        metrics.increment(MetricName.EMAILS_ENQUEUED)

    @staticmethod
    def enqueue_watchlist_email(
        subject: str,
        recipients: list[str],
        text_body: str,
        html_body: str,
        inline_images: dict[str, str] | None = None
    ):
        """
        Enqueue watchlist email sending in Redis (non-blocking).
        """
        from tasks.email_tasks import send_email_task
        from app import email_low_queue

        email_low_queue.enqueue(
            send_email_task,
            subject,
            recipients,
            text_body,
            html_body,
            inline_images,
            job_timeout=300,
            retry=Retry(max=2, interval=[60, 300]),
        )

        metrics.increment(MetricName.EMAILS_ENQUEUED)

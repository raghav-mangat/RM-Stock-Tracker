from app import get_app
from metrics import metrics
from metrics.registry import MetricName
from rq import get_current_job


def send_email_task(
    subject: str,
    recipients: list[str],
    text_body: str,
    html_body: str,
    inline_images: dict | None = None,
):
    """
    RQ job: Sends an email inside a Flask app context.
    """

    app = get_app()
    job = get_current_job()

    with app.app_context():
        from utils.emails.providers.factory import get_email_provider

        logger = app.logger
        provider = get_email_provider()

        logger.info(
            "Email send task started",
            extra={
                "log_type": "emails",
                "action": "email_send_start",
                "recipients_count": len(recipients),
                "job_id": job.id if job else None,
            },
        )

        try:
            provider.send(
                subject,
                recipients,
                text_body,
                html_body,
                inline_images,
            )

            # ---- SUCCESS ----
            metrics.increment(MetricName.EMAILS_SENT_SUCCESS)

            logger.info(
                "Email sent successfully",
                extra={
                    "log_type": "emails",
                    "action": "email_send_success",
                    "recipients_count": len(recipients),
                    "job_id": job.id if job else None,
                },
            )

        except Exception as exc:
            # ---- FAILURE ----
            metrics.increment(MetricName.EMAILS_SENT_FAILURE)

            # Track retries (RQ increments this internally)
            if job and job.retries_left and job.retries_left > 0:
                metrics.increment(MetricName.EMAIL_SEND_RETRIES)

                logger.warning(
                    "Email send failed, retrying",
                    extra={
                        "log_type": "emails",
                        "action": "email_send_retry",
                        "retries_left": job.retries_left,
                        "job_id": job.id,
                        "reason": str(exc),
                    },
                )
            else:
                # Permanent failure
                metrics.increment(MetricName.EMAIL_SEND_PERMANENT_FAILURE)

                logger.exception(
                    "Email send failed permanently",
                    extra={
                        "log_type": "emails",
                        "action": "email_send_failure",
                        "job_id": job.id if job else None,
                    }
                )

            # Let RQ handle retries / failure state
            raise